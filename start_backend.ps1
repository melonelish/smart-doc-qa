# Smart Doc QA - 后端守护脚本 (修复版)
# 用法：powershell -ExecutionPolicy Bypass -File start_backend.ps1

$BackendDir = "D:\XM\smart-doc-qa"
$PythonExe   = "D:\Anaconda\python.exe"
$LogFile     = "$BackendDir\backend.log"

# 确保工作目录存在
if (-not (Test-Path $BackendDir)) {
    Write-Host "[ERROR] 目录不存在: $BackendDir" -ForegroundColor Red
    pause; exit 1
}

function Test-Backend {
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:8000/" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

function Start-BackendProc {
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 🚀 启动后端..." -ForegroundColor Cyan
    $p = Start-Process -FilePath $PythonExe `
        -ArgumentList "-u", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000" `
        -WorkingDirectory $BackendDir `
        -RedirectStandardOutput $LogFile `
        -RedirectStandardError $LogFile `
        -PassThru `
        -WindowStyle Hidden
    # 等待启动
    $tries = 0
    while ($tries -lt 10) {
        Start-Sleep -Seconds 2
        if (Test-Backend) { return $p }
        $tries++
    }
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ⚠️  启动超时，请检查 $LogFile" -ForegroundColor Yellow
    return $p
}

# 首次启动
$proc = Start-BackendProc
Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ✅ 后端已启动 (PID: $($proc.Id))" -ForegroundColor Green
Write-Host "📝 日志: $LogFile" -ForegroundColor Yellow
Write-Host "⚠️  关闭此窗口将停止后端" -ForegroundColor Yellow
Write-Host "─" -ForegroundColor DarkGray

# 守护循环
while ($true) {
    Start-Sleep -Seconds 5
    $alive = -not $proc.HasExited
    $responsive = Test-Backend

    if (-not $alive -or -not $responsive) {
        if (-not $alive) {
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ❌ 进程已退出 (code: $($proc.ExitCode))，重启中..." -ForegroundColor Red
        } else {
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ⚠️  进程僵死，强制重启..." -ForegroundColor Yellow
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2
        }
        $proc = Start-BackendProc
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ✅ 后端已重启 (PID: $($proc.Id))" -ForegroundColor Green
    }
}
