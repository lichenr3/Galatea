#!/bin/bash
# Galatea Installation Script for Linux/Mac

echo "========================================"
echo "  Galatea - Installation Script"
echo "========================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 not found! Please install Python 3.13+"
    exit 1
fi
echo "[OK] Python found: $(python3 --version)"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "[ERROR] Node.js not found! Please install Node.js 18+"
    exit 1
fi
echo "[OK] Node.js found: $(node --version)"
echo ""

# Install Backend Dependencies
echo "[1/2] Installing Backend Dependencies..."
cd galatea_server

# Check if uv is available
if command -v uv &> /dev/null; then
    echo "Using uv (recommended)..."
    uv sync
else
    echo "Using pip..."
    echo "Tip: Install uv for better dependency management: pip install uv"
    pip3 install -e .
fi
cd ..
echo "[OK] Backend dependencies installed"
echo ""

# Install Frontend Dependencies
echo "[2/2] Installing Frontend Dependencies..."
cd galatea_client
npm install
cd ..
echo "[OK] Frontend dependencies installed"
echo ""

# Check .env files
echo ""
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

