# PowerShell script to start both FastAPI and Streamlit servers
# Double-click this file or run: .\run_dev.ps1

Write-Host "🚀 Starting Bilingual MCP Development Servers..." -ForegroundColor Green
Write-Host "📁 Working directory: $PSScriptRoot" -ForegroundColor Yellow

# Change to the script's directory
Set-Location $PSScriptRoot

# Set Python path so 'app' module can be imported
$env:PYTHONPATH = "."

Write-Host "🔧 Starting FastAPI Backend Server..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command", 
    "cd '$PSScriptRoot'; `$env:PYTHONPATH='.'; Write-Host '🔥 FastAPI Server Starting...' -ForegroundColor Red; uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
)

# Wait a moment before starting Streamlit
Start-Sleep -Seconds 2

Write-Host "🎨 Starting Streamlit UI Server..." -ForegroundColor Magenta
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$PSScriptRoot'; Write-Host '🎯 Streamlit UI Starting...' -ForegroundColor Blue; streamlit run ui_app.py --server.port 8501"
)

Write-Host ""
Write-Host "✅ Both servers are starting in separate windows!" -ForegroundColor Green
Write-Host ""
Write-Host "📱 Access your application at:" -ForegroundColor White
Write-Host "   🌐 Streamlit UI:    http://localhost:8501" -ForegroundColor Cyan
Write-Host "   🔗 FastAPI Docs:    http://127.0.0.1:8000/docs" -ForegroundColor Yellow
Write-Host "   ❤️  Health Check:   http://127.0.0.1:8000/health" -ForegroundColor Green
Write-Host ""
Write-Host "⚠️  Keep both PowerShell windows open to keep servers running!" -ForegroundColor Red
Write-Host "   Close the windows or press Ctrl+C in them to stop the servers." -ForegroundColor Yellow
Write-Host ""
Write-Host "Press any key to close this launcher window..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") 