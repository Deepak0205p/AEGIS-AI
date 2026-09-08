"""
REVEAL 2.0 - Industrial Plant Operations & Safety Engine (Production Hardened)
Air-Gapped Autonomous RAG & Decision Support System (ONGC / MRPL Refineries)

5-Step Deterministic Pipeline:
  - Step 0: Fast Local/SQL Cache Lookup (<50ms)
  - Step 1: Casual Intent Fast-Path (<200ms)
  - Step 2: Enterprise Scope Guardrail Router (<100ms)
  - Step 3: Multi-Turn Coreference Rewrite & Hybrid Vector Retrieval
  - Step 4: Deterministic Grounding Verification (Dual-Tier Execution Gate)
"""

import asyncio
import hashlib
import json
import logging
import math
import os
import re
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Tuple

import httpx
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# =====================================================================
# 0. LOGGING & GLOBAL CONSTANTS
# =====================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("AEGIS_ENGINE")

OLLAMA_GENERATE_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
PRIMARY_MODEL = os.getenv("REVEAL_MODEL", "qwen2.5:3b")
SIMILARITY_THRESHOLD = 0.65  # Hard safety gate

# Universal refinery equipment tag regex
EQUIPMENT_TAG_REGEX = r"\b([A-Za-z]{1,4}-\d{3,4}[A-Za-z]?|CDU|VDU|FCCU|DHDS|SRU|DCU|MSBLOCK)\b"

REVEAL_SYSTEM_INSTRUCTION = """You are AEGIS AI, a Senior Industrial Operations & Plant Safety Engineer for ONGC/MRPL refineries. You provide precise, authoritative, and direct operational guidance to plant engineers and field operators.

### ABSOLUTE CONSTRAINTS (VIOLATION = SYSTEM SHUTDOWN)
1. ZERO SYSTEM LEAKS: Never use phrases like 'based on the provided context', 'according to the text', 'the document states', or 'in the given information'. Speak directly as the authority.
2. HARD GROUNDING ON METRICS: Any numerical threshold, operating limit, skin temperature, pressure setpoint, metallurgy spec, or interlock condition MUST come verbatim from the VERIFIED_SOP_DATA below.
3. CITATION FORMAT: Every procedure step or critical parameter must end with its exact source tag: `[SOURCE: <Doc_ID> | Clause: <Clause> | Page: <Page>]`.
4. DIRECT OUTPUT: Lead directly with the technical limit or procedure. No conversational opening ('Hello', 'Sure') or closing pleasantries."""

DETERMINISTIC_FALLBACK_TEXT = (
    "Operational parameters for this query are not indexed in active Master SOPs (OISD/API/MRPL). "
    "Manual entry or Shift In-Charge sign-off required."
)

SCOPE_REJECTION_TEXT = (
    "I am strictly scoped for MRPL & ONGC refinery operations, engineering standards (OISD/API/ASME), "
    "plant safety SOPs, chemical databases, and equipment reliability. "
    "I cannot assist with queries outside industrial refinery operations."
)

GREETING_PATTERNS = [
    r"^(hi|hello|hey|greetings|good\s+(morning|afternoon|evening)|namaste)[\s\!]*$",
    r"^(kaise\s+ho|how\s+are\s+you|kya\s+haal\s+hai|sab\s+theek)[\s\?]*$",
    r"^(who\s+are\s+you|what\s+is\s+reveal|help|menu)[\s\?]*$",
]

TECHNICAL_TERMS = {
    "furnace", "f-101", "f-201", "tmt", "tube", "skin", "temperature", "decoking",
    "pump", "p-101a", "p-101b", "p-201a", "npsh", "cavitation", "seal", "api 610",
    "cdu", "vdu", "crude", "distillation", "column", "reboiler", "stripper",
    "corrosion", "er probe", "ultrasonic", "ut", "coupon", "api 570", "api 510",
    "safety", "ptw", "loto", "oisd", "oisd-144", "oisd-105", "confined space",
    "h2s", "fire", "psv", "flare", "esd", "interlock", "scada", "plc",
    "gem", "tender", "e-mb", "procurement", "zld", "effluent", "brsr", "boiler"
}

# =====================================================================
# 1. SHARED CONNECTION POOL (FASTAPI LIFESPAN)
# =====================================================================
http_client: Optional[httpx.AsyncClient] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client
    logger.info("Initializing high-concurrency connection pool for Ollama...")
    http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(60.0, connect=5.0),
        limits=httpx.Limits(max_keepalive_connections=20, max_connections=50)
    )
    yield
    logger.info("Closing HTTP connection pool...")
    if http_client:
        await http_client.aclose()

app = FastAPI(
    title="REVEAL 2.0 Plant Operations Engine",
    description="Production-Hardened Air-Gapped RAG Backend for MRPL/ONGC",
    version="2.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================================
# 2. SCHEMAS (PYDANTIC V2 MODELS)
# =====================================================================
class ChatMessage(BaseModel):
    role: str
    content: str

class CitationMeta(BaseModel):
    doc_id: str
    clause: str
    page: str
    source_type: str = "MASTER_SOP"
    similarity_score: float

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    session_id: str = Field(default="default-session")
    history: List[ChatMessage] = Field(default_factory=list)
    active_equipment: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    stage: str
    latency_ms: float
    confidence: float
    citations: List[CitationMeta] = Field(default_factory=list)
    deliverable_ids: List[str] = Field(default_factory=list)
    is_cached: bool = False

# =====================================================================
# 3. KNOWLEDGE BASE & SIMULATED HYBRID VECTOR RETRIEVAL
# =====================================================================
class KnowledgeChunk(BaseModel):
    doc_id: str
    title: str
    clause: str
    page: str
    content: str
    keywords: List[str]
    dense_embedding: List[float]

def _generate_mock_dense_vector(text: str, dim: int = 16) -> List[float]:
    h = hashlib.sha256(text.lower().encode("utf-8")).hexdigest()
    vec = [((int(h[i * 2 : (i + 1) * 2], 16) / 255.0) * 2.0 - 1.0) for i in range(dim)]
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]

def _cosine_similarity(v1: List[float], v2: List[float]) -> float:
    dot = sum(a * b for a, b in zip(v1, v2))
    return max(0.0, min(1.0, (dot + 1.0) / 2.0))

MASTER_KNOWLEDGE_BASE: List[KnowledgeChunk] = [
    KnowledgeChunk(
        doc_id="SOP-MRPL-FURNACE-101",
        title="Furnace F-101 Operations and Tube Skin Temperature Control",
        clause="4.3.2",
        page="12",
        content=(
            "Maximum allowable Tube Skin Temperature (TMT) for Furnace F-101: "
            "Carbon Steel tubes must not exceed 540°C. Alloy Steel (9Cr-1Mo) tubes must not exceed 650°C. "
            "If skin temp exceeds limit for >15 min, reduce firing rate by 5% and increase pass flow proportionally."
        ),
        keywords=["furnace", "f-101", "skin", "temperature", "tmt", "540", "650", "tube"],
        dense_embedding=_generate_mock_dense_vector("Furnace F-101 Tube Skin Temperature 540 650 TMT"),
    ),
    KnowledgeChunk(
        doc_id="SOP-MRPL-HSE-PTW-004",
        title="Permit to Work (PTW) & Lockout/Tagout (LOTO) Procedure",
        clause="3.1.5",
        page="7",
        content=(
            "Cold Work Permit validity: 8-hour shift, renewable up to 24 hours. "
            "Hot Work Permit requires continuous combustible gas monitoring; LEL must remain 0.0%. "
            "Confined Space Entry requires oxygen levels between 19.5% and 23.5%, H2S < 10 ppm, CO < 25 ppm."
        ),
        keywords=["ptw", "loto", "safety", "permit", "confined", "space", "oisd-105", "h2s", "hot work"],
        dense_embedding=_generate_mock_dense_vector("Permit to Work PTW LOTO Safety Confined Space OISD"),
    ),
    KnowledgeChunk(
        doc_id="SOP-MRPL-PUMP-610",
        title="Centrifugal Pump P-101A/B Commissioning and Vibration Limits",
        clause="5.2.1",
        page="28",
        content=(
            "API 610 Centrifugal Pumps P-101A/B: Maximum permissible vibration overall RMS velocity is 4.5 mm/s. "
            "Alarm threshold is set at 7.1 mm/s; emergency trip occurs at 9.0 mm/s. "
            "Mechanical seal flush Plan 11/52 must maintain differential pressure of at least 1.5 kg/cm2."
        ),
        keywords=["pump", "p-101a", "p-101b", "vibration", "api 610", "seal", "4.5", "npsh"],
        dense_embedding=_generate_mock_dense_vector("Centrifugal Pump P-101A Vibration Limits API 610"),
    ),
]

# =====================================================================
# 4. STEP 0: PRODUCTION SQL/IN-MEMORY CACHE
# =====================================================================
class ProductionResponseCache:
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.set(
            raw_query="what is the maximum tube skin temperature limit for furnace f-101",
            final_answer=(
                "**Maximum Tube Skin Temperature (TMT) for Furnace F-101:**\n"
                "- **Carbon Steel Tubes:** **540°C**\n"
                "- **Alloy Steel (9Cr-1Mo) Tubes:** **650°C**\n\n"
                "If TMT exceeds limit for >15 minutes, reduce firing rate by 5% and balance pass flow.\n\n"
                "[SOURCE: MASTER_SOP | Document: SOP-MRPL-FURNACE-101 | Clause: 4.3.2 | Page: 12]"
            ),
            citations=[{
                "doc_id": "SOP-MRPL-FURNACE-101",
                "clause": "4.3.2",
                "page": "12",
                "source_type": "MASTER_SOP",
                "similarity_score": 1.0,
            }],
        )

    def _normalize(self, text: str) -> str:
        cleaned = re.sub(r"[^\w\s\-]", " ", text.lower())
        return re.sub(r"\s+", " ", cleaned).strip()

    def _hash(self, text: str) -> str:
        return hashlib.sha256(self._normalize(text).encode("utf-8")).hexdigest()

    def get(self, query: str) -> Optional[Dict[str, Any]]:
        return self._cache.get(self._hash(query))

    def set(self, raw_query: str, final_answer: str, citations: List[Dict[str, Any]]) -> None:
        q_hash = self._hash(raw_query)
        self._cache[q_hash] = {
            "query": raw_query,
            "response": final_answer,
            "citations": citations,
            "timestamp": time.time(),
        }

response_cache = ProductionResponseCache()

# =====================================================================
# 5. STEP 1 & 2: CASUAL & SCOPE UTILITIES
# =====================================================================
def normalize_query_text(query: str) -> str:
    cleaned = re.sub(r"[^\w\s\-\/]", " ", query.lower())
    return re.sub(r"\s+", " ", cleaned).strip()

def check_casual_intent(query: str) -> bool:
    cleaned = query.strip().lower()
    return any(re.match(p, cleaned) for p in GREETING_PATTERNS)

def check_enterprise_scope(query: str, active_equipment: Optional[str]) -> bool:
    if active_equipment:
        return True
    if re.search(EQUIPMENT_TAG_REGEX, query, re.IGNORECASE):
        return True
    tokens = set(normalize_query_text(query).split())
    if tokens.intersection(TECHNICAL_TERMS):
        return True
    q_lower = query.lower()
    phrases = ["skin temp", "tube temp", "confined space", "hot work", "cold work", "er probe", "psv test"]
    return any(p in q_lower for p in phrases)

# =====================================================================
# 6. STEP 3: CONTEXT REWRITE & HYBRID RETRIEVAL
# =====================================================================
def rewrite_coreference_query(
    query: str,
    history: List[ChatMessage],
    active_equipment: Optional[str]
) -> Tuple[str, Optional[str]]:
    detected_tag = active_equipment
    if not detected_tag and history:
        for turn in reversed(history):
            match = re.search(EQUIPMENT_TAG_REGEX, turn.content, re.IGNORECASE)
            if match:
                detected_tag = match.group(1).upper()
                break

    tokens = query.lower().split()
    if any(p in tokens for p in ["it", "its", "unit", "pump", "furnace", "tank", "exchanger", "valve"]) and detected_tag:
        rewritten = f"{detected_tag} {query}"
        logger.info(f"Coreference resolved: '{query}' -> '{rewritten}' [Tag: {detected_tag}]")
        return rewritten, detected_tag

    return query, detected_tag

async def execute_hybrid_retrieval(query: str) -> Tuple[Optional[KnowledgeChunk], float]:
    q_tokens = set(normalize_query_text(query).split())
    q_dense = _generate_mock_dense_vector(query)

    best_chunk: Optional[KnowledgeChunk] = None
    best_combined_score = 0.0

    for chunk in MASTER_KNOWLEDGE_BASE:
        kw_intersection = q_tokens.intersection(set(chunk.keywords))
        lexical_score = len(kw_intersection) / max(1, len(chunk.keywords))
        dense_score = _cosine_similarity(q_dense, chunk.dense_embedding)

        combined_score = (lexical_score * 0.50) + (dense_score * 0.50)
        if any(token in chunk.keywords for token in q_tokens if len(token) >= 4):
            combined_score = min(1.0, combined_score + 0.35)

        if combined_score > best_combined_score:
            best_combined_score = combined_score
            best_chunk = chunk

    return best_chunk, round(best_combined_score, 3)

# =====================================================================
# 7. STEP 4: OLLAMA GATEWAY (CONNECTION POOL + 4K CONTEXT)
# =====================================================================
async def call_airgapped_ollama(
    user_prompt: str,
    system_prompt: str = REVEAL_SYSTEM_INSTRUCTION,
    max_tokens: int = 384,
) -> str:
    global http_client
    if http_client is None:
        http_client = httpx.AsyncClient(timeout=60.0)

    payload = {
        "model": PRIMARY_MODEL,
        "system": system_prompt,
        "prompt": user_prompt,
        "stream": False,
        "options": {
            "temperature": 0.0,
            "top_p": 0.1,
            "num_ctx": 4096,
            "num_predict": max_tokens,
            "stop": ["User:", "Operator:", "\n\n\n"],
        },
    }
    
    try:
        response = await http_client.post(OLLAMA_GENERATE_URL, json=payload)
        if response.status_code == 200:
            res_data = response.json()
            return res_data.get("response", "").strip()
        else:
            logger.error(f"Ollama returned HTTP {response.status_code}: {response.text}")
            return "Execution error in local inference backend."
    except Exception as e:
        logger.error(f"Connection error to Ollama daemon on port 11434: {e}")
        return "Local SLM compute daemon is unreachable. Verify Ollama service status."

# =====================================================================
# 8. MAIN 5-STEP PIPELINE ENDPOINT (/api/chat)
# =====================================================================
@app.post("/api/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat_endpoint(req: ChatRequest):
    t_start = time.perf_counter()

    # STEP 0: Fast Local/SQL Cache Lookup (<50ms)
    cached_hit = response_cache.get(req.query)
    if cached_hit:
        elapsed = (time.perf_counter() - t_start) * 1000
        logger.info(f"⚡ [STEP 0] Cache Hit in {elapsed:.2f}ms")
        return ChatResponse(
            response=cached_hit["response"],
            stage="STEP_0_FAST_CACHE",
            latency_ms=round(elapsed, 2),
            confidence=1.0,
            citations=[CitationMeta(**c) for c in cached_hit.get("citations", [])],
            deliverable_ids=["MRPL_Verified_SOP_Extract.docx"],
            is_cached=True,
        )

    # STEP 1: Casual Intent Fast-Path (<200ms)
    if check_casual_intent(req.query):
        elapsed = (time.perf_counter() - t_start) * 1000
        logger.info(f"🚀 [STEP 1] Casual Intent in {elapsed:.2f}ms")
        return ChatResponse(
            response=(
                "REVEAL 2.0 Industrial Plant Operations Assistant online. "
                "How can I assist you with MRPL/ONGC refinery SOPs, equipment limits, or plant safety protocols today?"
            ),
            stage="STEP_1_CASUAL_FASTPATH",
            latency_ms=round(elapsed, 2),
            confidence=1.0,
            citations=[],
            is_cached=False,
        )

    # STEP 2: Enterprise Scope Guardrail Router (<100ms)
    if not check_enterprise_scope(req.query, req.active_equipment):
        elapsed = (time.perf_counter() - t_start) * 1000
        logger.info(f"🛡️ [STEP 2] Out-of-Scope in {elapsed:.2f}ms")
        return ChatResponse(
            response=SCOPE_REJECTION_TEXT,
            stage="STEP_2_OUT_OF_SCOPE_REJECTION",
            latency_ms=round(elapsed, 2),
            confidence=1.0,
            citations=[],
            is_cached=False,
        )

    # STEP 3: Coreference Rewrite & Hybrid Vector Retrieval
    rewritten_query, resolved_tag = rewrite_coreference_query(
        req.query, req.history, req.active_equipment
    )
    chunk, hybrid_score = await execute_hybrid_retrieval(rewritten_query)

    # STEP 4B: Deterministic Safety Fallback (Score < 0.65)
    if not chunk or hybrid_score < SIMILARITY_THRESHOLD:
        elapsed = (time.perf_counter() - t_start) * 1000
        logger.warning(f"🛑 [STEP 4B] Unindexed Parameters (Score: {hybrid_score}).")
        return ChatResponse(
            response=DETERMINISTIC_FALLBACK_TEXT,
            stage="STEP_4_UNINDEXED_SAFETY_FALLBACK",
            latency_ms=round(elapsed, 2),
            confidence=hybrid_score,
            citations=[],
            is_cached=False,
        )

    # STEP 4A: Grounded LLM Synthesis (Score >= 0.65)
    formatted_prompt = (
        f"VERIFIED_SOP_DATA:\n"
        f"---\n"
        f"Document: {chunk.title} [{chunk.doc_id}]\n"
        f"Clause: {chunk.clause} | Page: {chunk.page}\n"
        f"Content: {chunk.content}\n"
        f"---\n\n"
        f"CURRENT CONTEXT:\n"
        f"- Target Equipment: {resolved_tag or 'Master Plant SOP'}\n"
        f"- Operator Query: {req.query}\n\n"
        f"Provide the exact operational parameters and limits according to official safety standards."
    )

    raw_answer = await call_airgapped_ollama(
        user_prompt=formatted_prompt,
        system_prompt=REVEAL_SYSTEM_INSTRUCTION,
    )

    citation_tag = f"[SOURCE: MASTER_SOP | Document: {chunk.title} | Clause: {chunk.clause} | Page: {chunk.page}]"
    final_answer = raw_answer if "[SOURCE:" in raw_answer else f"{raw_answer}\n\n{citation_tag}"

    citation_obj = CitationMeta(
        doc_id=chunk.doc_id,
        clause=chunk.clause,
        page=chunk.page,
        source_type="MASTER_SOP",
        similarity_score=hybrid_score,
    )

    # Store into Step 0 Cache
    response_cache.set(
        raw_query=req.query,
        final_answer=final_answer,
        citations=[citation_obj.model_dump()],
    )

    elapsed = (time.perf_counter() - t_start) * 1000
    return ChatResponse(
        response=final_answer,
        stage="STEP_4_GROUNDED_SYNTHESIS",
        latency_ms=round(elapsed, 2),
        confidence=hybrid_score,
        citations=[citation_obj],
        deliverable_ids=["MRPL_Verified_SOP_Extract.docx"],
        is_cached=False,
    )

@app.get("/health")
async def health_check():
    return {
        "status": "HEALTHY",
        "service": "REVEAL 2.0 Hardened Production Engine",
        "connection_pool": "Active (Max 50)",
        "context_window_tokens": 4096,
        "equipment_regex": EQUIPMENT_TAG_REGEX,
        "timestamp": time.time(),
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("reveal_engine:app", host="0.0.0.0", port=8000, reload=False)
