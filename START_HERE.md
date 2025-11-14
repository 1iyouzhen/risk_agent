# 🚀 从这里开始

## 一分钟快速启动

### Windows用户（推荐）

```bash
# 双击运行这个文件
start_full_system.bat
```

等待浏览器自动打开，然后：
1. 点击右上角"登录"
2. 输入：admin / admin123
3. 开始提问！

---

##  重要提示

###  错误的打开方式
- 直接双击 `index.html` 文件
- 这会导致CORS错误，无法连接后端

###  正确的打开方式
- 使用 `start_full_system.bat` 启动
- 或访问 `http://localhost:8080/index.html`

---

## 手动启动（如果自动启动失败）

### 步骤1：启动后端
```bash
python auth_server.py
```

### 步骤2：启动前端（新开一个终端）
```bash
python -m http.server 8080
```

### 步骤3：打开浏览器
```
http://localhost:8080/index.html
```

---

## 登录信息

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 管理员 |
| analyst | analyst123 | 分析师 |

---

## 试试这些问题

登录后可以问：
- ✅ 查询三木集团的最新风险状况
- ✅ 分析农产品行业的系统性风险
- ✅ 生成海螺新材的风险评估报告

---

## 遇到问题？

### 问题1：无法登录
```bash
# 1. 检查后端是否运行
curl http://localhost:8000/api/health

# 2. 使用测试页面
打开 test_login.html 测试
```

### 问题2：返回"知识库中暂无相关信息"
```bash
# 初始化数据库
python app.py --demo
```

### 问题3：其他问题
查看详细调试指南：
- 📖 `DEBUG_GUIDE.md` - 完整调试指南
- 📄 `如何使用.txt` - 简明使用说明

---

## 系统状态检查

### 检查后端
```bash
curl http://localhost:8000/api/health
```

### 检查前端
```
浏览器访问：http://localhost:8080
```

### 运行完整测试
```bash
python test_api.py
```

---

## 📁 重要文件

| 文件 | 说明 |
|------|------|
| `start_full_system.bat` | 一键启动脚本 |
| `index.html` | 主界面 |
| `test_login.html` | 登录测试页面 |
| `auth_server.py` | 后端服务器 |
| `如何使用.txt` | 简明说明 |
| `DEBUG_GUIDE.md` | 调试指南 |

---

## 下一步

1. ✅ 启动系统
2. ✅ 登录账号
3. ✅ 尝试提问
4. ✅ 查看生成的报告（html_reports目录）
5. ✅ 阅读完整文档（README_WEB.md）

---

**现在就开始吧！双击 `start_full_system.bat` 🚀**
