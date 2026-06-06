@echo off
REM Smart Doc QA - 后端启动（双击运行）
REM 关闭此窗口 = 停止后端

echo ========================================
echo  Smart Doc QA 后端服务
echo ========================================
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0start_backend.ps1"

pause
