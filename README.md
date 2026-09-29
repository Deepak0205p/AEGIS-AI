# 🛡️ AEGIS AI — Sovereign Industrial AI Workbench
### **100% Air-Gapped, Multimodal Agentic AI System for High-Security Industrial Facilities (MRPL / ONGC)**

[![Smart India Hackathon](https://img.shields.io/badge/SIH%202026-PS%20SIH26117-FF6F00.svg?style=for-the-badge&logo=target)](https://sih.gov.in)
[![Target Organization](https://img.shields.io/badge/Target%20PSU-MRPL%20%7C%20MoPNG-00529B.svg?style=for-the-badge&logo=building)](https://www.mrpl.co.in)
[![Air-Gap Sovereignty](https://img.shields.io/badge/Air--Gap%20Sovereignty-100%25%20Offline%20%26%20Zero%20Egress-00C853.svg?style=for-the-badge&logo=shield)](https://github.com/Deepak0205p/AEGIS-AI)
[![Hardware Budget](https://img.shields.io/badge/Target%20Hardware-Single%206GB%20GPU%20(RTX%203050%2F4060)-76B900.svg?style=for-the-badge&logo=nvidia)](https://nvidia.com)
[![Tech Stack](https://img.shields.io/badge/Stack-FastAPI%20%7C%20Next.js%2014%20%7C%20Ollama%20%7C%20PostgreSQL%2FMySQL-1E88E5.svg?style=for-the-badge)](https://github.com/Deepak0205p/AEGIS-AI)

---

## 📌 Executive Summary (SIH Problem Statement SIH26117)

| Attribute | Specification Details |
| :--- | :--- |
| **Problem Statement ID** | **SIH26117** |
| **Title** | Sovereign On-Premise Agentic AI Workbench using Open-Weight Multimodal LLMs for Confidential Industrial Work |
| **Target Organization** | **Mangalore Refinery and Petrochemicals Limited (MRPL)** & **ONGC** |
| **Nodal Ministry** | **Ministry of Petroleum & Natural Gas (MoPNG)** |
| **Category & Theme** | Smart Automation \| Software Edition |
| **Hardware Deployment Baseline** | Standard Engineer Laptop / Workstation (Single 6GB–8GB VRAM GPU, e.g. RTX 3050 / RTX 4060) |

---

## ⚠️ The Industrial Problem

Critical national infrastructure assets such as refineries (**MRPL 15 MMTPA**) and offshore drilling facilities (**ONGC**) handle classified telemetry, Piping & Instrumentation Diagrams (P&IDs), shift logs, and safety-critical operations under **OISD / ISO 27001 / MoPNG** standards.

Commercial public cloud AI systems (OpenAI, Claude, Copilot) are **strictly forbidden** in these zones due to:
1. **Critical Cyber Egress Risk:** Process logs, P&IDs, and confidential bids cannot leave on-premise networks.
2. **Strict Hardware Constraints:** Heavy 70B+ LLMs require multi-million dollar GPU clusters. Plant field engineers need reliable AI running on **standard 6GB VRAM laptops**.
3. **Catastrophic Hallucinations:** An LLM fabricating a furnace skin temperature, relief valve setpoint, or toxic gas first-aid protocol can cause fatal industrial accidents.
4. **Complex Multimodal Tasks:** Standard chatbots cannot parse complex engineering P&ID diagrams, calculate thermodynamics in isolated sandboxes, or export verifiable Word/Excel/PPT deliverables.

---

## 💡 The Solution: AEGIS AI (REVEAL 2.0)

**AEGIS AI** is a **100% self-hosted, air-gapped sovereign AI workbench** engineered specifically for industrial field operations. It combines quantized open-weight foundation models, real-time chemical safety databases, GraphRAG equipment hierarchy retrieval, and an isolated execution sandbox.

```
                              ┌───────────────────────────────────────────────┐
                              │           AEGIS AI WORKBENCH                  │
                              │       (100% Offline & Air-Gapped)             │
                              └──────────────────────┬────────────────────────┘
                                                     │
               ┌─────────────────────────────────────┴─────────────────────────────────────┐
               ▼                                                                           ▼
┌─────────────────────────────┐                                             ┌─────────────────────────────┐
│    FIELD CHAT & CANVAS UI   │                                             │     ADMIN OBSERVATORY UI    │
│       (:3000 / Next.js)     │                                             │       (:3001 / Next.js)     │
│  - Operator Chat & Canvas   │                                             │  - Real-Time VRAM & Models  │
│  - Real-Time SSE Streaming  │                                             │  - Tamper-Evident Ledger    │
│  - Interactive Office Docs  │                                             │  - GraphRAG Explorer        │
└──────────────┬──────────────┘                                             └──────────────┬──────────────┘
               │                                                                           │
               └─────────────────────────────────────┬─────────────────────────────────────┘
                                                     │ HTTP / WebSocket (JWT Auth)
                                                     ▼
                              ┌───────────────────────────────────────────────┐
                              │            FASTAPI BACKEND GATEWAY            │
                              │                 (Port :8000)                  │
                              └──────────────────────┬────────────────────────┘
                                                     │
     ┌──────────────────────┬────────────────────────┼────────────────────────┬──────────────────────┐
     ▼                      ▼                        ▼                        ▼                      ▼
┌──────────────┐   ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐   ┌─────────────────┐
│ INTENT ROUTER│   │  MSDS & CHEM DB │      │ GRAPHRAG ENGINE │      │ SECURE SANDBOX  │   │ HUMAN APPROVAL  │
│  Auto-routes │   │ 16 Verified P&I │      │ Equipment Tags, │      │ Isolated Python │   │ 2-Step Sign-off │
│  Domain/Mode │   │ Toxic Limits    │      │ Hierarchy, SOPs │      │ Safe Execution  │   │ for Deliverable │
└──────┬───────┘   └────────┬────────┘      └────────┬────────┘      └────────┬────────┘   └────────┬────────┘
       └────────────────────┼────────────────────────┼────────────────────────┼─────────────────────┘
                            ▼                        ▼                        ▼
                 ┌─────────────────────────────────────────────────────────────────┐
                 │                   LOCAL OLLAMA INFERENCE DAEMON                 │
                 │                    (Air-Gapped Port :11434)                     │
                 │                                                                 │
                 │  • Reasoning & Code: deepseek-v4-pro:4b / gemma4-e4b:latest     │
                 │  • Vision & P&ID:    qwen2.5vl:3b                               │
                 │  • Offline OCR:      unlimited-ocr:latest                       │
                 └─────────────────────────────────────────────────────────────────┘
```

---

## 🌟 Key Capabilities & Architectural Innovations

### 1. 🎯 Dynamic VRAM Swapping within 6GB Budget
- Designed specifically for laptop GPUs (RTX 3050/4060 6GB).
- Sub-second dynamic model swapping via Ollama keep-alive management.
- Prevents Out-Of-Memory (OOM) crashes by unloading inactive vision models during text generation.

### 2. 🛡️ Deterministic Safety Guardrails & Zero-Hallucination Fallback
- **Chemical Safety Database (`backend/data/chemical_db.json`)**: Pre-indexed ACGIH TLV-TWA limits, PPE requirements, and medical first-aid protocols for toxic compounds (H₂S, Benzene, HF, Chlorine).
- **Exact SOP Citations**: Verbatim clause-level citations `[SOURCE: Doc_ID | Clause: X | Page: Y]`.
- **Deterministic Guardrail Fallback**: If an internal operating parameter is unindexed, the system returns a certified deterministic fallback notice rather than hallucinating dangerous estimates.

### 3. 🕸️ GraphRAG & Visual Equipment Hierarchy
- Connects refinery assets (`CDU-100` -> `P-101A` -> `ISO-10816`), interlock trip limits, and cross-standard compliance rules.
- Fully interactive visual graph canvas in the Admin Observatory.

### 4. 🖨️ Native Industrial Deliverable Generator & Canvas
- Generates verified Word (`.docx`), Excel spreadsheets (`.xlsx`), and presentation slides (`.pptx`).
- Interactive web canvas powered by Univer for direct in-browser editing before export.

### 5. 🔒 Tamper-Evident Security Ledger & 2-Step Human Verification
- SHA-256 hash chains on every log entry for audit compliance.
- 2-Step human verification workflow: High-impact actions require review and approval from qualified engineers (`PROCESS_LEAD` / `SUPER_ADMIN`).

---

## 🏗️ Technical Stack

| Layer | Technologies Used | Purpose |
| :--- | :--- | :--- |
| **Backend Core** | Python 3.10–3.12, FastAPI, Uvicorn | High-performance asynchronous API gateway |
| **LLM Inference** | Ollama, GGUF v3 Q4_K_M / Q3_K_L | 100% offline local model execution on GPU/CPU |
| **Models** | DeepSeek V4 Pro (4B), Gemma 4 (E4B), Qwen2.5-VL (3B), Unlimited-OCR | Reasoning, code generation, multimodal vision, and OCR |
| **Database** | MySQL / MariaDB (or PostgreSQL via Prisma) | Conversation history, user authentication, security audit logs |
| **Frontend UI** | Next.js 14, React 18, Tailwind CSS, TypeScript, Zustand | Operator Chat UI & Admin Observatory dashboards |
| **Document Engine** | Python-Docx, OpenPyXL, Python-PPTX, Univer Core | Air-gapped office document generation and spreadsheet canvas |
| **Security & Auth** | PBKDF2 Password Hashing, HMAC-SHA256 JWT, Air-Gap Network Guard | Strict zero-egress enforcement and role-based access control |

---

## ⚡ 6 Specialized Execution Modes

| Mode | Trigger Keyword / Intent | Action Performed |
| :--- | :--- | :--- |
| **💬 Chat** | General refinery query, definitions | Multimodal technical dialogue grounded in plant knowledge |
| **🐍 Code** | Calculations, data analysis, conversions | Sandboxed Python execution with auto-retry and output visualization |
| **📄 Docs** | Reports, SOP summaries, shift handovers | Formatted `.docx` document generation with standard corporate headers |
| **📊 Excel** | Inventory logs, production telemetry | Formatted `.xlsx` spreadsheet creation with formulas and styling |
| **📽️ PPT** | Safety briefings, executive decks | Structured `.pptx` presentation deck synthesis |
| **👁️ Vision** | P&ID diagrams, gauge images, equipment photos | Visual question answering and OCR symbol extraction |

---

## 🚀 Quickstart & Setup Guide

### Prerequisites
1. **OS**: Windows 10/11 or Ubuntu Linux
2. **GPU**: NVIDIA GPU with 6GB+ VRAM (CUDA installed) or high-end multi-core CPU
3. **Software**:
   - Python 3.10+
   - Node.js 18+ & npm
   - [Ollama](https://ollama.com) installed
   - Local Database (XAMPP MySQL or PostgreSQL)

---

### Step 1: Clone the Clean Repository
```bash
git clone https://github.com/Deepak0205p/AEGIS-AI.git
cd AEGIS-AI
```

### Step 2: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
*(Configure database credentials in `.env`. By default, it connects to local MySQL on port 3306).*

### Step 4: Initialize the Database
```bash
python scripts/init_db.py
```

### Step 5: Start Local Model Inference (Ollama)
In a dedicated terminal:
```bash
ollama serve
```
Verify or pull the required lightweight models:
```bash
ollama pull deepseek-v4-pro:4b
ollama pull gemma4-e4b:latest
ollama pull qwen2.5vl:3b
ollama pull unlimited-ocr:latest
```

### Step 6: Launch Applications
You can start all services in separate terminals or use `start_services.bat`:

1. **Backend Gateway** (Port 8000):
   ```bash
   python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```
2. **Public Chat & Canvas UI** (Port 3000):
   ```bash
   cd apps/chat-frontend
   npm install
   npm run dev
   ```
3. **Admin Observatory UI** (Port 3001):
   ```bash
   cd apps/admin-frontend
   npm install
   npm run dev
   ```

---

## 🌐 System Port & Service Map

| Service | Local URL | Description |
| :--- | :--- | :--- |
| **Chat & Canvas UI** | `http://localhost:3000` | Public operator interface with real-time SSE streaming & canvas |
| **Admin Observatory** | `http://localhost:3001` | System monitoring, GraphRAG inspector, security audit ledger |
| **Backend API Gateway** | `http://127.0.0.1:8000` | FastAPI core gateway with air-gap network guard |
| **Interactive API Docs** | `http://127.0.0.1:8000/docs` | OpenAPI / Swagger interactive documentation |
| **Ollama LLM Daemon** | `http://127.0.0.1:11434` | Air-gapped local model inference server |
| **Database** | `127.0.0.1:3306` (or `5432`) | MySQL / PostgreSQL persistent store |

---

## 🔐 Default Demo Accounts

| Role | Username | Password | Access Level |
| :--- | :--- | :--- | :--- |
| **Lead Process Operator** | `operator` | `RefineryPass2026!` | Chat, Calculations, Document Creation |
| **Maintenance Engineer** | `engineer` | `RefineryEng2026!` | Chat, Equipment Diagnostics, Verification |
| **Chief Process Lead** | `lead` | `ProcessLead2026!` | Deliverable Verification & Channel Review |
| **Super Administrator** | `admin` | `RefineryAdmin2026!` | Full Observatory Access, Security Audit Logs |

---

## 🧪 Demonstration Scenarios for SIH Evaluation

1. **Chemical Hazard Safety Query:**
   - *Query:* `"What is the permissible exposure limit for Hydrogen Sulfide and what immediate action is needed?"`
   - *Result:* Exact ACGIH TLV-TWA (1 ppm, 5 ppm STEL) injected from the verified chemical database with SCBA PPE requirements.
2. **Air-Gapped Engineering Calculation:**
   - *Query:* `"Calculate the hydrostatic pressure of 10.5 ppg drilling mud at 8500 ft TVD"`
   - *Result:* Code mode automatically writes and executes Python in the isolated sandbox, returning the exact result (`4,641 psi`).
3. **Autonomous Shift Handover Document:**
   - *Query:* `"Generate a CDU shift handover report for Night Shift"`
   - *Result:* Synthesizes a structured `.docx` document and loads it directly into the web canvas for operator sign-off.
4. **Multimodal P&ID Analysis:**
   - *Action:* Upload a piping diagram image and ask `"Identify the pressure relief valve tag and its setpoint"`.
   - *Result:* Local vision model extracts equipment tag and valve details without internet access.

---

## 📂 Repository File Structure

```
AEGIS-AI/
├── .env.example                     # Environment configuration template
├── .gitignore                       # Clean repository exclusions (zero junk)
├── README.md                        # Master SIH documentation
├── DOMAIN_COVERAGE.md               # 40+ Departmental test specifications
├── docker-compose.yml               # Container orchestration
├── package.json                     # Root scripts & workspaces
├── requirements.txt                 # Backend Python dependencies
├── run_server.py                    # Standalone backend launcher
├── start_services.bat               # 1-Click multi-service Windows launcher
│
├── apps/
│   ├── chat-frontend/               # Operator Chat & Canvas (Next.js 14)
│   └── admin-frontend/              # Admin Observatory & Telemetry (Next.js 14)
│
├── backend/                         # FastAPI Air-Gapped Core
│   ├── main.py                      # Application entrypoint & API routes
│   ├── config.py                    # Strict air-gap configuration
│   ├── chemical_kb.py               # Chemical database engine
│   ├── db.py                        # Database schema & query manager
│   ├── db_dialect.py                # PostgreSQL & MySQL compatibility layer
│   ├── graph_rag.py                 # Industrial GraphRAG implementation
│   ├── router.py                    # Multi-domain intent classifier
│   ├── sandbox.py                   # Isolated code execution sandbox
│   ├── data/
│   │   └── chemical_db.json         # 16 Verified refinery chemical MSDS records
│   └── templates.py                 # Industrial OpenXML document templates
│
├── models/
│   ├── models.yaml                  # Model configuration & VRAM budget map
│   └── gguf/                        # Modelfiles for offline Ollama builds
│
├── sample_docs/                     # Domain SOPs (Refinery, Defence, PSU)
└── scripts/                         # Verification, migration, and setup utilities
```

---

## ⚖️ License & Sovereignty Statement

Developed for **Smart India Hackathon (SIH 2026) — Problem Statement SIH26117**.  
Designed to comply with **MoPNG, OISD, and ISO 27001** data sovereignty principles. 100% of telemetry and weights remain on-premise.
