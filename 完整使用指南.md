# 完整指南

## 目录
1. [系统架构](#系统架构)
2. [快速启动](#快速启动)
3. [功能详解](#功能详解)
4. [配置说明](#配置说明)
5. [常见问题](#常见问题)

## 系统架构

### 整体架构
```
┌─────────────────┐
│   前端界面      │  index.html (Tailwind CSS)
│   (浏览器)      │
└────────┬────────┘
         │ HTTP/REST API
         ↓
┌─────────────────┐
│  后端服务器     │  auth_server.py (FastAPI)
│  - 认证管理     │
│  - 会话管理     │
│  - API路由      │
└────────┬────────┘
         │
    ┌────┴────┬────────┬────────┐
    ↓         ↓        ↓        ↓
┌────────┐ ┌──────┐ ┌──────┐ ┌──────┐
│SQLite  │ │Vector│ │Neo4j │ │LLM   │
│数据库  │ │Store │ │图库  │ │API   │
└────────┘ └──────┘ └──────┘ └──────┘
```

### 数据流程
1. **用户登录** → Token验证 → 会话创建
2. **用户查询** → 多源检索（并行）→ LLM推理 → 结构化输出
3. **结果保存** → 数据库 + HTML报告

## 快速启动

### 方法一：一键启动（Windows）

```bash
# 双击运行
start_server.bat
```

### 方法二：手动启动

**步骤1：安装依赖**
```bash
pip install -r requirements_web.txt
```

**步骤2：初始化数据库**
```bash
python app.py --demo
```

**步骤3：启动后端服务**
```bash
python auth_server.py
```

**步骤4：打开前端**
- 直接用浏览器打开 `index.html`
- 或使用本地服务器：`python -m http.server 8080`

**步骤5：登录系统**
- 用户名：`admin`
- 密码：`admin123`

## 功能详解

### 1. 用户认证系统

#### 登录流程
```python
POST /api/auth/login
{
  "username": "admin",
  "password": "admin123"
}

# 返回
{
  "success": true,
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "username": "admin",
    "role": "admin"
  }
}
```

#### Token使用
所有后续请求需要在Header中携带Token：
```
Authorization: Bearer YOUR_TOKEN_HERE
```

### 2. 智能查询系统

#### 查询接口
```python
POST /api/chat/query
Headers: Authorization: Bearer TOKEN
{
  "query": "查询三木集团的风险状况",
  "history": [
    {"role": "user", "content": "之前的问题"},
    {"role": "assistant", "content": "之前的回答"}
  ]
}
```

#### 检索流程
系统会并行执行以下检索：

1. **SQLite数据库检索**
   - 查询历史评估记录
   - 匹配entity_id
   - 返回风险评分和报告

2. **向量数据库检索**
   - 使用BAAI/bge-m3嵌入模型
   - 计算语义相似度
   - 返回Top-K相似文档

3. **知识库检索**
   - 从knowledge_docs目录检索
   - TF-IDF关键词匹配
   - 返回相关专业知识

4. **Neo4j图数据库检索**
   - 查询企业关联关系
   - 分析风险传导路径
   - 返回图谱信息

#### 响应格式
```json
{
  "success": true,
  "query": "查询三木集团的风险状况",
  "answer": "【主要风险】\n...\n【指标说明】\n...\n【应对建议】\n...",
  "hits": [
    {
      "text": "检索到的证据文本",
      "score": 0.85,
      "source": "database"
    }
  ],
  "valid": true,
  "timestamp": "2023-11-27T10:30:00"
}
```

### 3. 多轮对话支持

系统自动维护对话上下文：

```javascript
// 前端自动管理
conversationHistory.push({ role: 'user', content: message });
conversationHistory.push({ role: 'assistant', content: response });

// 发送时只传最近10轮
history: conversationHistory.slice(-10)
```

### 4. 配置查询

```bash
GET /api/config/info
Headers: Authorization: Bearer TOKEN

# 返回系统配置信息
{
  "config": {
    "llm": {
      "provider": "OpenAI Compatible",
      "model": "deepseek-chat",
      "api_key_configured": true
    },
    "neo4j": {
      "available": true,
      "uri": "bolt://localhost:7687"
    }
  }
}
```

## 配置说明

### 环境变量配置

创建 `.env` 文件：

```bash
# ===== LLM配置 =====
OPENAI_API_KEY=sk-your-deepseek-api-key
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_CHAT_MODEL=deepseek-chat
OPENAI_EMBED_MODEL=text-embedding-3-small

# ===== 嵌入模型配置 =====
EMBED_PROVIDER=baai  # 可选: baai 或 openai
BAAI_MODEL=BAAI/bge-m3

# ===== Neo4j配置 =====
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# ===== RAG配置 =====
RAG_TOP_K=3
RAG_MIN_SCORE=0.25
RAG_MIN_SOURCES=2
KNOWLEDGE_DIRS=knowledge_docs

# ===== 数据库配置 =====
DB_PATH=risk_agent.sqlite
```

### 配置优先级
1. 环境变量
2. config.json文件
3. 代码中的默认值

## 常见问题

### Q1: 后端启动失败

**错误：** `ModuleNotFoundError: No module named 'fastapi'`

**解决：**
```bash
pip install fastapi uvicorn
```

### Q2: 前端无法连接后端

**错误：** `连接服务器失败`

**检查清单：**
- [ ] 后端是否已启动（访问 http://localhost:8000/docs）
- [ ] 端口8000是否被占用
- [ ] 浏览器控制台是否有CORS错误
- [ ] 防火墙是否阻止连接

**解决：**
```bash
# 检查端口占用
netstat -ano | findstr :8000

# 更换端口
uvicorn auth_server:app --port 8001
```

### Q3: 登录后查询返回空结果

**原因：** 数据库未初始化

**解决：**
```bash
# 运行demo生成测试数据
python app.py --demo

# 验证数据
python -c "import sqlite3; conn = sqlite3.connect('risk_agent.sqlite'); print(conn.execute('SELECT COUNT(*) FROM assessments').fetchone())"
```

### Q4: Neo4j连接失败

**错误：** `Neo4j不可用`

**解决：**
1. 确保Neo4j服务已启动
2. 检查连接配置
3. 系统会自动降级，不影响其他功能

```bash
# 测试Neo4j连接
python -c "from src.agent.neo4j_client import Neo4jClient; print(Neo4jClient().available())"
```

### Q5: LLM调用失败

**错误：** `AI服务暂时不可用`

**检查：**
- [ ] API Key是否正确
- [ ] Base URL是否可访问
- [ ] 账户余额是否充足

**解决：**
```bash
# 测试API连接
curl -X POST https://api.deepseek.com/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"test"}]}'
```

### Q6: 向量检索速度慢

**优化方案：**

1. 使用FAISS加速
```bash
pip install faiss-cpu
```

2. 减少Top-K数量
```bash
export RAG_TOP_K=2
```

3. 启用缓存
```python
# 在auth_server.py中添加
from functools import lru_cache
```

## 测试验证

### 运行测试脚本

```bash
python test_api.py
```

### 手动测试

**1. 测试健康检查**
```bash
curl http://localhost:8000/api/health
```

**2. 测试登录**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

**3. 测试查询**
```bash
curl -X POST http://localhost:8000/api/chat/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"query":"查询三木集团的风险状况","history":[]}'
```

## 生产部署建议

### 1. 安全加固
- 修改默认密码
- 使用HTTPS
- 限制CORS来源
- 添加速率限制

### 2. 性能优化
- 使用Gunicorn/uWSGI
- 启用Redis缓存
- 使用FAISS向量索引
- 数据库连接池

### 3. 监控告警
- 添加日志系统
- 监控API响应时间
- 跟踪错误率
- 设置告警阈值

### 4. 高可用部署
- 负载均衡
- 数据库主从复制
- 服务容器化（Docker）
- 自动扩缩容

## 开发扩展

### 添加新用户

编辑 `auth_server.py`：
```python
USERS_DB["newuser"] = {
    "username": "newuser",
    "password_hash": hashlib.sha256("password".encode()).hexdigest(),
    "role": "analyst"
}
```

### 自定义检索逻辑

在 `auth_server.py` 的 `chat_query` 函数中添加：
```python
# 添加自定义检索源
custom_results = your_custom_retriever(query)
hits.extend(custom_results)
```

### 修改响应格式

在 `index.html` 的 `formatAIResponse` 函数中自定义：
```javascript
function formatAIResponse(data) {
    // 自定义格式化逻辑
    return customHTML;
}
```

## 技术支持

如遇到问题：
1. 查看 `README_WEB.md` 详细文档
2. 检查后端日志输出
3. 访问 http://localhost:8000/docs 查看API文档
4. 运行 `test_api.py` 验证系统状态

---

**祝使用愉快！** 🚀

