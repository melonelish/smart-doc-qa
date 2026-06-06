# Smart Doc QA - 前端守护脚本
# 用法：powershell -ExecutionPolicy Bypass -File start_frontend.ps1

$FrontendDir = "D:\XM\smart-doc-qa\frontend"
$LogFile    = "D:\XM\smart-doc-qa\frontend.log"

function Test-Frontend {
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:5173/" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

function Start-FrontendProc {
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 🚀 启动前端..." -ForegroundColor Cyan
    $p = Start-Process -FilePath "npm.cmd" `
        -ArgumentList "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173", "--force" `
        -WorkingDirectory $FrontendDir `
        -RedirectStandardOutput $LogFile `
        -RedirectStandardError $LogFile `
        -PassThru `
        -WindowStyle Hidden
    Start-Sleep -Seconds 6
    return $p
}

$proc = Start-FrontendProc
Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ✅ 前端已启动 (PID: $($proc.Id))" -ForegroundColor Green
Write-Host "📝 日志: $LogFile" -ForegroundColor Yellow
Write-Host "🌐 访问: http://127.0.0.1:5173" -ForegroundColor Cyan
Write-Host "⚠️  关闭此窗口将停止前端" -ForegroundColor Yellow
Write-Host "─" -ForegroundColor DarkGray

while ($true) {
    Start-Sleep -Seconds 5
    $alive = -not $proc.HasExited
    $responsive = Test-Frontend

    if (-not $alive -or -not $responsive) {
        if (-not $alive) {
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ❌ 进程已退出 (code: $($proc.ExitCode))，重启中..." -ForegroundColor Red
        } else {
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ⚠️  进程僵死，强制重启..." -ForegroundColor Yellow
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2
        }
        $proc = Start-FrontendProc
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ✅ 前端已重启 (PID: $($proc.Id))" -ForegroundColor Green
    }
}
