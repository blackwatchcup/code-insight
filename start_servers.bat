@echo off
echo ========================================
echo CodeInsight Start Servers
echo ========================================

echo.
echo [Step 1/3] Stopping old services...
call stop_servers.bat

echo.
echo [Step 2/3] Starting backend...
cd backend
start "CodeInsight Backend" cmd /k "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
echo Backend starting on port 8000...

echo.
echo [Step 3/3] Starting frontend...
cd ..\frontend
start "CodeInsight Frontend" cmd /k "npm run dev"
echo Frontend starting on port 5173...

echo.
echo ========================================
echo Services started successfully!
echo.
echo Access URLs:
echo   Frontend: http://localhost:5173
echo   Backend:  http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo.
echo Run stop_servers.bat to stop services
echo ========================================
pause
