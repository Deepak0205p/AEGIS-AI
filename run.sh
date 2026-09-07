#!/usr/bin/env bash
# ==============================================================================
# Air-Gapped Local AI Backend Server Launcher
# ==============================================================================
set -euo pipefail

# 1. Enforce Air-Gapped Sovereign Environment Variables
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export OLLAMA_NO_USAGE_STATS=1
export PYTHONUNBUFFERED=1

# Model Name Configuration (matches exact `ollama list` tag)
export MODEL_NAME="${MODEL_NAME:-deepseek-v4-pro:4b}"
export OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"
export NUM_CTX="${NUM_CTX:-8192}"

echo "======================================================================"
echo "  Sovereign Air-Gapped AI Backend Starting"
echo "  Model: ${MODEL_NAME}"
echo "  Context Window: ${NUM_CTX}"
echo "  Ollama Host: ${OLLAMA_HOST}"
echo "======================================================================"

# 2. Check Ollama Service
if ! curl -s "${OLLAMA_HOST}/api/tags" > /dev/null 2>&1; then
    echo "[!] Ollama is not reachable at ${OLLAMA_HOST}."
    echo "[!] Fix: Run 'ollama serve' in a separate terminal and try again."
    exit 1
fi

# 3. Check Model Tag in Ollama
if ! curl -s "${OLLAMA_HOST}/api/tags" | grep -q "${MODEL_NAME}"; then
    echo "[!] Error: Model '${MODEL_NAME}' is not present in Ollama."
    echo "[!] Fix: Run: ollama serve && ollama pull ${MODEL_NAME}"
    exit 1
fi
echo "[+] Ollama verified with model '${MODEL_NAME}'"

# 4. Build Docker Sandbox (if docker is available)
if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    echo "[+] Building python-sandbox container image..."
    docker build -t python-sandbox -f Dockerfile.sandbox . || echo "[!] Warning: Docker build skipped or failed; will use subprocess sandbox fallback."
else
    echo "[*] Docker daemon not active; using secure local subprocess sandbox fallback."
fi

# 5. Launch FastAPI Backend
echo "[+] Launching FastAPI Uvicorn Server on 0.0.0.0:8000..."
exec uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 1 --ws websockets --log-level info
