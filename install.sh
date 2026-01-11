#!/bin/bash
cd "$(dirname "$0")"

echo "========================================"
echo "  Galatea - Installation Script"
echo "========================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python not found! Please install Python 3.13+"
    echo "Download from: https://www.python.org/downloads/"
    exit 1
fi
echo "[OK] Python found"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "[ERROR] Node.js not found! Please install Node.js 18+"
    echo "Download from: https://nodejs.org/"
    exit 1
fi
echo "[OK] Node.js found"
echo ""

# Install Backend Dependencies
echo "[1/2] Installing Backend Dependencies..."
cd galatea_server

if command -v uv &> /dev/null; then
    echo "Using uv - recommended..."
    uv sync
else
    echo "Using pip..."
    echo "Tip: Install uv for better dependency management: pip install uv"
    
    if [ ! -d ".venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv .venv
    fi
    
    source .venv/bin/activate
    pip install -e .
fi

if [ $? -ne 0 ]; then
    echo "[ERROR] Backend dependency installation failed!"
    exit 1
fi

cd ..
echo "[OK] Backend dependencies installed"
echo ""

# Install Frontend Dependencies
echo "[2/2] Installing Frontend Dependencies..."
cd galatea_client
npm install

if [ $? -ne 0 ]; then
    echo "[ERROR] Frontend dependency installation failed!"
    exit 1
fi

cd ..
echo "[OK] Frontend dependencies installed"
echo ""

# Check configuration files
echo "Checking configuration files..."
if [ ! -f "galatea_server/.env" ]; then
    echo "[!] galatea_server/.env not found - Please configure it"
else
    echo "[OK] galatea_server/.env found"
fi

if [ ! -f "galatea_client/.env" ]; then
    if [ -f "galatea_client/.env.example" ]; then
        cp "galatea_client/.env.example" "galatea_client/.env"
        echo "[OK] Created galatea_client/.env from template"
    else
        echo "[!] galatea_client/.env.example not found"
    fi
else
    echo "[OK] galatea_client/.env found"
fi

if [ ! -f "galatea_server/.env" ]; then
    echo ""
    echo "========================================"
    echo "  IMPORTANT: Configure API Key"
    echo "========================================"
    echo ""
    echo "Please create galatea_server/.env file:"
    echo "  1. cd galatea_server"
    echo "  2. cp .env.example .env"
    echo "  3. Edit .env and add your OPENAI_API_KEY"
    echo ""
fi

echo "========================================"
echo "  Installation Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Make sure galatea_server/.env is configured"
echo "  2. Run: ./start.sh"
echo ""
