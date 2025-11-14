@echo off
chcp 65001 >nul
echo ========================================
echo 金融AI风险评估系统 - 完整启动
echo ========================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python
    pause
    exit /b 1
)

echo [1/5] 检查依赖包...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo [提示] 正在安装依赖...
    pip install fastapi uvicorn -q
)

echo [2/5] 检查数据库...
if not exist "risk_agent.sqlite" (
    echo [提示] 初始化数据库（首次运行）...
    python app.py --demo
)

echo [3/5] 启动后端服务...
start "后端服务 - 请勿关闭" cmd /k "python auth_server.py"

echo [4/5] 等待后端启动...
timeout /t 5 /nobreak >nul

echo [5/5] 启动前端服务...
start "前端服务 - 请勿关闭" cmd /k "python -m http.server 8080"

timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo 系统已启动！
echo ========================================
echo.
echo 后端API: http://localhost:8000
echo API文档: http://localhost:8000/docs
echo.
echo 前端界面: http://localhost:8080/index.html
echo 测试页面: http://localhost:8080/test_login.html
echo.
echo 登录账号:
echo   用户名: admin
echo   密码: admin123
echo.
echo ========================================
echo.
echo 正在打开浏览器...
timeout /t 2 /nobreak >nul
start http://localhost:8080/index.html

echo.
echo 提示: 关闭此窗口不会停止服务
echo 要停止服务，请关闭"后端服务"和"前端服务"窗口
echo.
pause
