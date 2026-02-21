@echo off
echo ========================================
echo CodeInsight Stop Servers
echo ========================================

echo.
echo [1/2] Stopping backend...
taskkill /F /IM python.exe /T >nul 2>&1
if %errorlevel% == 0 (
    echo Backend stopped
) else (
    echo No backend running
)

echo.
echo [2/2] Stopping frontend...
taskkill /F /IM node.exe /T >nul 2>&1
if %errorlevel% == 0 (
    echo Frontend stopped
) else (
    echo No frontend running
)

echo.
echo All services stopped
echo ========================================
pause
