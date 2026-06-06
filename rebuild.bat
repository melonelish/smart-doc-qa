@echo off
echo === SmartDocQA 自动构建 + 重启 ===

echo [1/3] 构建前端...
cd /d %~dp0frontend
call npx vite build
if errorlevel 1 (
    echo [错误] 前端构建失败！
    pause
    exit /b 1
)
echo [2/3] 停止旧后端...
taskkill /F /IM python.exe >nul 2>&1

echo [3/3] 启动后端...
cd /d %~dp0
start "SmartDocQA" cmd /c "python -m app.main"

echo === 完成！刷新 http://localhost:8000 ===
