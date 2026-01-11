@echo off
cd /d "%~dp0"

echo ========================================
echo   Galatea AI - Launcher
echo ========================================
echo.

if not exist "galatea_client\node_modules" (
    echo [!] First run detected. Running installation...
    call install.bat
    if errorlevel 1 (
        echo [ERROR] Installation failed.
        pause
        exit /b 1
    )
)

if not exist "galatea_server\.env" (
    echo [ERROR] galatea_server\.env not found.
    echo Please copy .env.example to .env and configure your keys.
    pause
    exit /b 1
)

if not exist "galatea_client\.env" (
    if exist "galatea_client\.env.example" (
        copy "galatea_client\.env.example" "galatea_client\.env" >nul
    )
)

echo [1/2] Starting Backend Server...
cd galatea_server

set "SERVER_STARTED=0"

where uv >nul 2>&1
if not errorlevel 1 (
    start "Galatea Server" cmd /k "uv run python run.py"
    set "SERVER_STARTED=1"
) else (
    if exist ".venv\Scripts\activate.bat" (
        start "Galatea Server" cmd /k ".venv\Scripts\activate.bat && python run.py"
        set "SERVER_STARTED=1"
    )
)

if "%SERVER_STARTED%"=="0" (
    echo.
    echo [ERROR] CRITICAL: No virtual environment found!
    echo [!] The server cannot start safely without a virtual environment.
    echo [!] Please run install.bat to set up the environment.
    echo.
    pause
    exit /b 1
)

cd ..

echo [2/2] Waiting for server to start...
timeout /t 4 /nobreak >nul

echo [3/3] Starting Client...
cd galatea_client
start "Galatea Client" cmd /c "npm run dev"
cd ..

echo.
echo ========================================
echo   Galatea is running!
echo   Backend: http://localhost:8000
echo   Frontend: http://localhost:5137
echo ========================================
echo.
echo Press any key to stop...
pause >nul