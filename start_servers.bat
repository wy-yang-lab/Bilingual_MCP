@echo off
echo 🚀 Starting Bilingual MCP Development Servers...
cd /d "%~dp0"

echo 🔧 Starting FastAPI Backend Server...
start "FastAPI Backend" cmd /k "set PYTHONPATH=. && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 3 /nobreak >nul

echo 🎨 Starting Streamlit UI Server...
start "Streamlit UI" cmd /k "streamlit run ui_app.py --server.port 8501"

echo.
echo ✅ Both servers are starting in separate windows!
echo.
echo 📱 Access your application at:
echo    🌐 Streamlit UI:    http://localhost:8501
echo    🔗 FastAPI Docs:    http://127.0.0.1:8000/docs
echo    ❤️  Health Check:   http://127.0.0.1:8000/health
echo.
echo ⚠️  Keep both command windows open to keep servers running!
echo    Close the windows to stop the servers.
echo.
pause 