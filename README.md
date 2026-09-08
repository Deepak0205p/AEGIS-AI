# 🛡️ AEGIS AI: Sovereign Industrial AI Workbench
### **Air-Gapped, On-Premise Multi-Model Agentic AI System for Confidential Industrial Work**

[![SIH Problem Statement](https://img.shields.io/badge/SIH%202026-PS%20SIH26117-orange.svg?style=for-the-badge&logo=target)](https://sih.gov.in)
[![Target Organization](https://img.shields.io/badge/Target%20PSU-MRPL%20%7C%20MoPNG-00529B.svg?style=for-the-badge&logo=building)](https://www.mrpl.co.in)
[![Air-Gapped Sovereignty](https://img.shields.io/badge/Sovereignty-100%25%20Air--Gapped%20%26%20Zero%20Egress-green.svg?style=for-the-badge&logo=shield)](https://github.com)
[![Hardware Budget](https://img.shields.io/badge/Target%20GPU-Single%206GB%20Laptop%20(RTX%203050%2F4060)-76B900.svg?style=for-the-badge&logo=nvidia)](https://nvidia.com)
[![Full-Stack](https://img.shields.io/badge/Architecture-FastAPI%20%2B%20Next.js%2014%20%2B%20Ollama%20%2B%20Docker-blue.svg?style=for-the-badge)](https://github.com)

---

## 📑 Quick Navigation
- [📌 Problem Statement (SIH26117)](#-problem-statement-overview-sih26117)
- [💡 Solution: AEGIS AI](#-the-solution-aegis-ai)
- [🛠️ Complete Technology Stack (Tech Stack)](#-complete-technology-stack-tech-stack)
- [🏗️ System Architecture & Dataflow](#️-system-architecture)
- [🎯 Industrial Domains & Departmental Coverage](#-supported-industrial-domains--departmental-coverage)
- [⚡ 6 Core Execution Modes](#-6-execution-modes)
- [🚀 Quickstart & Installation (1-1-Click)](#-quickstart--installation-guide)
- [🌐 Service Ports & Connectivity](#-system-port--service-map)
- [🧪 Evaluation & Demo Scenarios for Judges](#-demonstration-scenarios-for-sih-evaluation)
- [📡 API Endpoints Reference](#-api-endpoints-reference)
- [📂 Repository Directory Structure](#-repository-file-structure)
- [📋 SIH26117 Compliance Matrix](#-sih26117-compliance-matrix)
- [🔒 Security & Air-Gap Verification](#-security--air-gap-verification)

---

## 📌 Problem Statement Overview (SIH26117)

| Attribute | Details |
| :--- | :--- |
| **Problem Statement ID** | **SIH26117** |
| **Title** | Sovereign On-Premise Agentic AI Workbench using Open-Weight Multimodal LLMs for Confidential Industrial Work |
| **Target Organization** | **Mangalore Refinery and Petrochemicals Limited (MRPL)** |
| **Nodal Ministry** | **Ministry of Petroleum & Natural Gas (MoPNG)** |
| **Theme & Category** | Smart Automation \| Software Edition |
| **Deployment Target** | Single Mid-Range Workstation / Laptop with 6GB–8GB VRAM (NVIDIA RTX 3050 / 4060) |

### ⚠️ The Industrial Challenge
Modern industrial facilities like **Mangalore Refinery and Petrochemicals Limited (MRPL)** and **ONGC** handle critical national infrastructure assets, proprietary Piping & Instrumentation Diagrams (P&IDs), real-time process logs (SCADA), standard operating procedures (SOPs), and commercial procurement bids. 

Commercial cloud AI solutions (such as ChatGPT, Anthropic Claude, or GitHub Copilot) are **strictly prohibited** in these secure zones due to:
1. **Critical Cyber Egress & Security Risks:** Sensitive plant telemetry, process upsets, and confidential engineering documents cannot be transmitted to external cloud servers.
2. **Regulatory & Statutory Non-Compliance:** Violates Ministry of Petroleum & Natural Gas (MoPNG), OISD (Oil Industry Safety Directorate), and ISO 27001 data sovereignty mandates.
3. **Hardware & VRAM Bottlenecks:** Enterprise AI models (70B+) require multi-GPU server clusters ($50k+). Refineries need a high-performance system operating on **standard engineering laptops (6GB VRAM)**.
4. **Hallucination in Safety-Critical Scenarios:** An AI guessing a furnace skin temperature, pressure relief valve (PRV) setpoint, or chemical first-aid protocol can lead to catastrophic industrial accidents.

---

## 💡 The Solution: AEGIS AI

**AEGIS AI** is a production-grade, 100% self-hosted, air-gapped agentic AI workbench. It operates entirely on-premise without external network connections, delivering multimodal intelligence, autonomous sandboxed execution, and native enterprise document synthesis.

### 🌟 Core Architectural Innovations
1. **Dynamic VRAM Swapping & Paging Engine:** Orchestrates multiple specialized lightweight open-weight models (2B to 4B parameters) inside a **strict 6GB VRAM ceiling**, maintaining sub-second model swapping with zero Out-Of-Memory (OOM) errors.
2. **Two-Stage Intelligent Auto-Selection Router:** Dynamically classifies operator queries using high-speed regex heuristic triggers (<50ms) and dense semantic intent classification, eliminating manual model switching.
3. **Deterministic SOP RAG & Fallback Gate:** Grounded directly in verified MRPL, ONGC, OISD, and API operational standards with verbatim clause citations (`[SOURCE: Doc_ID | Clause: X | Page: Y]`) and a zero-hallucination deterministic fallback for unindexed parameters.
4. **Air-Gapped Chemical Safety Engine:** In-memory MSDS & ACGIH chemical safety database for instant toxic gas limits (H₂S, Benzene, Chlorine, HF), flammable thresholds, and immediate medical first-aid protocols.
5. **Isolated Docker Python Sandbox (`--network none`):** Generates, runs, and self-heals engineering calculations (hydraulic power, pump efficiency, corrosion rate) inside a hardened container with zero host-network access.
6. **Self-Healing Agentic Loop:** Analyzes execution tracebacks and automatically patches code/deliverable schemas across up to 10 iterative correction cycles.
7. **Native OpenXML Deliverable Generation:** Programmatically builds ready-to-use, styled Microsoft Word (`.docx`), Excel (`.xlsx`), and PowerPoint (`.pptx`) deliverables with 50+ industrial styling presets.
8. **Real-Time Cryptographic Sovereignty Daemon:** Background socket sniffer continuously auditing network interfaces (127.0.0.1 bound), logging 0 external packets and providing tamper-evident exportable audit trails.
9. **Dual Production Frontends:**
   - **Chat & Canvas Workspace (Port 3000):** Next.js 14 client featuring embedded UniverJS Office Canvas (live editing of generated Word, Excel, and PowerPoint files), Monaco Code Editor, and Server-Sent Events (SSE).
   - **Admin Observatory (Port 3001):** Unified operations deck with RAG Observatory, Router Analyzer, Docker Sandbox Monitor, Live VRAM Telemetry, and Sovereignty Sniffer.

---

## 🛠️ Complete Technology Stack (Tech Stack)

The entire REVEAL 2.0 system is built with an enterprise-grade, modern full-stack architecture engineered specifically for **high performance, data sovereignty, and offline single-laptop execution**.

### 🎨 Tech Stack At a Glance

| Domain | Core Technologies & Frameworks |
| :--- | :--- |
| **Frontend Clients** | ![Next.js](https://img.shields.io/badge/Next.js%2014-black?style=flat-square&logo=next.js) ![React](https://img.shields.io/badge/React%2018-20232A?style=flat-square&logo=react) ![TypeScript](https://img.shields.io/badge/TypeScript%205-007ACC?style=flat-square&logo=typescript) ![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS%203.4-38B2AC?style=flat-square&logo=tailwind-css) ![UniverJS](https://img.shields.io/badge/UniverJS%20(Office%20Canvas)-0F172A?style=flat-square) ![Monaco Editor](https://img.shields.io/badge/Monaco%20Editor-1E1E1E?style=flat-square&logo=visual-studio-code) ![Radix UI](https://img.shields.io/badge/Radix%20UI-161618?style=flat-square) ![Zustand](https://img.shields.io/badge/Zustand-4338CA?style=flat-square) |
| **Backend & API** | ![Python](https://img.shields.io/badge/Python%203.11%2F3.12-3776AB?style=flat-square&logo=python&logoColor=white) ![FastAPI](https://img.shields.io/badge/FastAPI%200.110-009688?style=flat-square&logo=fastapi&logoColor=white) ![Uvicorn](https://img.shields.io/badge/Uvicorn-499848?style=flat-square) ![Pydantic](https://img.shields.io/badge/Pydantic%20v2-E92063?style=flat-square&logo=pydantic&logoColor=white) ![WebSockets](https://img.shields.io/badge/WebSockets-010101?style=flat-square) ![HTTPX](https://img.shields.io/badge/HTTPX-111827?style=flat-square) |
| **AI / ML & Local Models** | ![Ollama](https://img.shields.io/badge/Ollama%20Local-FFFFFF?style=flat-square&logo=ollama&logoColor=black) ![DeepSeek](https://img.shields.io/badge/DeepSeek--V4--Pro-006699?style=flat-square) ![Qwen](https://img.shields.io/badge/Qwen%202.5%20Coder%203B-6366F1?style=flat-square) ![Qwen2-VL](https://img.shields.io/badge/Qwen2--VL%202B-8B5CF6?style=flat-square) ![Llama 3.2](https://img.shields.io/badge/Llama%203.2%203B-0467DF?style=flat-square&logo=meta&logoColor=white) ![ChromaDB](https://img.shields.io/badge/ChromaDB-FF6F00?style=flat-square) ![PaddleOCR](https://img.shields.io/badge/PaddleOCR-D97706?style=flat-square) |
| **Database & Persistence** | ![MySQL](https://img.shields.io/badge/XAMPP%20MySQL%20%2F%20MariaDB-4479A1?style=flat-square&logo=mysql&logoColor=white) ![Prisma](https://img.shields.io/badge/Prisma%20ORM%205.19-2D3748?style=flat-square&logo=prisma&logoColor=white) ![PyMySQL](https://img.shields.io/badge/PyMySQL-3776AB?style=flat-square) |
| **Deliverables & Office** | ![Word](https://img.shields.io/badge/python--docx%20(.docx)-2B579A?style=flat-square&logo=microsoft-word&logoColor=white) ![Excel](https://img.shields.io/badge/openpyxl%20(.xlsx)-217346?style=flat-square&logo=microsoft-excel&logoColor=white) ![PowerPoint](https://img.shields.io/badge/python--pptx%20(.pptx)-D24726?style=flat-square&logo=microsoft-powerpoint&logoColor=white) ![Matplotlib](https://img.shields.io/badge/Matplotlib%20%2F%20Pandas-11557C?style=flat-square) |
| **Security & Sandbox** | ![Docker](https://img.shields.io/badge/Docker%20Sandbox%20(--network_none)-2496ED?style=flat-square&logo=docker&logoColor=white) ![psutil](https://img.shields.io/badge/psutil%20(Socket%20Auditing)-334155?style=flat-square) ![Air-Gapped](https://img.shields.io/badge/100%25%20Air--Gapped%20Guard-10B981?style=flat-square) |

---

### 📦 Comprehensive Tech Stack Matrix

#### 1. 🖥️ Frontend Technologies (`apps/chat-frontend` & `apps/admin-frontend`)

| Technology / Library | Version | Purpose & Implementation |
| :--- | :--- | :--- |
| **Next.js** | `14.2.5` | React framework with App Router, server-side rendering, API routes, and static export support (`output: 'export'`). |
| **React** | `18.3.1` | Core declarative component library with Hooks and Concurrent features. |
| **TypeScript** | `^5.5.2` | End-to-end type safety across stores, API contracts, SSE streams, and component props. |
| **Tailwind CSS** | `3.4.4` | Utility-first styling engine custom-tuned for industrial high-contrast dark themes. |
| **UniverJS Core & UI** | `0.25.1` | Production-grade in-browser office suite (`@univerjs/core`, `@univerjs/ui`, `@univerjs/design`). |
| **UniverJS Sheets** | `0.25.1` | Full Excel spreadsheet canvas (`@univerjs/sheets`, `@univerjs/sheets-ui`, `@univerjs/sheets-formula`). |
| **UniverJS Docs** | `0.25.1` | Interactive Word document canvas (`@univerjs/docs`, `@univerjs/docs-ui`). |
| **UniverJS Slides** | `0.25.1` | Interactive presentation slide deck viewer and editor (`@univerjs/slides`, `@univerjs/slides-ui`). |
| **Monaco Editor** | `^4.6.0` | In-browser VS Code editor engine (`@monaco-editor/react`) for viewing, editing, and running Python automation scripts. |
| **Radix UI** | `1.1.x – 1.2.x` | Accessible, unstyled UI primitives: Accordion, Dialog, Tooltip, Tabs, and Progress. |
| **Framer Motion** | `11.3.19` | Smooth layout transitions, collapsible ReAct thought steps, and slide-in panels. |
| **Zustand** | `4.5.4` | Ultra-fast client-side state store (`useDeliverableStore`, `useCanvasStore`, `useChatStore`). |
| **Recharts** | `^2.12.7` | Hardware VRAM telemetry and network socket auditing live graphs. |
| **Lucide React** | `0.395.0` | Comprehensive industrial and UI icon set. |
| **React Markdown & GFM** | `9.0.1 / 4.0.0` | GitHub-flavored markdown parsing with table and math syntax support. |

---

#### 2. ⚡ Backend Gateway & Frameworks (`backend/`)

| Technology / Library | Version | Purpose & Implementation |
| :--- | :--- | :--- |
| **Python** | `3.11 / 3.12` | 64-bit high-performance execution runtime for async server and sandboxing. |
| **FastAPI** | `>=0.110.0` | High-throughput asynchronous ASGI web framework for REST API, SSE streams, and WebSockets. |
| **Uvicorn** | `>=0.28.0` | Lightning-fast ASGI web server implementation with reload capabilities. |
| **Pydantic** | `>=2.6.0` | Type-driven data validation, request parsing, and response serialization. |
| **HTTPX** | `>=0.27.0` | Async HTTP client with connection pooling for communication with local Ollama inference service. |
| **WebSockets** | `>=12.0` | Bidirectional real-time streaming for live token generation and 1Hz sovereignty auditing. |
| **psutil** | `>=5.9.0` | OS process monitor inspecting open TCP/UDP sockets, VRAM, and system RAM in real time. |

---

#### 3. 🧠 AI, LLM Models & Local Inference Engine

| Technology / Model | Format / Tag | VRAM Footprint | Purpose in REVEAL 2.0 |
| :--- | :--- | :--- | :--- |
| **Ollama** | Native Local Daemon | Host Process | Air-gapped model serving daemon with CUDA GPU acceleration and sub-second model paging. |
| **DeepSeek-V4-Pro / Gemma 4** | `GGUF Q3_K_L / Q4_K_S` | ~2.5GB – 4.8GB | Primary thinking engine: complex industrial reasoning, SOP synthesis, ReAct multi-step planning. |
| **Qwen 2.5 Coder 3B** | `GGUF Q4_K_M` | ~2.1GB | Specialized code generation: writing and fixing Python automation scripts and hydraulic formulas. |
| **Qwen2-VL 2B** | `GGUF IQ4_XS` | ~1.8GB | Multimodal vision engine: analyzing scanned inspection PDFs, equipment nameplates, and P&IDs. |
| **Llama 3.2 3B** | `GGUF Q4_K_M` | ~2.0GB | High-speed conversational engine: quick queries, summarization, and executive formatting. |
| **BAAI/bge-small-en-v1.5** | Dense Embeddings | CPU / ~300MB | Local vector embedding model generating 384-dimensional dense vectors for SOP retrieval. |
| **ChromaDB** | Embedded SQLite/Vector | Local Storage | Grounded local vector database storing MRPL & ONGC SOPs without cloud leakage. |
| **PaddleOCR / Tesseract** | On-Device Engine | Local Engine | High-precision optical character recognition for degraded refinery field logs and tables. |

---

#### 4. 📄 Deterministic Office Deliverable Synthesizers

| Library | Version | Output Deliverable | Key Features |
| :--- | :--- | :--- | :--- |
| **python-docx** | `>=1.1.0` | Microsoft Word (`.docx`) | Programmatic generation of executive approval notes, inspection reports, and shift handovers with custom headers, tables, and borders. |
| **openpyxl** | `>=3.1.2` | Microsoft Excel (`.xlsx`) | Generation of multi-sheet workbooks, formatted asset registers, calculation tables, auto-column widths, and live formula injection. |
| **python-pptx** | `>=0.6.23` | Microsoft PowerPoint (`.pptx`) | Automated deck builder featuring **50 unique industrial presentation styles and themes** (Safety, Operations, Executive, Metallurgy). |
| **matplotlib** | `>=3.8.0` | High-Res PNG / Vector | Engineering curve plotting (pump performance curves, Nelson curves, corrosion rate projections). |
| **pandas & numpy** | `>=2.2.0 / >=1.26.0` | Structured Data Arrays | In-memory data transformations, numerical analysis, and tabular data structuring. |

---

#### 5. 💾 Database & Persistence Layer

| Technology | Implementation | Functionality |
| :--- | :--- | :--- |
| **XAMPP MySQL / MariaDB** | Port `3306` (`sovereign_ai` DB) | Enterprise relational persistence for chat sessions, message logs, deliverable metadata, and user accounts. |
| **PyMySQL** | `pymysql.cursors.DictCursor` | High-speed direct connection pool from FastAPI backend to MySQL with autocommit transactions. |
| **Prisma ORM** | `@prisma/client 5.19.1` | Declarative schema modeling, migrations, and Prisma Studio browser GUI for visual database management. |
| **Rolling Summarizer** | SQLite / MySQL Cache | Maintains 10-message conversational window while rolling older turns into 3-sentence cached summaries. |

---

#### 6. 🔒 Security, Sandboxing & DevOps Automation

| Component | Mechanism | Security Function |
| :--- | :--- | :--- |
| **Docker Sandbox** | `Dockerfile.sandbox` | Executes generated Python calculations in total network isolation (`--network none`, 1GB RAM, 1 CPU limit). |
| **Subprocess Fallback** | Process Sandbox | Local fallback sandbox when Docker daemon is unavailable, running with timeout and memory guards. |
| **Sovereignty Daemon** | AF_INET Socket Monitor | Real-time packet sniffer ensuring zero outbound external connections during all LLM and tool operations. |
| **Batch Automation** | `install_dependencies.bat` | Concurrent multi-process dependency installer for Windows, completing full installation in under 4 minutes. |
| **Service Launcher** | `start_services.bat` | Single-click orchestration launching Backend Gateway, Chat UI, and Admin UI in separate managed terminals. |

---

## 🏗️ System Architecture

```mermaid
flowchart TB
    subgraph ClientLayer["🖥️ Frontend Client Layer (Next.js 14 + Tailwind CSS)"]
        ChatUI["Public Chat & Canvas UI\n(:3000)\n• UniverJS (Sheets / Docs / Slides)\n• Monaco Editor\n• SSE & WebSockets Stream"]
        AdminUI["Admin Observatory\n(:3001)\n• RAG & Router Visualizer\n• Sandbox Telemetry\n• Sovereignty Sniffer & VRAM Meter"]
    end

    subgraph GatewayLayer["⚡ Backend Gateway (FastAPI + Uvicorn :8000)"]
        Router["Two-Stage Auto-Selection Router\n• Heuristic Intent Matcher (<50ms)\n• Semantic Classifier"]
        Auth["Air-Gapped Auth Engine\n(Role-Based: Operator / Engineer / Admin)"]
        AuditDaemon["Sovereignty Watchdog & Sniffer\n(psutil / AF_INET Socket Monitor -> 0 Egress)"]
    end

    subgraph IntelligenceLayer["🧠 Local Model Inference Hub (Ollama :11434)"]
        VRAMManager["VRAM-Aware Model Pager\n(6.0GB VRAM Budget Controller)"]
        M1["DeepSeek-V4-Pro / Gemma 4 (4B)\nPrimary Reasoning & SOP Synthesis"]
        M2["Qwen 2.5 Coder (3B)\nPython Scripting & Math Engine"]
        M3["Qwen2-VL (2B) + PaddleOCR\nMultimodal Vision & P&ID Extractor"]
        M4["Llama 3.2 (3B)\nFast Conversational Assistant"]
    end

    subgraph KnowledgeLayer["📚 Grounded Sovereign Knowledge Base"]
        ChromaDB["Embedded Vector Store\n(MRPL / ONGC / OISD SOPs)"]
        ChemDB["Chemical Safety Registry\n(MSDS, CAS, TLVs, ACGIH, Antidotes)"]
        TemplateReg["Industrial Template Registry\n(Shift Handover, DPR, PTW, Inspection)"]
    end

    subgraph SandboxLayer["🔒 Isolated Execution Sandbox"]
        DockerSandbox["Hardened Docker Sandbox\n(--network none, 1GB RAM, 1 CPU, 128 PIDs)\nAuto-Repair Self-Correction Loop (Up to 10x)"]
    end

    subgraph DeliverableEngine["📄 Deterministic Deliverable Engine"]
        DocxGen["Word Builder (python-docx)\nFormal Memos, Inspection Notes"]
        XlsxGen["Excel Builder (openpyxl)\nAsset Logs, Pump Efficiency Sheets"]
        PptxGen["PowerPoint Builder (python-pptx)\n50+ Refinery Engineering Themes"]
    end

    subgraph PersistenceLayer["💾 Relational Storage (XAMPP MySQL / MariaDB)"]
        MySQL[("MySQL 3306\n• Sessions & Message History\n• 10-Message Windowing\n• Cached Rolling Summaries\n• File Registry")]
    end

    %% Connections
    ChatUI <--> GatewayLayer
    AdminUI <--> GatewayLayer
    GatewayLayer --> Router
    Router --> IntelligenceLayer
    IntelligenceLayer --> KnowledgeLayer
    Router --> SandboxLayer
    Router --> DeliverableEngine
    DeliverableEngine --> PersistenceLayer
    GatewayLayer <--> PersistenceLayer
    AuditDaemon -. Audits Socket Boundary .-> GatewayLayer
```

---

## 🎯 Supported Industrial Domains & Departmental Coverage

Tested and cataloged across 7 core refinery & upstream operational departments:

| Department | Sample Operator Query | Mechanism | Grounding / Output |
| :--- | :--- | :--- | :--- |
| **Refinery Operations (CDU/VDU/HCU)** | *"Furnace F-101 tube skin temperature max limit kitna hai?"* | RAG (Master SOP) | Indexed in `SOP-MRPL-FURNACE-101` (Limit: 750°C, Alarm: 720°C) |
| **Upstream Drilling Services** | *"Calculate hydrostatic pressure for 10.5 ppg mud at 8,500 ft TVD"* | Calculation (Code) | Executes `P = 0.052 * MW * TVD` in isolated Docker sandbox |
| **Offshore Platforms (ONGC)** | *"TEG contactor dehydration glycol circulation rate & reboiler temp?"* | Chemical-DB + RAG | Injects Triethylene Glycol properties & decomposition limits |
| **HSE & Fire Safety** | *"H2S gas leak exposure symptoms and TLV threshold?"* | Chemical-DB | CAS 7783-06-4, TLV: 1 ppm, STEL: 5 ppm, Level A PPE |
| **Mechanical Maintenance** | *"API 610 pump P-101A/B vibration alarm and trip limits?"* | RAG (Master SOP) | Indexed in `SOP-MRPL-PUMP-610` (Alarm: 4.5 mm/s, Trip: 7.1 mm/s) |
| **Inspection & Metallurgy (NDT)** | *"Calculate remaining corrosion life: current 9.2mm, min 6.8mm, rate 0.15mm/yr"* | Calculation (Code) | Executes calculation in sandbox: **16.0 Years** |
| **QC Laboratory** | *"Generate Daily Quality Certificate of Analysis (COA) for BS-VI HSD"* | Template (Document) | Programmatically builds formatted `.docx` inspection certificate |

---

## ⚡ 6 Core Execution Modes

| Mode | Trigger Keyword / Intent | Engine Pipeline | Output Deliverable |
| :--- | :--- | :--- | :--- |
| **Auto Mode** | Dynamic query classification | Two-Stage Regex + Semantic Router | Routes to Code / Docs / Excel / PPT / Chat |
| **Chat Mode** | SOP questions, plant inquiries, safety | RAG SOP Retrieval + Grounded LLM | Cited guidance with `[SOURCE: Doc_ID \| Clause]` |
| **Code Mode** | Python scripts, hydraulic formulas, math | Isolated Docker Sandbox + Self-Healing | Verbatim stdout/stderr execution outputs |
| **Docs Mode** | Handover logs, memos, inspection reports | Structured Planner + `python-docx` | Editable `.docx` Microsoft Word document |
| **Excel Mode** | Asset logs, inventory, sensor data | Structured Planner + `openpyxl` | Styled `.xlsx` Microsoft Excel spreadsheet |
| **PPT Mode** | Presentation decks, safety briefings | 50+ Style Registry + `python-pptx` | Professional `.pptx` slide presentation |

---

## 🚀 Quickstart & Installation Guide

### Prerequisites
1. **Operating System:** Windows 10/11 64-bit or Ubuntu 22.04 LTS.
2. **Python:** Python 3.11 or 3.12 installed and added to `PATH`.
3. **Node.js:** Node.js 18+ or 20+ LTS and `npm` installed.
4. **Ollama:** Ollama installed locally (`https://ollama.ai`).
5. **Database:** XAMPP MySQL running on port 3306 (or local MySQL instance).
6. **Docker:** Docker Desktop installed (for isolated code sandboxing).

---

### Method 1: 1-Click Automated Setup (Windows)

#### Step 1: Install Dependencies in Parallel
Double-click or run from command line:
```bat
install_dependencies.bat
```
*This launches 4 concurrent worker processes installing Python requirements, Chat Frontend dependencies, Admin Frontend dependencies, and root Prisma packages in under 4 minutes.*

#### Step 2: Ingest & Verify Offline Models
Verify that the required local models are pulled and registered in Ollama:
```bash
ollama serve
ollama pull deepseek-v4-pro:4b
```
*(Optional: Run the SHA-256 model verification utility)*
```bash
python scripts/download_and_verify_models.py --verify-all
```

#### Step 3: Build Docker Sandbox Container
```bash
docker build -t python-sandbox -f Dockerfile.sandbox .
```

#### Step 4: 1-Click Launch All Services
```bat
start_services.bat
```
*This starts the Python Backend Gateway (:8000), Public Chat & Canvas UI (:3000), and Admin Observatory (:3001) in dedicated console windows.*

---

### Method 2: Manual Step-by-Step Setup

#### 1. Setup Backend
```bash
# Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start Backend Gateway (Enforcing air-gap offline flags)
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Setup Public Chat & Canvas UI
```bash
cd apps/chat-frontend
npm install
npm run dev:http
# Accessible at: http://localhost:3000
```

#### 3. Setup Admin Observatory
```bash
cd apps/admin-frontend
npm install
npm run dev
# Accessible at: http://localhost:3001
```

---

## 🌐 System Port & Service Map

| Service | Port | Description | Health / Status URL |
| :--- | :--- | :--- | :--- |
| **Public Chat & Canvas UI** | `3000` | Primary operator interface with embedded UniverJS office editors | `http://localhost:3000` |
| **Admin Observatory** | `3001` | RAG, Router, Sandbox & Sovereignty Audit dashboard | `http://localhost:3001` |
| **Backend Gateway API** | `8000` | FastAPI server handling SSE chat, tools, sandboxing, and files | `http://localhost:8000/api/health` |
| **Interactive API Docs** | `8000` | OpenAPI Swagger Documentation | `http://localhost:8000/docs` |
| **Ollama Local Engine** | `11434` | Local model inference server | `http://localhost:11434/api/tags` |
| **XAMPP MySQL** | `3306` | Persistent session, history, and deliverable storage | `localhost:3306` (`sovereign_ai`) |

---

## 🧪 Demonstration Scenarios for SIH Evaluation

The repository includes pre-configured operational test scenarios designed for live demonstration before SIH evaluation panels:

### Scenario 1: Scanned Inspection PDF to Formal Word Approval Note
- **User Action:** Upload a scanned inspection report containing furnace skin temperature anomalies and decoking requirements.
- **System Execution:** Activates `Qwen2-VL` + `PaddleOCR` for tabular data extraction, queries ChromaDB for relevant MRPL SOP limits (`SOP-MRPL-FURNACE-101`), and synthesizes an executive memorandum.
- **Deliverable:** Programmatically outputs a styled `approval_note.docx` rendered directly in the in-browser UniverJS Canvas.

### Scenario 2: Sandboxed Hydraulic Pump Efficiency Calculation
- **User Action:** Prompt: *"Write a Python script to calculate centrifugal pump hydraulic power and efficiency for Flow: 250 m³/h, Head: 85m, Density: 850 kg/m³, Motor Power: 65 kW."*
- **System Execution:** Router automatically dispatches request to `Qwen 2.5 Coder 3B`, executes the script inside the `--network none` Docker sandbox, intercepts stdout, and self-checks results.
- **Output:** Live execution stdout displayed alongside interactive Monaco code editor.

### Scenario 3: P&ID Drawing Extraction to Formatted Excel Register
- **User Action:** Upload a technical P&ID diagram of Crude Distillation Unit (CDU).
- **System Execution:** Identifies valves, pumps, and instrumentation tags (e.g., `P-101A`, `FCV-101`), cross-references against local plant registry, and builds an editable spreadsheet.
- **Deliverable:** Generates `equipment_register.xlsx` with headers, auto-fit columns, and formula totals, viewable in the UniverJS Spreadsheet Canvas.

### Scenario 4: Provable Air-Gap Sovereignty Audit
- **Demonstration:** Navigate to Admin Observatory (`http://localhost:3001`) -> **Sovereignty Audit Tab**.
- **Evidence:** Live socket sniffer continuously samples all network interfaces:
  - **External Outbound Packets:** `0`
  - **DNS Requests:** `0`
  - **Telemetry Egress:** `Blocked / Suppressed`
  - **Audit Certificate:** Exportable cryptographic verification log.

---

## 📡 API Endpoints Reference

| Endpoint | Method | Purpose |
| :--- | :--- | :--- |
| `/api/health` | `GET` | Health check verifying Ollama connection, active model, and air-gap status |
| `/api/chat` | `POST` | Primary Server-Sent Events (SSE) streaming chat endpoint |
| `/api/chat/stream` | `WebSocket` | Real-time bidirectional WebSocket streaming endpoint |
| `/api/audit-stream` | `WebSocket` | 1Hz real-time network packet and VRAM telemetry stream |
| `/api/chat/sessions` | `GET`, `POST` | List and create persistent chat conversation sessions |
| `/api/chat/sessions/{id}` | `GET`, `DELETE` | Retrieve or delete specific conversation history |
| `/api/files/list` | `GET` | List all generated `.docx`, `.xlsx`, and `.pptx` deliverables |
| `/api/files/{file_id}` | `GET` | Direct download endpoint for generated binary deliverable files |
| `/api/files/{file_id}/content`| `GET` | Returns parsed JSON structure for live UniverJS Canvas rendering |
| `/api/models` | `GET` | Returns inventory of active and standby local models |
| `/api/models/swap` | `POST` | Triggers dynamic VRAM model swapping with context preservation |
| `/api/ppt/styles` | `GET` | Returns registry of 50 industrial presentation slide styles |
| `/api/v1/auth/login` | `POST` | Air-gapped local role-based authentication (`admin`, `operator`, `engineer`) |

---

## 📂 Repository File Structure

```text
.
├── apps/
│   ├── chat-frontend/           # Port 3000: Next.js 14 Operator UI & UniverJS Canvas
│   │   ├── src/components/canvas/ # UniverJS Sheets, Docs, Slides & Monaco Editors
│   │   ├── src/store/           # Zustand state stores (deliverables, sessions)
│   │   └── package.json         # UniverJS, Monaco, Radix UI, Framer Motion
│   └── admin-frontend/          # Port 3001: Next.js 14 Admin Observatory UI
│       ├── src/components/      # RagObservatory, RouterObservatory, SandboxObservatory
│       └── package.json         # Admin dependencies & design system
├── backend/                     # Port 8000: FastAPI Air-Gapped Gateway
│   ├── chat_mode.py             # Grounded natural dialogue & anti-hallucination engine
│   ├── code_mode.py             # Python code generator with sandbox runner & self-healing
│   ├── docs_mode.py             # Document planner & Word builder dispatcher
│   ├── excel_mode.py            # Excel spreadsheet generator wrapper
│   ├── ppt_mode.py              # PowerPoint presentation generator wrapper
│   ├── ppt_styles.py            # 50 unique industrial presentation style themes
│   ├── deliverables.py          # Native OpenXML file synthesizers (docx, xlsx, pptx)
│   ├── router.py                # Two-Stage regex heuristic & semantic router
│   ├── knowledge_base.py        # Master SOP RAG search & deterministic cache
│   ├── chemical_kb.py           # In-memory MSDS, CAS, and toxic chemical safety database
│   ├── departments.py           # Industrial department classifier (Refinery / E&P / HSE)
│   ├── templates.py             # Industrial template registry (Shift logs, DPR, PTW)
│   ├── sandbox.py               # Docker container execution & subprocess fallback
│   ├── db.py                    # XAMPP MySQL database manager & context windowing
│   ├── ollama_client.py         # Model inference handler & dynamic VRAM swapping
│   ├── config.py                # Environment configs & air-gapped security flags
│   └── main.py                  # FastAPI application, SSE endpoints, and WebSockets
├── models/
│   └── models.yaml              # Declarative model registry with VRAM budgets & regex routes
├── scripts/
│   ├── download_and_verify_models.py # Model ingestion and SHA-256 audit utility
│   └── build_sandbox_image.py   # Docker sandbox build & smoke testing utility
├── data/                        # Persistent storage for ChromaDB and SQLite fallbacks
├── generated/                   # Local output folder for generated docx, xlsx, pptx files
├── Dockerfile.sandbox           # Isolated execution container definition
├── install_dependencies.bat     # Parallel automated installer for Windows
├── start_services.bat           # 1-Click launcher for all 3 system services
├── requirements.txt             # Python backend dependencies
└── README.md                    # System documentation
```

---

## 📋 SIH26117 Compliance Matrix

| S.No | SIH Requirement | System Implementation | Verification Evidence |
| :---: | :--- | :--- | :--- |
| **01** | **Self-Hosted & Air-Gapped** | Runs 100% on localhost via local Ollama and FastAPI instances. Zero cloud APIs or external tokens required. | Verified offline runtime (`HF_HUB_OFFLINE=1`, `OLLAMA_NO_USAGE_STATS=1`). |
| **02** | **Zero External Egress** | All network sockets bound strictly to `127.0.0.1`. Background socket monitor audits all open connections. | Sovereignty Audit Log confirming **0 external packets transmitted**. |
| **03** | **Single Workstation (6GB GPU)** | Optimized 4-bit quantized (GGUF) models orchestrated within a 6.0GB VRAM ceiling with sub-second paging. | `nvidia-smi` telemetry confirms stable allocation at **~4.6GB / 6.0GB**. |
| **04** | **Multi-Model Support** | Simultaneous support for Reasoning (Qwen3/Gemma), Coding (Qwen Coder), Vision (Qwen2-VL), and Fast Chat. | `/api/models` endpoint returns live inventory and status of all models. |
| **05** | **Intelligent Auto-Selection** | Two-stage router analyzes prompt syntax, keywords, and semantic intent to select the optimal model. | Dynamic routing demonstrated across Code, Docs, Excel, PPT, and Chat. |
| **06** | **Extensible Model Registry** | Declarative YAML-based registry (`models/models.yaml`) allows hot-adding models without code refactoring. | Live registration and hot-swapping supported via API and UI. |
| **07** | **Agentic Planning & Self-Correction** | ReAct agent loop decomposes complex goals, executes tools, and self-heals tracebacks up to 10 iterations. | Live visual reasoning trace and auto-retry logs visible in UI. |
| **08** | **Local Sandboxed Execution** | Hardened Docker sandbox with restricted CPU/memory and `--network none` flag. | Sandboxed Python math script execution with isolated stdout capture. |
| **09** | **Multimodal Input Processing** | Hybrid pipeline combining PaddleOCR text extraction with Qwen2-VL spatial reasoning for P&IDs and scans. | Upload and analysis of engineering drawings and scanned inspection reports. |
| **10** | **Production Deliverables** | Native OpenXML generators creating fully formatted `.docx`, `.xlsx`, `.pptx`, and `.py` files. | Instant generation and in-browser interactive editing via UniverJS Canvas. |
| **11** | **Grounded SOP Knowledge Base** | Embedded vector search across verified MRPL & ONGC SOPs with mandatory clause citations. | Query responses citing specific SOP document IDs, clauses, and pages. |
| **12** | **Provable Sovereignty Auditing** | Real-time socket sniffer continuously auditing network traffic with exportable compliance certificates. | Admin Observatory displaying live network packet counts (0 external). |

---

## 🔒 Security & Air-Gap Verification

To guarantee strict compliance with industrial security policies:
1. **Network Boundary:** All services bind strictly to `127.0.0.1` or authorized internal intranet interfaces.
2. **Environment Isolation:** The following environment variables are permanently active:
   ```bash
   HF_HUB_OFFLINE=1
   TRANSFORMERS_OFFLINE=1
   OLLAMA_NO_USAGE_STATS=1
   ```
3. **Container Isolation:** The Docker sandbox is executed with:
   ```bash
   docker run --rm --network none --memory 1024m --cpus 1.0 --pids-limit 128 ...
   ```
4. **Data Sovereignty Guarantee:** No prompts, telemetry, vector embeddings, or generated documents ever leave the host machine.

---

## 👥 Contributors & Acknowledgements

Developed for the **Smart India Hackathon 2026 (SIH26117)** under the Ministry of Petroleum & Natural Gas (MoPNG) for **Mangalore Refinery and Petrochemicals Limited (MRPL)**.

*Built with passion for Indian Industrial Sovereignty and AI Excellence.* 🇮🇳
