#!/bin/bash
cd "$(dirname "$0")"

echo "========================================"
echo "  Galatea AI - Launcher"
echo "========================================"
echo ""

# Check if first run
if [ ! -d "galatea_client/node_modules" ]; then
    echo "[!] First run detected. Running installation..."
    ./install.sh
    if [ $? -ne 0 ]; then
        echo "[ERROR] Installation failed."
        exit 1
    fi
fi

# Check backend configuration
if [ ! -f "galatea_server/.env" ]; then
    echo "[ERROR] galatea_server/.env not found."
    echo "Please copy .env.example to .env and configure your keys."
    exit 1
fi

# Check/create frontend configuration
if [ ! -f "galatea_client/.env" ]; then
    if [ -f "galatea_client/.env.example" ]; then
        cp "galatea_client/.env.example" "galatea_client/.env"
    fi
fi

# Detect OS and terminal
OS_TYPE=$(uname -s)
TERMINAL_CMD=""

case "$OS_TYPE" in
    Darwin*)
        # macOS
        TERMINAL_CMD="osascript"
        ;;
    Linux*)
        # Linux - try to detect available terminal
        if command -v gnome-terminal &> /dev/null; then
            TERMINAL_CMD="gnome-terminal"
        elif command -v konsole &> /dev/null; then
            TERMINAL_CMD="konsole"
        elif command -v xterm &> /dev/null; then
            TERMINAL_CMD="xterm"
        else
            echo "[WARNING] No supported terminal emulator found."
            echo "Terminals checked: gnome-terminal, konsole, xterm"
            echo "Starting in background mode..."
            TERMINAL_CMD="background"
        fi
        ;;
    *)
        echo "[WARNING] Unknown OS: $OS_TYPE. Using background mode."
        TERMINAL_CMD="background"
        ;;
esac

# Start Backend Server
echo "[1/2] Starting Backend Server..."
cd galatea_server

SERVER_STARTED=0

if command -v uv &> /dev/null; then
    CMD_BACKEND="cd $(pwd) && uv run python run.py"
    SERVER_STARTED=1
elif [ -f ".venv/bin/activate" ]; then
    CMD_BACKEND="cd $(pwd) && source .venv/bin/activate && python run.py"
    SERVER_STARTED=1
fi

if [ $SERVER_STARTED -eq 0 ]; then
    echo ""
    echo "[ERROR] CRITICAL: No virtual environment found!"
    echo "[!] The server cannot start safely without a virtual environment."
    echo "[!] Please run ./install.sh to set up the environment."
    echo ""
    exit 1
fi

# Launch backend based on detected terminal
case "$TERMINAL_CMD" in
    osascript)
        osascript -e 'tell app "Terminal" to do script "'"$CMD_BACKEND"'"' &> /dev/null
        ;;
    gnome-terminal)
        gnome-terminal -- bash -c "$CMD_BACKEND; exec bash" &> /dev/null &
        ;;
    konsole)
        konsole -e bash -c "$CMD_BACKEND; exec bash" &> /dev/null &
        ;;
    xterm)
        xterm -e bash -c "$CMD_BACKEND; exec bash" &> /dev/null &
        ;;
    background)
        nohup bash -c "$CMD_BACKEND" > ../backend.log 2>&1 &
        echo "[INFO] Backend running in background. Log: backend.log"
        ;;
esac

cd ..

# Wait for server to start
echo "[2/2] Waiting for server to start..."
sleep 4

# Start Frontend Client
echo "[3/3] Starting Client..."
cd galatea_client
CMD_FRONTEND="cd $(pwd) && npm run dev"

# Launch frontend based on detected terminal
case "$TERMINAL_CMD" in
    osascript)
        osascript -e 'tell app "Terminal" to do script "'"$CMD_FRONTEND"'"' &> /dev/null
        ;;
    gnome-terminal)
        gnome-terminal -- bash -c "$CMD_FRONTEND; exec bash" &> /dev/null &
        ;;
    konsole)
        konsole -e bash -c "$CMD_FRONTEND; exec bash" &> /dev/null &
        ;;
    xterm)
        xterm -e bash -c "$CMD_FRONTEND; exec bash" &> /dev/null &
        ;;
    background)
        nohup bash -c "$CMD_FRONTEND" > ../frontend.log 2>&1 &
        echo "[INFO] Frontend running in background. Log: frontend.log"
        ;;
esac

cd ..

# Read ports from .env files
BACKEND_PORT=8000
if [ -f "galatea_server/.env" ]; then
    PORT_LINE=$(grep "^PORT=" galatea_server/.env | head -n 1)
    if [ ! -z "$PORT_LINE" ]; then
        BACKEND_PORT=$(echo $PORT_LINE | cut -d'=' -f2)
    fi
fi

FRONTEND_PORT=5137
if [ -f "galatea_client/.env" ]; then
    VITE_PORT_LINE=$(grep "^VITE_PORT=" galatea_client/.env | head -n 1)
    if [ ! -z "$VITE_PORT_LINE" ]; then
        FRONTEND_PORT=$(echo $VITE_PORT_LINE | cut -d'=' -f2)
    fi
fi

echo ""
echo "========================================"
echo "  Galatea is running!"
echo "  Backend: http://localhost:$BACKEND_PORT"
echo "  Frontend: http://localhost:$FRONTEND_PORT"
echo "========================================"
echo ""

if [ "$TERMINAL_CMD" = "background" ]; then
    echo "Services are running in background mode."
    echo "Logs: backend.log, frontend.log"
    echo ""
    echo "To stop the services:"
    echo "  pkill -f 'python run.py'"
    echo "  pkill -f 'npm run dev'"
else
    echo "Services are running in separate terminal windows."
    echo "Close the terminal windows to stop the services."
fi
echo ""
