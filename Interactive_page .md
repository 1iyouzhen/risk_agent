# 🚀 前后端说明

## 一分钟启动

### Windows用户
```bash
# 1. 双击运行
start_server.bat

# 2. 打开浏览器访问 index.html
```

### Linux/Mac用户
```bash
# 1. 安装依赖
pip install fastapi uvicorn

# 2. 初始化数据（首次运行）
python app.py --demo

# 3. 启动服务
python auth_server.py

# 4. 打开浏览器访问 index.html
```

## 登录信息

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 管理员 |
| analyst | analyst123 | 分析师 |

## 测试查询

试试这些问题：
- ✅ 查询三木集团的最新风险状况
- ✅ 分析农产品行业的系统性风险
- ✅ 生成海螺新材的风险评估报告
- ✅ 冀凯股份的信用评分如何？

## 核心功能

### 1️⃣ 登录认证
- Token-based身份验证
- 24小时有效期
- 自动保存登录状态

### 2️⃣ 智能查询
- **RAG检索**：从多个数据源检索相关信息
- **知识图谱**：分析企业关联关系
- **LLM推理**：生成结构化报告

### 3️⃣ 多轮对话
- 自动保持上下文
- 支持连续追问
- 每个用户独立会话

### 4️⃣ 报告生成
- 自动保存HTML报告
- 支持导出PDF/CSV
- 可视化风险分析

## 系统架构

```
前端 (index.html)
    ↓ REST API
后端 (auth_server.py)
    ↓
┌───┴───┬────────┬────────┐
│       │        │        │
SQLite  Vector  Neo4j   LLM
数据库  存储    图库    API
```

## API端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/auth/login` | POST | 用户登录 |
| `/api/auth/logout` | POST | 用户登出 |
| `/api/chat/query` | POST | 智能查询 |
| `/api/chat/history` | GET | 对话历史 |
| `/api/config/info` | GET | 系统配置 |
| `/api/health` | GET | 健康检查 |

## 配置文件

### 环境变量 (.env)
```bash
# LLM配置
OPENAI_API_KEY=sk-your-api-key
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_CHAT_MODEL=deepseek-chat

# 嵌入模型
EMBED_PROVIDER=baai
BAAI_MODEL=BAAI/bge-m3

# Neo4j（可选）
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# RAG配置
RAG_TOP_K=3
RAG_MIN_SCORE=0.25
```

## 故障排除

### ❌ 后端启动失败
```bash
pip install fastapi uvicorn
```

### ❌ 前端无法连接
- 检查后端是否启动：访问 http://localhost:8000/docs
- 检查端口是否被占用：`netstat -ano | findstr :8000`

### ❌ 查询返回空结果
```bash
# 初始化数据库
python app.py --demo
```

### ❌ Neo4j连接失败
- 系统会自动降级，不影响其他功能
- 可选：启动Neo4j服务并配置环境变量

## 测试验证

### 自动测试
```bash
python test_api.py
```

### 完整演示
```bash
python demo_full_system.py
```

### 手动测试
```bash
# 健康检查
curl http://localhost:8000/api/health

# 登录
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `index.html` | 前端界面（Tailwind CSS） |
| `auth_server.py` | 后端服务器（FastAPI） |
| `app.py` | 核心业务逻辑 |
| `start_server.bat` | Windows启动脚本 |
| `test_api.py` | API测试脚本 |
| `demo_full_system.py` | 完整功能演示 |
| `config_example.json` | 配置文件示例 |
| `README_WEB.md` | 详细文档 |
| `USAGE_GUIDE.md` | 使用指南 |

## 下一步

1. ✅ 启动系统并登录
2. ✅ 尝试示例查询
3. ✅ 查看生成的HTML报告
4. ✅ 阅读 `USAGE_GUIDE.md` 了解更多
5. ✅ 访问 http://localhost:8000/docs 查看API文档

## 技术栈

- **前端**：HTML5, Tailwind CSS, JavaScript
- **后端**：FastAPI, Python 3.8+
- **数据库**：SQLite, Neo4j
- **AI**：DeepSeek/OpenAI, BAAI/bge-m3
- **向量存储**：Sentence-Transformers

## 获取帮助

- 📖 详细文档：`README_WEB.md`
- 📚 使用指南：`USAGE_GUIDE.md`
- 🔧 API文档：http://localhost:8000/docs
- 🧪 运行测试：`python test_api.py`

---

**祝使用愉快！** 🎉
