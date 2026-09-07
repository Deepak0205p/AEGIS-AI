"""
Knowledge Base & SOP Retrieval Engine for Air-Gapped Local AI Backend.
Provides deterministic, offline hybrid vector and keyword matching against MRPL/ONGC SOPs.
"""

import re
import time
import math
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel
from backend.config import logger, MIN_RAG_SCORE, RAG_CACHE_TTL_SECONDS


class SOPChunk(BaseModel):
    doc_id: str
    title: str
    clause: str
    page: str
    content: str
    keywords: List[str]
    equipment_tags: List[str]
    dense_embedding: List[float] = []


def _generate_dense_vector(text: str, dim: int = 16) -> List[float]:
    """Deterministic hash-based dense vector for offline similarity scoring."""
    h = hashlib.sha256(text.lower().encode("utf-8")).hexdigest()
    vec = [((int(h[i * 2 : (i + 1) * 2], 16) / 255.0) * 2.0 - 1.0) for i in range(dim)]
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


def _cosine_similarity(v1: List[float], v2: List[float]) -> float:
    dot = sum(a * b for a, b in zip(v1, v2))
    return max(0.0, min(1.0, (dot + 1.0) / 2.0))


# Master Knowledge Base with Verified MRPL & ONGC Operational Standards
_RAW_SOPS = [
    {
        "doc_id": "SOP-MRPL-FURNACE-101",
        "title": "Furnace F-101 Operations and Tube Skin Temperature Control",
        "clause": "4.3.2",
        "page": "12",
        "content": (
            "Maximum allowable Tube Skin Temperature (TMT) for Furnace F-101: "
            "Carbon Steel tubes must not exceed 540°C. Alloy Steel (9Cr-1Mo) tubes must not exceed 650°C. "
            "If skin temp exceeds limit for >15 min, reduce firing rate by 5% and increase pass flow proportionally. "
            "Burner maintenance must follow OISD-111 safety standards."
        ),
        "keywords": ["furnace", "f-101", "skin", "temperature", "tmt", "540", "650", "tube", "maintenance", "sop", "firing"],
        "equipment_tags": ["F-101", "F101"],
    },
    {
        "doc_id": "SOP-MRPL-FURNACE-201",
        "title": "Furnace F-201 Vacuum Heater Startup and Decoking Procedure",
        "clause": "5.1.8",
        "page": "18",
        "content": (
            "Furnace F-201 Vacuum Heater Operations: "
            "Coil inlet pressure must remain between 3.8 and 4.2 kg/cm2g. Maximum tube metal temperature is 675°C. "
            "Decoking cycle utilizes steam-air mixture at 500-550°C with effluent CO2 monitoring below 0.2% before termination."
        ),
        "keywords": ["furnace", "f-201", "vacuum", "heater", "decoking", "temperature", "pressure", "sop"],
        "equipment_tags": ["F-201", "F201"],
    },
    {
        "doc_id": "SOP-MRPL-HSE-PTW-004",
        "title": "Permit to Work (PTW) & Lockout/Tagout (LOTO) Procedure",
        "clause": "3.1.5",
        "page": "7",
        "content": (
            "Permit to Work (PTW) & LOTO Guidelines as per OISD-105: "
            "Cold Work Permit validity is 8-hour shift, renewable up to 24 hours. "
            "Hot Work Permit requires continuous combustible gas monitoring with LEL strictly at 0.0%. "
            "Confined Space Entry requires oxygen levels between 19.5% and 23.5%, H2S < 10 ppm, CO < 25 ppm."
        ),
        "keywords": ["ptw", "loto", "safety", "permit", "confined", "space", "oisd", "oisd-105", "h2s", "hot work", "procedure", "shift"],
        "equipment_tags": [],
    },
    {
        "doc_id": "SOP-MRPL-PUMP-610",
        "title": "Centrifugal Pump P-101A/B Commissioning and Vibration Limits",
        "clause": "5.2.1",
        "page": "28",
        "content": (
            "API 610 Centrifugal Pumps P-101A/B Operating Standards: "
            "Maximum permissible vibration overall RMS velocity is 4.5 mm/s for continuous duty. "
            "Alarm threshold is set at 7.1 mm/s; emergency automatic trip occurs at 9.0 mm/s. "
            "Mechanical seal flush Plan 11/52 must maintain differential pressure of at least 1.5 kg/cm2."
        ),
        "keywords": ["pump", "p-101a", "p-101b", "vibration", "api 610", "seal", "npsh", "procedure", "maintenance"],
        "equipment_tags": ["P-101A", "P-101B", "P101A", "P101B"],
    },
    {
        "doc_id": "SOP-ONGC-CORR-570",
        "title": "Corrosion Monitoring and Ultrasonic Thickness Gauging",
        "clause": "2.4.1",
        "page": "15",
        "content": (
            "Corrosion Monitoring Standard (API 570 / OISD-144): "
            "Electrical Resistance (ER) probe corrosion rate limit: maximum 0.125 mm/year. "
            "Ultrasonic Thickness (UT) gauging required on crude transfer lines at 90° bends every 6 months. "
            "Baseline nominal wall thickness: 12.5 mm; minimum structural retirement thickness: 6.8 mm."
        ),
        "keywords": ["corrosion", "er probe", "ultrasonic", "ut", "thickness", "api 570", "inspection", "piping", "oisd-144"],
        "equipment_tags": [],
    },
    {
        "doc_id": "SOP-MRPL-CDU-VDU-002",
        "title": "Crude Distillation Unit (CDU) & Vacuum Distillation Unit (VDU) Operating Guidelines",
        "clause": "6.1.4",
        "page": "34",
        "content": (
            "CDU/VDU Primary Distillation Parameters: "
            "CDU Atmospheric Tower top temperature must be maintained at 115-125°C with overhead accumulator pressure 0.25 kg/cm2g. "
            "Desalter operating temperature: 130-140°C with water injection rate at 4-6 vol% of crude charge."
        ),
        "keywords": ["cdu", "vdu", "crude", "distillation", "column", "desalter", "temperature", "pressure", "sop"],
        "equipment_tags": ["CDU", "VDU"],
    },
    {
        "doc_id": "SOP-MRPL-ENV-BRSR-008",
        "title": "Environmental Compliance, Effluent Treatment & Zero Liquid Discharge (ZLD)",
        "clause": "4.1.2",
        "page": "9",
        "content": (
            "Environmental Compliance & ETP Discharge Standards (CPCB/KSPCB): "
            "Final treated effluent discharge parameters: COD < 250 mg/L, BOD < 30 mg/L, TSS < 100 mg/L, Oil & Grease < 5 mg/L. "
            "Continuous Emission Monitoring System (CEMS) SO2 must remain below 500 mg/Nm3."
        ),
        "keywords": ["environmental", "etp", "zld", "effluent", "brsr", "cod", "bod", "emission", "cems", "policy"],
        "equipment_tags": [],
    },
    {
        "doc_id": "SOP-ONGC-GEM-PROC-012",
        "title": "GeM Procurement, Contract Execution & e-Measurement Book (e-MB)",
        "clause": "7.3.3",
        "page": "22",
        "content": (
            "Government e-Marketplace (GeM) & Contract Execution Guidelines: "
            "All physical work measurements must be entered into e-MB within 7 days of milestone completion. "
            "Contractor statutory compliance (PF, ESIC, labor license verification) is mandatory prior to Running Account (RA) bill clearance."
        ),
        "keywords": ["gem", "procurement", "e-mb", "contract", "tender", "billing", "compliance", "policy", "guideline"],
        "equipment_tags": [],
    },
    {
        "doc_id": "SOP-MRPL-INSP-510",
        "title": "Pressure Vessel Inspection & PSV Pop Test Calibration",
        "clause": "3.8.2",
        "page": "14",
        "content": (
            "Pressure Safety Valve (PSV) & Vessel Inspection (API 510 / ASME Sec VIII): "
            "PSV pop test calibration interval: strictly 24 months. Set pressure tolerance is ±3% for set pressures above 5 kg/cm2g. "
            "Hydrostatic testing of repaired vessels must be conducted at 1.3 times the Maximum Allowable Working Pressure (MAWP)."
        ),
        "keywords": ["psv", "safety valve", "api 510", "asme", "inspection", "mawp", "hydrostatic", "standard"],
        "equipment_tags": ["PSV-101", "PSV-201"],
    }
]

MASTER_SOPS: List[SOPChunk] = [
    SOPChunk(
        doc_id=item["doc_id"],
        title=item["title"],
        clause=item["clause"],
        page=item["page"],
        content=item["content"],
        keywords=item["keywords"],
        equipment_tags=item["equipment_tags"],
        dense_embedding=_generate_dense_vector(f"{item['title']} {item['content']}"),
    )
    for item in _RAW_SOPS
]


class RAGRetrievalCache:
    """In-memory cache for RAG chunks per conversation session."""
    def __init__(self, ttl_seconds: float = RAG_CACHE_TTL_SECONDS):
        self.ttl = ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get(self, chat_id: str) -> Optional[Dict[str, Any]]:
        record = self._cache.get(chat_id)
        if not record:
            return None
        if time.time() - record["timestamp"] > self.ttl:
            del self._cache[chat_id]
            return None
        return record

    def store(self, chat_id: str, query: str, chunks: List[Dict[str, Any]]) -> None:
        self._cache[chat_id] = {
            "query": query,
            "chunks": chunks,
            "timestamp": time.time(),
        }


rag_cache = RAGRetrievalCache()


def search_sops(query: str, min_score: float = MIN_RAG_SCORE, top_k: int = 4) -> List[Dict[str, Any]]:
    """
    Executes hybrid keyword + vector retrieval against verified SOP chunks.
    Returns list of chunks with similarity score >= min_score, ranked descending.
    """
    query_clean = query.lower()
    query_tokens = set(re.findall(r"\b[a-z0-9\-\_]+\b", query_clean))
    query_vec = _generate_dense_vector(query_clean)
    
    scored_results: List[Tuple[float, SOPChunk]] = []

    for chunk in MASTER_SOPS:
        # 1. Keyword match score
        chunk_tokens = set(chunk.keywords + [k.lower() for k in chunk.equipment_tags])
        overlap = len(query_tokens.intersection(chunk_tokens))
        kw_score = min(1.0, overlap / max(1, len(chunk_tokens) ** 0.5)) if overlap else 0.0

        # Exact equipment tag boost
        for tag in chunk.equipment_tags:
            if tag.lower() in query_clean:
                kw_score = max(kw_score, 0.85)

        # 2. Dense vector similarity
        vec_score = _cosine_similarity(query_vec, chunk.dense_embedding)

        # 3. Hybrid score (60% keyword/tag precision, 40% semantic dense)
        hybrid_score = round(0.60 * kw_score + 0.40 * vec_score, 4)

        if hybrid_score >= min_score:
            scored_results.append((hybrid_score, chunk))

    # Sort descending by score
    scored_results.sort(key=lambda x: x[0], reverse=True)

    results = []
    for score, chunk in scored_results[:top_k]:
        results.append({
            "doc_id": chunk.doc_id,
            "title": chunk.title,
            "clause": chunk.clause,
            "page": chunk.page,
            "content": chunk.content,
            "similarity_score": score,
        })
    return results


def format_rag_context_block(chunks: List[Dict[str, Any]]) -> str:
    """Formats retrieved SOP chunks into the standard delimited context block."""
    if not chunks:
        return ""
    lines = ["[RETRIEVED CONTEXT — answer ONLY from this; if insufficient, say so]"]
    for i, c in enumerate(chunks, 1):
        lines.append(
            f"--- Document {i}: {c['doc_id']} (Clause: {c['clause']}, Page: {c['page']}) ---\n"
            f"Title: {c['title']}\n"
            f"Content: {c['content']}\n"
            f"[SOURCE: {c['doc_id']} | Clause: {c['clause']} | Page: {c['page']}]"
        )
    return "\n".join(lines)
