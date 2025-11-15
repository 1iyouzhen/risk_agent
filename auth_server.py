
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
def llm_chat(messages, temperature=0.2):
    from src.agent.config import OPENAI_API_KEY, OPENAI_CHAT_MODEL, OPENAI_BASE_URL, REQUEST_TIMEOUT, REQUEST_RETRIES
    import json as _json
    import time as _time
    import requests as _requests
    if not OPENAI_API_KEY:
        return ""
    url = OPENAI_BASE_URL.rstrip("/") + "/v1/chat/completions"
    headers = {"Authorization": "Bearer " + OPENAI_API_KEY, "Content-Type": "application/json"}
    payload = {"model": OPENAI_CHAT_MODEL, "messages": messages, "temperature": temperature}
    last = None
    for _ in range(max(1, REQUEST_RETRIES)):
        try:
            resp = _requests.post(url, headers=headers, data=_json.dumps(payload), timeout=REQUEST_TIMEOUT)
            if resp.status_code == 200:
                j = resp.json()
                return j.get("choices", [{}])[0].get("message", {}).get("content", "")
            last = Exception(f"http {resp.status_code}")
        except Exception as e:
            last = e
        _time.sleep(0.5)
    return ""

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
    
    # 统计检索来源
    sources_stats = {}
    for h in hits:
        source = h.get("source", "unknown")
        sources_stats[source] = sources_stats.get(source, 0) + 1
    
    # 构建上下文
    context_parts = []
    
    # 添加检索证据（优化展示）
    if hits:
        evidence_by_source = {}
        for h in hits:
            source = h.get("source", "unknown")
            if source not in evidence_by_source:
                evidence_by_source[source] = []
            text = h.get("text", "")
            if text:
                evidence_by_source[source].append(text)
        
        for source, texts in evidence_by_source.items():
            source_name = {
                "history": "历史评估记录",
                "knowledge": "专业知识库",
                "vector": "向量数据库",
                "graph_csv": "关系图谱(CSV)",
                "graph_neo4j": "知识图谱(Neo4j)"
            }.get(source, source)
            context_parts.append(f"【{source_name}】\n" + "\n".join(texts[:3]))
    
    # 添加对话历史
    if request.history:
        history_text = "\n".join([
            f"{msg['role']}: {msg['content']}" 
            for msg in request.history[-6:]  # 最近3轮对话
        ])
        context_parts.append(f"【对话历史】\n{history_text}")
    
    # 构建Prompt
    system_prompt = """你是专业的金融风控分析师。请基于提供的检索证据回答用户问题。

要求：
1. 如果检索证据不足，明确告知"知识库中暂无相关信息"，不要编造内容
2. 如果有足够证据，输出结构化回答，包含：
   【主要风险】：总结关键风险点（列表形式，每条独立成行）
   【指标说明】：解释相关指标和证据（列表形式，每条独立成行）
   【应对建议】：提出具体可执行的措施（列表形式，每条独立成行）
3. 保持专业、准确、简洁
4. 尽量引用检索证据中的具体数据和事实"""
    
    user_prompt = "\n\n".join(context_parts) + f"\n\n用户查询：{query}"
    
    # 调用LLM生成回答
    answer = ""
    llm_error = None
    
    if is_valid:
        try:
            answer = llm_chat([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ], temperature=0.25)
            
            if not answer:
                answer = "AI服务返回为空，以下是检索到的相关信息：\n\n" + "\n".join([
                    f"• {h.get('text', '')[:200]}" for h in hits[:5]
                ])
        except Exception as e:
            llm_error = str(e)
            print(f"LLM调用错误: {e}")
            answer = f"抱歉，AI服务暂时不可用（{llm_error[:100]}）。以下是检索到的相关信息：\n\n" + "\n".join([
                f"• {h.get('text', '')[:200]}" for h in hits[:5]
            ])
    else:
        answer = "知识库中暂无相关信息。请尝试：\n• 使用更具体的企业名称或关键词\n• 查询已有数据的企业（如：三木集团、海螺新材、冀凯股份、农产品、胜利股份）\n• 运行 python app.py --demo 初始化数据库"
    
    # 保存到用户会话
    if username not in USER_SESSIONS:
        USER_SESSIONS[username] = []
    
    USER_SESSIONS[username].append({
        "query": query,
        "answer": answer,
        "timestamp": datetime.now().isoformat(),
        "hits_count": len(hits),
        "sources": sources_stats
    })
    
    # 保存查询记录到数据库
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        html_dir = os.path.join(os.getcwd(), "html_reports")
        os.makedirs(html_dir, exist_ok=True)
        
        filename = f"query_{username}_{timestamp}.html"
        filepath = os.path.join(html_dir, filename)
        
        # 格式化检索证据
        evidence_html = ""
        for i, h in enumerate(hits[:10]):
            source = h.get("source", "unknown")
            score = h.get("score", 0.0)
            text = h.get("text", "")[:500]
            evidence_html += f"""
            <div style="margin-bottom: 15px; padding: 10px; background: #f9f9f9; border-left: 3px solid #667eea;">
                <div style="color: #666; font-size: 12px; margin-bottom: 5px;">
                    来源: {source} | 相关度: {score:.4f}
                </div>
                <div>{text}</div>
            </div>
            """
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset='utf-8'>
            <title>查询结果 - {query}</title>
            <style>
                body {{ font-family: "Microsoft YaHei", sans-serif; margin: 40px; background: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                h2 {{ color: #667eea; border-bottom: 2px solid #667eea; padding-bottom: 10px; }}
                h3 {{ color: #444; margin-top: 30px; }}
                .meta {{ background: #f0f0f0; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .meta p {{ margin: 5px 0; }}
                .evidence {{ margin: 20px 0; }}
                .answer {{ background: #e8f4f8; padding: 20px; border-radius: 8px; margin: 20px 0; line-height: 1.8; }}
                .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
                .stat-card {{ flex: 1; background: #f9f9f9; padding: 15px; border-radius: 5px; text-align: center; }}
                .stat-card .number {{ font-size: 24px; font-weight: bold; color: #667eea; }}
                .stat-card .label {{ font-size: 12px; color: #666; margin-top: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>🔍 查询记录</h2>
                <div class="meta">
                    <p><strong>用户：</strong>{username}</p>
                    <p><strong>时间：</strong>{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                    <p><strong>查询：</strong>{query}</p>
                </div>
                
                <div class="stats">
                    <div class="stat-card">
                        <div class="number">{len(hits)}</div>
                        <div class="label">检索命中数</div>
                    </div>
                    <div class="stat-card">
                        <div class="number">{len(sources_stats)}</div>
                        <div class="label">数据源数量</div>
                    </div>
                    <div class="stat-card">
                        <div class="number">{'是' if is_valid else '否'}</div>
                        <div class="label">证据充分性</div>
                    </div>
                </div>
                
                <h3>📊 检索证据（{len(hits)}条）</h3>
                <div class="evidence">
                    {evidence_html if evidence_html else '<p>暂无检索结果</p>'}
                </div>
                
                <h3>🤖 AI分析结果</h3>
                <div class="answer">
                    {answer.replace(chr(10), '<br>')}
                </div>
                
                {f'<div style="color: red; margin-top: 20px;"><strong>错误信息：</strong>{llm_error}</div>' if llm_error else ''}
            </div>
        </body>
        </html>
        """
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        print(f"查询记录已保存: {filepath}")
    except Exception as e:
        print(f"保存查询记录失败: {e}")
    
    return {
        "success": True,
        "query": query,
        "answer": answer,
        "hits": hits[:10],  # 只返回前10条
        "sources_stats": sources_stats,
        "valid": is_valid,
        "timestamp": datetime.now().isoformat(),
        "llm_error": llm_error
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


@app.post("/api/risk/assess")
async def risk_assess(request: Dict[str, Any], username: str = Depends(verify_token)):
    """
    风险评估接口
    接收企业数据，返回风险评分和分析报告
    """
    try:
        from src.agent.models.risk_forecast import RiskForecaster
        from src.agent.explainability import explain_contributions
        from src.agent.reporting import generate_report
        
        # 获取输入数据
        entity_id = request.get("entity_id", "未知企业")
        record = request.get("data", {})
        
        if not record:
            raise HTTPException(status_code=400, detail="缺少评估数据")
        
        # 初始化模型
        forecaster = RiskForecaster()
        
        # 计算风险评分
        risk_score = forecaster.score(record)
        
        # 计算特征贡献度
        contributions = explain_contributions(record)
        
        # 生成报告
        report_text = generate_report(
            {"entity_id": entity_id, "company_name": entity_id},
            risk_score,
            contributions,
            [], [], [], ""
        )
        
        # 保存到数据库
        db_path = os.environ.get("DB_PATH", DEFAULT_DB_PATH)
        storage = Storage(db_path)
        storage.init()
        
        timestamp = record.get("timestamp", datetime.now().strftime("%Y-%m-%d"))
        assessment_id = storage.save_assessment(entity_id, timestamp, risk_score, "")
        storage.save_report(assessment_id, report_text)
        
        # 保存特征
        for feature, value in record.items():
            if feature not in ["entity_id", "timestamp"]:
                try:
                    storage.save_feature(
                        assessment_id,
                        feature,
                        float(value),
                        float(contributions.get(feature, 0.0))
                    )
                except:
                    pass
        
        return {
            "success": True,
            "entity_id": entity_id,
            "risk_score": risk_score,
            "risk_level": "高风险" if risk_score >= 0.7 else "中风险" if risk_score >= 0.5 else "低风险",
            "contributions": contributions,
            "report": report_text,
            "assessment_id": assessment_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"风险评估错误: {e}")
        raise HTTPException(status_code=500, detail=f"评估失败: {str(e)}")


@app.get("/api/risk/history/{entity_id}")
async def get_risk_history(entity_id: str, username: str = Depends(verify_token)):
    """获取企业的历史风险评估记录"""
    try:
        db_path = os.environ.get("DB_PATH", DEFAULT_DB_PATH)
        storage = Storage(db_path)
        storage.init()
        
        # 查询历史记录
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, timestamp, risk_score, decision
            FROM assessments
            WHERE entity_id = ?
            ORDER BY timestamp DESC
            LIMIT 50
        """, (entity_id,))
        
        records = []
        for row in cursor.fetchall():
            records.append({
                "id": row[0],
                "timestamp": row[1],
                "risk_score": row[2],
                "decision": row[3]
            })
        
        conn.close()
        
        return {
            "success": True,
            "entity_id": entity_id,
            "count": len(records),
            "records": records
        }
        
    except Exception as e:
        print(f"查询历史记录错误: {e}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


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
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
