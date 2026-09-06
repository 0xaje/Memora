#!/usr/bin/env bash
set -e

echo "========================================================"
echo "Starting MEMORA — Full Operational Stack (Backend + UI)"
echo "========================================================"

# Determine repo root
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Check if port 8000 is already in use
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "[!] Port 8000 is already in use. Assuming Memora backend is already running."
    BACKEND_STARTED=0
else
    echo "[+] Launching Memora FastAPI backend on http://localhost:8000..."
    .venv/bin/uvicorn memora.api.app:app --host 0.0.0.0 --port 8000 --reload &
    BACKEND_PID=$!
    BACKEND_STARTED=1
fi

cleanup() {
    if [ "$BACKEND_STARTED" -eq 1 ] && [ -n "$BACKEND_PID" ]; then
        echo ""
        echo "[*] Shutting down Memora backend (PID $BACKEND_PID)..."
        kill "$BACKEND_PID" 2>/dev/null || true
    fi
}
trap cleanup EXIT INT TERM

# Wait up to 5 seconds for backend to become responsive
echo "[*] Waiting for Sibyl Memory backend readiness..."
for i in {1..10}; do
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        echo "[✓] Backend ready! Sibyl Memory connected."
        break
    fi
    sleep 0.5
done

# Launch frontend
echo "[+] Starting Memora Operations Console UI..."
npm run dev --prefix frontend
