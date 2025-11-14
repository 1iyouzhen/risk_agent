# 调试指南 - 前后端连接问题

## 问题诊断步骤

### 1. 检查后端服务是否运行

**方法1：访问健康检查端点**
```bash
# PowerShell
curl http://localhost:8000/api/health

# 或在浏览器中访问
http://localhost:8000/api/health
```

**预期输出：**
```json
{"status":"healthy","timestamp":"2025-11-14T22:10:43.832766","active_users":0}
```

**方法2：访问API文档**
```
http://localhost:8000/docs
```

如果能看到Swagger文档页面，说明后端正常运行。

### 2. 测试登录API

**使用PowerShell测试：**
```powershell
$body = @{username='admin'; password='admin123'} | ConvertTo-Json
Invoke-RestMethod -Uri 'http://localhost:8000/api/auth/login' -Method Post -Body $body -ContentType 'application/json'
```

**预期输出：**
```
success token                                       user
------- -----                                       ----
   True D9C_vrkmKXO30zbDzwc4HXAy3ikpFAqlm0EjOyo8f9k @{username=admin; role=admin}
```

### 3. 使用测试页面

打开 `test_login.html` 文件进行测试：
- 默认用户名：admin
- 默认密码：admin123
- 点击登录按钮
- 查看结果和浏览器控制台

### 4. 检查浏览器控制台

**打开方式：**
- Chrome/Edge: F12 或 右键 → 检查
- Firefox: F12 或 右键 → 检查元素

**查看内容：**
1. Console标签 - 查看JavaScript错误
2. Network标签 - 查看网络请求

**常见错误：**

#### 错误1: CORS错误
```
Access to fetch at 'http://localhost:8000/api/auth/login' from origin 'null' 
has been blocked by CORS policy
```

**解决方案：**
- 确保后端CORS配置正确（已配置allow_origins=["*"]）
- 使用本地服务器打开HTML而不是直接打开文件
```bash
python -m http.server 8080
# 然后访问 http://localhost:8080/index.html
```

#### 错误2: 网络错误
```
Failed to fetch
TypeError: Failed to fetch
```

**解决方案：**
- 检查后端是否运行
- 检查端口8000是否被占用
- 检查防火墙设置

#### 错误3: 401 Unauthorized
```
{"detail":"未提供认证令牌"}
```

**原因：** 查询时未携带Token

**解决方案：** 确保登录后再进行查询

## 完整测试流程

### 步骤1：启动后端
```bash
python auth_server.py
```

**验证：** 看到以下输出
```
============================================================
金融AI风险评估系统 - 后端服务
============================================================
服务地址: http://localhost:8000
API文档: http://localhost:8000/docs
测试账号: admin / admin123
         analyst / analyst123
============================================================
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 步骤2：测试健康检查
```bash
curl http://localhost:8000/api/health
```

### 步骤3：使用本地服务器打开前端
```bash
# 在项目目录下运行
python -m http.server 8080

# 然后在浏览器访问
http://localhost:8080/index.html
```

**重要：** 不要直接双击打开index.html，这会导致CORS问题！

### 步骤4：登录测试
1. 点击右上角"登录"按钮
2. 输入用户名：admin
3. 输入密码：admin123
4. 点击登录

**预期结果：**
- 登录按钮消失
- 显示用户名和退出按钮
- 可以开始提问

### 步骤5：查询测试
输入以下问题之一：
- 查询三木集团的最新风险状况
- 分析农产品行业的系统性风险
- 生成海螺新材的风险评估报告

**预期结果：**
- 显示"正在思考"动画
- 1-3秒后显示AI回答
- 回答包含检索证据和结构化内容

## 常见问题解决

### Q1: 点击登录没反应

**检查清单：**
- [ ] 打开浏览器控制台（F12）查看错误
- [ ] 确认后端服务已启动
- [ ] 确认使用本地服务器打开（不是file://协议）
- [ ] 检查Network标签是否有请求发出

**解决方案：**
```bash
# 1. 确保后端运行
python auth_server.py

# 2. 使用本地服务器
python -m http.server 8080

# 3. 访问 http://localhost:8080/test_login.html 测试
```

### Q2: 登录后无法提问

**检查：**
1. 打开浏览器控制台
2. 输入：`console.log(authToken)`
3. 应该显示一个长字符串

**如果显示null：**
- 重新登录
- 清除浏览器缓存
- 检查localStorage：`localStorage.getItem('authToken')`

### Q3: 提问后一直加载

**可能原因：**
1. 数据库未初始化
2. LLM API配置错误
3. 网络超时

**解决方案：**
```bash
# 1. 初始化数据库
python app.py --demo

# 2. 检查配置
python -c "from src.agent.config import OPENAI_API_KEY; print('API Key:', 'OK' if OPENAI_API_KEY else 'NOT SET')"

# 3. 查看后端日志
# 在运行auth_server.py的终端查看错误信息
```

### Q4: 返回"知识库中暂无相关信息"

**原因：** 数据库中没有相关数据

**解决方案：**
```bash
# 生成测试数据
python app.py --demo

# 验证数据
python -c "import sqlite3; conn = sqlite3.connect('risk_agent.sqlite'); print('记录数:', conn.execute('SELECT COUNT(*) FROM assessments').fetchone()[0])"
```

## 调试技巧

### 1. 查看后端日志
运行auth_server.py的终端会显示所有请求：
```
INFO:     127.0.0.1:56101 - "POST /api/auth/login HTTP/1.1" 200 OK
INFO:     127.0.0.1:56102 - "POST /api/chat/query HTTP/1.1" 200 OK
```

### 2. 使用浏览器开发者工具

**Network标签：**
- 查看请求URL
- 查看请求Headers
- 查看请求Body
- 查看响应内容

**Console标签：**
- 查看JavaScript错误
- 手动测试API：
```javascript
fetch('http://localhost:8000/api/health')
  .then(r => r.json())
  .then(d => console.log(d))
```

### 3. 使用Postman或curl测试

**测试登录：**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

**测试查询：**
```bash
curl -X POST http://localhost:8000/api/chat/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{"query":"查询三木集团","history":[]}'
```

## 端口冲突解决

如果8000端口被占用：

**查找占用进程：**
```powershell
netstat -ano | Select-String ":8000"
```

**修改端口：**
1. 编辑 `auth_server.py`，修改最后一行：
```python
uvicorn.run(app, host="0.0.0.0", port=8001)  # 改为8001
```

2. 编辑 `index.html`，修改API_BASE_URL：
```javascript
const API_BASE_URL = 'http://localhost:8001';  // 改为8001
```

## 完整测试脚本

创建 `test_full.bat`：
```batch
@echo off
echo 测试后端服务...
curl http://localhost:8000/api/health
echo.
echo.
echo 测试登录...
powershell -Command "$body = @{username='admin'; password='admin123'} | ConvertTo-Json; Invoke-RestMethod -Uri 'http://localhost:8000/api/auth/login' -Method Post -Body $body -ContentType 'application/json'"
echo.
echo 测试完成！
pause
```

## 获取帮助

如果以上方法都无法解决问题：

1. 查看后端完整日志
2. 查看浏览器控制台完整错误
3. 运行 `python test_api.py` 查看API是否正常
4. 检查Python版本（需要3.8+）
5. 检查依赖包是否完整安装

---

**记住：** 始终使用本地服务器（http://localhost）打开HTML文件，不要直接双击打开！
