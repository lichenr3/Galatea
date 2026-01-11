@echo off
cd /d "%~dp0"

echo ========================================
echo   Galatea - Installation Script
echo ========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python 3.13+
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [OK] Python found

node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found! Please install Node.js 18+
    echo Download from: https://nodejs.org/
    pause
    exit /b 1
)
echo [OK] Node.js found
echo.

echo [1/2] Installing Backend Dependencies...
cd galatea_server

where uv >nul 2>&1
if not errorlevel 1 (
    echo Using uv (recommended)...
    uv sync
) else (
    echo Using pip...
    echo Tip: Install uv for better dependency management: pip install uv
    
    if not exist .venv (
        echo Creating virtual environment...
        python -m venv .venv
    )
    
    call .venv\Scripts\activate.bat
    pip install -e .
)

if errorlevel 1 (
    echo [ERROR] Backend dependency installation failed!
    pause
    exit /b 1
)

cd ..
echo [OK] Backend dependencies installed
echo.

echo [2/2] Installing Frontend Dependencies...
cd galatea_client
call npm install

if errorlevel 1 (
    echo [ERROR] Frontend dependency installation failed!
    pause
    exit /b 1
)

cd ..
echo [OK] Frontend dependencies installed
echo.

echo Checking configuration files...
if not exist "galatea_server\.env" (
    echo [!] galatea_server\.env not found - Please configure it
) else (
    echo [OK] galatea_server\.env found
)

if not exist "galatea_client\.env" (
    if exist "galatea_client\.env.example" (
        copy "galatea_client\.env.example" "galatea_client\.env" >nul
        echo [OK] Created galatea_client\.env from template
    ) else (
        echo [!] galatea_client\.env.example not found
    )
) else (
    echo [OK] galatea_client\.env found
)

if not exist "galatea_server\.env" (
    echo.
    echo ========================================
    echo   IMPORTANT: Configure API Key
    echo ========================================
    echo.
    echo Please create galatea_server\.env file:
    echo   1. cd galatea_server
    echo   2. copy .env.example .env
    echo   3. Edit .env and add your OPENAI_API_KEY
    echo.
)

echo ========================================
echo   Installation Complete!
echo ========================================
echo.
echo Next steps:
echo   1. Make sure galatea_server\.env is configured
echo   2. Run: start.bat
echo.
pause