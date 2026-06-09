@echo off
REM Auto-restart backend launcher for Windows
REM This script detects when uvicorn crashes and restarts it.
cd /d D:\XM\smart-doc-qa

:restart
echo [%date% %time%] Starting backend...
set PYTHONPATH=D:\XM\smart-doc-qa
D:\Anaconda\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
echo [%date% %time%] Backend crashed! Restarting in 3 seconds...
timeout /t 3 /nobreak >nul
goto restart
