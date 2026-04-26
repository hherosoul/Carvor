@echo off
chcp 65001 >nul 2>&1
title Carvor - 科研助手

echo ========================================
echo   Carvor 科研助手 - 启动中...
echo ========================================
echo.

cd /d "%~dp0"

if not exist "frontend\dist\index.html" (
    echo [错误] 未找到前端构建文件，请先运行:
    echo   cd frontend ^&^& npm install ^&^& npm run build
    echo.
    pause
    exit /b 1
)

echo [启动] 正在启动 Carvor 服务...
echo [信息] 启动后请在浏览器中访问: http://localhost:5173
echo [信息] 按 Ctrl+C 停止服务
echo.

cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 5173
