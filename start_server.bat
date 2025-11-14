@echo off
echo ========================================
echo 金融AI风险评估系统 - 启动脚本
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo [1/4] 检查依赖包...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo [提示] 正在安装依赖包...
    pip install fastapi uvicorn python-multipart
)

echo [2/4] 检查数据库...
if not exist "risk_agent.sqlite" (
    echo [提示] 数据库不存在，正在初始化...
    python app.py --demo
)

echo [3/4] 启动后端服务...
start "后端服务" cmd /k python auth_server.py

echo [4/4] 等待服务启动...
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo 服务已启动！
echo ========================================
echo 后端API: http://localhost:8000
echo API文档: http://localhost:8000/docs
echo.
echo 请用浏览器打开 index.html 文件
echo 测试账号: admin / admin123
echo ========================================
echo.
echo 按任意键退出...
pause >nul
