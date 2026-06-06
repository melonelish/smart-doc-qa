@echo off
REM Smart Doc QA - 前端启动（双击运行）
REM 关闭此窗口 = 停止前端

echo ========================================
echo  Smart Doc QA 前端服务
echo ========================================
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0start_frontend.ps1"

pause
