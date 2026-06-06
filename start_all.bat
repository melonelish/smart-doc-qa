@echo off
REM Smart Doc QA - 一键启动前后端（双击运行）
REM 会打开两个窗口，分别运行前端和后端
REM 关闭两个窗口 = 停止所有服务

echo ========================================
echo  Smart Doc QA 一键启动
echo ========================================
echo.
echo 即将打开两个窗口：
echo   [窗口1] 后端服务 (端口 8000)
echo   [窗口2] 前端服务 (端口 5173)
echo.
echo 关闭两个窗口即可停止所有服务
echo ========================================
echo.
pause

start "SmartDocQA-Backend" cmd /k "powershell -ExecutionPolicy Bypass -File \"%~dp0start_backend.ps1\""
timeout /t 3 >nul
start "SmartDocQA-Frontend" cmd /k "powershell -ExecutionPolicy Bypass -File \"%~dp0start_frontend.ps1\""

echo.
echo ✅ 已启动两个服务窗口
echo 🌐 浏览器访问：http://127.0.0.1:5173
echo.
pause
