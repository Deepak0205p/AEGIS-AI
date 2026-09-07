# Air-Gapped Local AI Chatbot Backend

High-performance, sovereign, air-gapped backend for industrial intranet AI assistance built with **FastAPI** and **Ollama**.

---

## Key Features & Sovereign Architecture

- **Air-Gapped & Offline Guarantee**: Strictly offline runtime with zero external internet dependencies (`HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, `OLLAMA_NO_USAGE_STATS=1`). Outbound network guards block external connections.
- **Single Universal Model**: One single model tag (`deepseek-v4-pro:4b`) serves all modes by dynamically adjusting system prompts and generation parameters.
- **Strict Anti-Hallucination Core**: Prompts enforce that answers are derived only from conversation context and verified sandbox outputs.
- **Isolated Execution Sandbox**: Executes Python code in Docker containers (`--network none`, memory 1G, 1 CPU, 128 PIDs) with subprocess fallback and auto-repair retry loops.
- **Deterministic Deliverable Generators**: Word (`.docx`), Excel (`.xlsx`), and PowerPoint (`.pptx`) deliverables are built via native Python libraries (`python-docx`, `openpyxl`, `python-pptx`, `matplotlib`) from structured model plans.
- **SQLite History & Windowing**: Persists all messages, maintains last 10 messages context window with cached 3-sentence rolling summaries for older turns, and automatically enforces context limits.

---

## 1. Ollama Setup & Model Verification

### Step 1: Start Ollama Server
```bash
ollama serve
```

### Step 2: Verify Exact Model Tag
Check that the active model (`deepseek-v4-pro:4b`) is registered:
```bash
ollama list
```
Expected output:
```text
NAME                  ID              SIZE      MODIFIED
deepseek-v4-pro:4b    4de4edfcd3f9    2.5 GB    15 hours ago
```

If the model is not present, pull it or import it:
```bash
ollama pull deepseek-v4-pro:4b
```

### Step 3: Test Ollama Tags API
```bash
curl -s http://localhost:11434/api/tags
```

---

## 2. Docker Sandbox Image Build

Build the isolated offline Python execution container:
```bash
docker build -t python-sandbox -f Dockerfile.sandbox .
```

---

## 3. Installation & Starting the Server

### Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Start Backend via Script or Uvicorn
**Linux / macOS / Git Bash:**
```bash
chmod +x run.sh
./run.sh
```

**Windows PowerShell:**
```powershell
$env:HF_HUB_OFFLINE="1"
$env:TRANSFORMERS_OFFLINE="1"
$env:OLLAMA_NO_USAGE_STATS="1"
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 4. End-to-End `curl` Test Commands for Every Mode

### Health Check (`GET /api/health`)
```bash
curl -X GET http://localhost:8000/api/health
```
*Expected Response:*
```json
{
  "status": "ok",
  "ollama_connected": true,
  "model": "deepseek-v4-pro:4b",
  "num_ctx": 8192,
  "air_gapped": true
}
```

---

### 1. Auto Mode (Heuristic Keyword Router)
```bash
curl -N -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Can you write a python script to calculate factorial of 10?", "mode": "auto", "chat_id": "test_auto"}'
```
*Emits first SSE event: `data: {"route": "code", "trigger": "python"}`*

---

### 2. Chat Mode (Natural & Anti-Hallucination)
```bash
curl -N -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello! What is the status of boiler unit 4?", "mode": "chat", "chat_id": "test_chat"}'
```

---

### 3. Code Mode (Isolated Sandbox Execution & Output)
```bash
curl -N -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Write a python function to compute numpy mean of [12.5, 14.8, 19.2, 22.1] and print the result.", "mode": "code", "chat_id": "test_code"}'
```
*Streams code and yields verified verbatim stdout in `run_output`.*

---

### 4. Docs Mode (.docx Document Generator)
```bash
curl -N -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Create a formal inspection report document for Pump P-101. Operating pressure is 15.2 bar and vibration is 2.1 mm/s.", "mode": "docs", "chat_id": "test_docs"}'
```
*Yields final SSE event with `generated_file: "/api/files/<file_id>"`.*

---

### 5. Excel Mode (.xlsx Spreadsheet Generator)
```bash
curl -N -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Generate an Excel sheet with monthly turbine maintenance logs: Jan: 45 hrs, Feb: 30 hrs, Mar: 55 hrs.", "mode": "excel", "chat_id": "test_excel"}'
```
*Creates `.xlsx` workbook with formatted tables, column auto-widths, and formulas.*

---

### 6. PowerPoint Mode (.pptx Presentation Generator)
```bash
curl -N -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Generate a PPT presentation deck summarizing refinery safety standards and daily operating checklist.", "mode": "ppt", "chat_id": "test_ppt"}'
```
*Generates `.pptx` slide deck with title slide and categorized sections.*

---

### 7. Chat History API (`GET /api/history/{chat_id}`)
```bash
curl -X GET http://localhost:8000/api/history/test_chat
```

---

### 8. Deliverable Download API (`GET /api/files/{file_id}`)
```bash
curl -O -J http://localhost:8000/api/files/<file_id>
```

---

## File Structure

```
.
├── backend/
│   ├── __init__.py
│   ├── main.py            # FastAPI app, SSE endpoint, file server & health checks
│   ├── config.py          # Offline env vars, exact model tag, paths & logger
│   ├── ollama_client.py   # Unified inference helper & startup verification
│   ├── router.py          # Fast regex heuristic routing (auto -> mode)
│   ├── chat_mode.py       # Natural conversation & anti-hallucination chat
│   ├── code_mode.py       # Python code generator with sandbox runner & self-healing
│   ├── docs_mode.py       # Document planner & builder dispatcher
│   ├── excel_mode.py      # Excel spreadsheet builder wrapper
│   ├── ppt_mode.py        # PowerPoint deck builder wrapper
│   ├── deliverables.py    # Python file builders (python-docx, openpyxl, python-pptx)
│   ├── sandbox.py         # Docker container & subprocess execution sandbox
│   └── db.py              # SQLite storage, 10-message window & cached summaries
├── config.py              # Root-level alias
├── ollama_client.py       # Root-level alias
├── router.py              # Root-level alias
├── chat_mode.py           # Root-level alias
├── code_mode.py           # Root-level alias
├── docs_mode.py           # Root-level alias
├── excel_mode.py          # Root-level alias
├── ppt_mode.py            # Root-level alias
├── deliverables.py        # Root-level alias
├── sandbox.py             # Root-level alias
├── db.py                  # Root-level alias
├── requirements.txt       # Python package dependencies
├── Dockerfile.sandbox     # Isolated execution container definition
├── run.sh                 # Production launcher script
└── README.md              # Documentation
```
