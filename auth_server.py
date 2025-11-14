#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整的认证和RAG查询服务器
集成登录、多轮对话、RAG检索、知识图谱查询功能
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
import json
import hashlib
import secrets
from datetime import datetime, timedelta

from src.agent.config import DEFAULT_DB_PATH, TOP_K
from src.agent.storage import Storage
from src.agent.vector_store import VectorStore
from src.agent.knowledge_base import load_knowledge
from src.agent.graph_client import GraphClient
from src.agent.neo4j_client import Neo4jClient
from src.agent.retriever import retrieve_all
from src.agent.llm_client import LLMClient

app = FastAPI(title="金融AI风险评估系统")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 用户数据库（生产环境应使用真实数据库）
USERS_DB = {
    "admin": {
        "username": "admin",
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "role": "admin"
    },
    "analyst": {
        "username": "analyst",
        "password_hash": hashlib.sha256("analyst123".encode()).hexdigest(),
        "role": "analyst"
    }
}

# Token存储（生产环境应使用Redis）
ACTIVE_TOKENS = {}

# 会话存储（存储每个用户的对话历史）
USER_SESSIONS = {}


# ==================== 数据模型 ====================

class LoginRequest(BaseModel):
    username: str
    password: str


class ChatRequest(BaseModel):
    query: str
    history: Optional[List[Dict[str, str]]] = []


class User(BaseModel):
    username: str
    role: str


# ==================== 认证相关 ====================

def create_token(username: str) -> str:
    """创建访问令牌"""
    token = secrets.token_urlsafe(32)
    ACTIVE_TOKENS[token] = {
        "username": username,
        "created_at": datetime.now(),
        "expires_at": datetime.now() + timedelta(hours=24)
    }
    return token


def verify_token(authorization: Optional[str] = Header(None)) -> str:
    """验证访问令牌"""
    if not authorization:
        raise HTTPException(status_code=401, detail="未提供认证令牌")
    
    try:
        token = authorization.replace("Bearer ", "")
    except:
        raise HTTPException(status_code=401, detail="令牌格式错误")
    
    token_data = ACTIVE_TOKENS.get(token)
    if not token_data:
        raise HTTPException(status_code=401, detail="无效的令牌")
    
    if datetime.now() > token_data["expires_at"]:
        del ACTIVE_TOKENS[token]
        raise HTTPException(status_code=401, detail="令牌已过期")
    
    return token_data["username"]


# ==================== API端点 ====================

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """用户登录"""
    user = USERS_DB.get(request.username)
    
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    password_hash = hashlib.sha256(request.password.encode()).hexdigest()
    if password_hash != user["password_hash"]:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    token = create_token(request.username)
    
    return {
        "success": True,
        "token": token,
        "user": {
            "username": user["username"],
            "role": user["role"]
        }
    }


@app.post("/api/auth/logout")
async def logout(username: str = Depends(verify_token)):
    """用户登出"""
    # 清除该用户的所有token
    tokens_to_remove = [
        token for token, data in ACTIVE_TOKENS.items() 
        if data["username"] == username
    ]
    for token in tokens_to_remove:
        del ACTIVE_TOKENS[token]
    
    return {"success": True, "message": "登出成功"}


@app.get("/api/auth/me")
async def get_current_user(username: str = Depends(verify_token)):
    """获取当前用户信息"""
    user = USERS_DB.get(username)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return {
        "username": user["username"],
        "role": user["role"]
    }


@app.post("/api/chat/query")
async def chat_query(request: ChatRequest, username: str = Depends(verify_token)):
    """
    智能查询接口 - 支持多轮对话
    集成RAG检索、知识图谱、向量数据库
    """
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="查询内容不能为空")
    
    # 初始化组件
    db_path = os.environ.get("DB_PATH", DEFAULT_DB_PATH)
    storage = Storage(db_path)
    storage.init()
    
    # 加载知识库
    knowledge = load_knowledge()
    
    # 初始化向量存储
    vs = VectorStore()
    try:
        vs.add_knowledge_dirs()
    except Exception as e:
        print(f"向量存储初始化警告: {e}")
    
    # 初始化图数据库客户端
    gc = GraphClient("graph_data")
    n4 = Neo4jClient()
    
    # 执行多源检索
    try:
        result = retrieve_all(storage, knowledge, vs, gc, n4, query, top_k=TOP_K)
        hits = result.get("hits", [])
        is_valid = result.get("valid", False)
    except Exception as e:
        print(f"检索错误: {e}")
        hits = []
        is_valid = False
    
    # 构建上下文
    context_parts = []
    
    # 添加检索证据
    if hits:
        evidence_texts = [h.get("text", "") for h in hits if h.get("text")]
        if evidence_texts:
            context_parts.append("检索证据:\n" + "\n".join(evidence_texts[:TOP_K]))
    
    # 添加对话历史
    if request.history:
        history_text = "\n".join([
            f"{msg['role']}: {msg['content']}" 
            for msg in request.history[-6:]  # 最近3轮对话
        ])
        context_parts.append(f"对话历史:\n{history_text}")
    
    # 构建Prompt
    system_prompt = """你是专业的金融风控分析师。请基于提供的检索证据回答用户问题。

要求：
1. 如果检索证据不足，明确告知"知识库中暂无相关信息"，不要编造内容
2. 如果有足够证据，输出结构化回答，包含：
   【主要风险】：总结关键风险点
   【指标说明】：解释相关指标和证据
   【应对建议】：提出具体可执行的措施
3. 保持专业、准确、简洁"""
    
    user_prompt = "\n\n".join(context_parts) + f"\n\n用户查询：{query}"
    
    # 调用LLM生成回答
    answer = ""
    if is_valid:
        try:
            llm = LLMClient()
            answer = llm.chat([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ], temperature=0.2)
        except Exception as e:
            print(f"LLM调用错误: {e}")
            answer = "抱歉，AI服务暂时不可用。以下是检索到的相关信息：\n\n" + "\n".join([
                f"• {h.get('text', '')[:200]}" for h in hits[:3]
            ])
    else:
        answer = "知识库中暂无相关信息。请尝试：\n• 使用更具体的企业名称或关键词\n• 查询已有数据的企业（如：三木集团、海螺新材）\n• 检查数据库是否已初始化"
    
    # 保存到用户会话
    if username not in USER_SESSIONS:
        USER_SESSIONS[username] = []
    
    USER_SESSIONS[username].append({
        "query": query,
        "answer": answer,
        "timestamp": datetime.now().isoformat(),
        "hits_count": len(hits)
    })
    
    # 保存查询记录到数据库
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        html_dir = os.path.join(os.getcwd(), "html_reports")
        os.makedirs(html_dir, exist_ok=True)
        
        filename = f"query_{username}_{timestamp.replace(' ', '_').replace(':', '-')}.html"
        filepath = os.path.join(html_dir, filename)
        
        html_content = f"""
        <html>
        <head>
            <meta charset='utf-8'>
            <title>查询结果 - {query}</title>
            <style>
                body {{ font-family: "Microsoft YaHei", sans-serif; margin: 40px; }}
                h2 {{ color: #667eea; }}
                .evidence {{ background: #f7f7f7; padding: 15px; border-radius: 8px; margin: 10px 0; }}
                .answer {{ background: #e8f4f8; padding: 15px; border-radius: 8px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <h2>查询记录</h2>
            <p><strong>用户：</strong>{username}</p>
            <p><strong>时间：</strong>{timestamp}</p>
            <p><strong>查询：</strong>{query}</p>
            
            <h3>检索证据（{len(hits)}条）</h3>
            <div class="evidence">
                {'<br>'.join([f"{i+1}. {h.get('text', '')[:300]}" for i, h in enumerate(hits)])}
            </div>
            
            <h3>AI回答</h3>
            <div class="answer">
                {answer.replace(chr(10), '<br>')}
            </div>
        </body>
        </html>
        """
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)
    except Exception as e:
        print(f"保存查询记录失败: {e}")
    
    return {
        "success": True,
        "query": query,
        "answer": answer,
        "hits": hits,
        "valid": is_valid,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/chat/history")
async def get_chat_history(username: str = Depends(verify_token)):
    """获取用户的对话历史"""
    history = USER_SESSIONS.get(username, [])
    return {
        "success": True,
        "history": history[-20:]  # 返回最近20条
    }


@app.get("/api/config/info")
async def get_config_info(username: str = Depends(verify_token)):
    """获取系统配置信息"""
    from src.agent.config import (
        OPENAI_API_KEY, OPENAI_CHAT_MODEL, OPENAI_BASE_URL,
        EMBED_PROVIDER, BAAI_MODEL, TOP_K, RAG_MIN_SCORE
    )
    
    # 检查Neo4j连接
    n4 = Neo4jClient()
    neo4j_available = n4.available()
    
    return {
        "success": True,
        "config": {
            "llm": {
                "provider": "OpenAI Compatible",
                "model": OPENAI_CHAT_MODEL,
                "base_url": OPENAI_BASE_URL,
                "api_key_configured": bool(OPENAI_API_KEY)
            },
            "embedding": {
                "provider": EMBED_PROVIDER,
                "model": BAAI_MODEL if EMBED_PROVIDER == "baai" else "OpenAI"
            },
            "rag": {
                "top_k": TOP_K,
                "min_score": RAG_MIN_SCORE
            },
            "neo4j": {
                "available": neo4j_available,
                "uri": os.environ.get("NEO4J_URI", "未配置")
            },
            "database": {
                "path": DEFAULT_DB_PATH,
                "exists": os.path.exists(DEFAULT_DB_PATH)
            }
        }
    }


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_users": len(set(data["username"] for data in ACTIVE_TOKENS.values()))
    }


if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("金融AI风险评估系统 - 后端服务")
    print("=" * 60)
    print(f"服务地址: http://localhost:8000")
    print(f"API文档: http://localhost:8000/docs")
    print(f"测试账号: admin / admin123")
    print(f"         analyst / analyst123")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
