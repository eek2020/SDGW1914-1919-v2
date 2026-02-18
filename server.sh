#!/usr/bin/env bash
# SDGW 1914-1919 Flask Server Control
# Usage: ./server.sh [start|stop|restart|status]

PORT=5001
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
PIDFILE="/tmp/sdgw_server.pid"
LOGFILE="$APP_DIR/logs/sdgw_server.log"
mkdir -p "$APP_DIR/logs"

# Generate a secret key if not already set
export FLASK_SECRET_KEY="${FLASK_SECRET_KEY:-$(python3 -c 'import secrets; print(secrets.token_hex(32))')}"

start_server() {
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
        echo "Server already running (PID $(cat "$PIDFILE")) on http://127.0.0.1:$PORT"
        return 1
    fi

    echo "Starting SDGW server on http://127.0.0.1:$PORT ..."
    cd "$APP_DIR"
    nohup python3 -u src/web_app.py > "$LOGFILE" 2>&1 &
    echo $! > "$PIDFILE"
    sleep 1

    if kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
        echo "Server started (PID $(cat "$PIDFILE"))"
        echo "Log: $LOGFILE"
    else
        echo "Failed to start. Check log: $LOGFILE"
        rm -f "$PIDFILE"
        return 1
    fi
}

stop_server() {
    if [ ! -f "$PIDFILE" ]; then
        echo "No PID file found. Checking for stray processes..."
        local pids
        pids=$(lsof -ti :$PORT 2>/dev/null)
        if [ -n "$pids" ]; then
            echo "Killing processes on port $PORT: $pids"
            echo "$pids" | xargs kill 2>/dev/null
            sleep 1
            echo "Stopped."
        else
            echo "Server not running."
        fi
        return 0
    fi

    local pid
    pid=$(cat "$PIDFILE")
    if kill -0 "$pid" 2>/dev/null; then
        echo "Stopping server (PID $pid)..."
        kill "$pid" 2>/dev/null
        sleep 1
        # Force kill if still running
        if kill -0 "$pid" 2>/dev/null; then
            kill -9 "$pid" 2>/dev/null
            sleep 0.5
        fi
        echo "Stopped."
    else
        echo "Server not running (stale PID file)."
    fi
    rm -f "$PIDFILE"
}

restart_server() {
    echo "Restarting SDGW server..."
    stop_server
    sleep 1
    start_server
}

show_status() {
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
        echo "Server is RUNNING (PID $(cat "$PIDFILE")) on http://127.0.0.1:$PORT"
    else
        local pids
        pids=$(lsof -ti :$PORT 2>/dev/null)
        if [ -n "$pids" ]; then
            echo "Server is RUNNING (PID $pids) on port $PORT (no PID file)"
        else
            echo "Server is STOPPED"
        fi
    fi
}

case "${1:-start}" in
    start)   start_server ;;
    stop)    stop_server ;;
    restart) restart_server ;;
    status)  show_status ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
