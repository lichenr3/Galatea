#!/bin/bash
# Galatea Quick Start Script for Linux/Mac

echo "========================================"
echo "  Galatea AI Virtual Character System"
echo "========================================"
echo ""

# Check if server .env exists
if [ ! -f "galatea_server/.env" ]; then
    echo "[ERROR] .env file not found in galatea_server/"
    echo "Please copy .env.example to .env and configure your OPENAI_API_KEY"
    echo ""
    exit 1
fi

# Check if client .env exists (create from example if not)
if [ ! -f "galatea_client/.env" ]; then
    echo "[INFO] Creating galatea_client/.env from .env.example..."
    if [ -f "galatea_client/.env.example" ]; then
        cp "galatea_client/.env.example" "galatea_client/.env"
        echo "[OK] Client .env created"
    else
        echo "[WARNING] galatea_client/.env.example not found"
    fi
    echo ""
fi

# Start backend server
echo "[1/2] Starting Backend Server..."
cd galatea_server

# Check if uv is available
if command -v uv &> /dev/null; then
    echo "Using uv to run server..."
    uv run python run.py &
    SERVER_PID=$!
else
    # Check if virtual environment exists
    if [ -f ".venv/bin/activate" ]; then
        echo "Using virtual environment..."
        source .venv/bin/activate
        python run.py &
        SERVER_PID=$!
    else
        echo "Running with system Python..."
        python3 run.py &
        SERVER_PID=$!
    fi
fi
cd ..

# Wait for server to start
echo "[2/2] Waiting for server to start..."
sleep 5

# Start client
echo "[3/3] Starting Client..."
cd galatea_client
npm run dev &
CLIENT_PID=$!
cd ..

echo ""
echo "========================================"
echo "  Galatea is running!"
echo "  Server: http://localhost:8000"
echo "  Server PID: $SERVER_PID"
echo "  Client PID: $CLIENT_PID"
echo "========================================"
echo ""
echo "Press Ctrl+C to stop..."

# Trap Ctrl+C to cleanup
trap "echo 'Stopping...'; kill $SERVER_PID $CLIENT_PID 2>/dev/null; exit" INT

# Wait for user interrupt
wait

