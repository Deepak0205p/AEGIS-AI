"""
Chemical Safety & Database Module for Air-Gapped Local AI Backend.
Loads verified refinery chemicals from backend/data/chemical_db.json,
performs regex matching (plural-tolerant for full names, exact for formulas),
and provides deterministic chemical context injection.
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from backend.config import logger

_DB_PATH = Path(__file__).resolve().parent / "data" / "chemical_db.json"
_CHEMICAL_ENTRIES: List[Dict[str, Any]] = []
_COMPILED_PATTERNS: List[Tuple[re.Pattern, Dict[str, Any]]] = []

# Short formulas / symbols / abbreviations that must NEVER have plural suffixes
_EXACT_ONLY = {
    "h2", "co", "hf", "h2s", "nh3", "naoh", "h2so4", "so2", "cl2", "c6h6",
    "c7h8", "c8h10", "c3h8", "c4h10", "c3h6", "c2h4", "ch4", "c2h6", "ch3oh",
    "c6h5oh", "px", "lpg", "atf", "hsd", "fo", "rfo", "lshs", "vg-30", "vg-40",
    "dea", "mdea", "meg", "teg", "hcl", "n2", "o2", "mtbe", "hg", "lin", "lox",
    "ch2o2", "c6h8o7"
}


def load_chemical_db() -> List[Dict[str, Any]]:
    """Loads and indexes chemical entries with precompiled regex patterns."""
    global _CHEMICAL_ENTRIES, _COMPILED_PATTERNS
    if not _DB_PATH.exists():
        logger.warning(f"[CHEM_DB] Chemical database not found at {_DB_PATH}")
        return []

    try:
        with open(_DB_PATH, "r", encoding="utf-8") as f:
            _CHEMICAL_ENTRIES = json.load(f)
    except Exception as e:
        logger.error(f"[CHEM_DB] Error loading {_DB_PATH}: {e}")
        return []

    _COMPILED_PATTERNS = []
    for chem in _CHEMICAL_ENTRIES:
        names = [chem["name"]] + chem.get("aliases", [])
        pattern_parts = []
        for n in names:
            n_clean = n.strip().lower()
            escaped = re.escape(n_clean)
            if n_clean in _EXACT_ONLY or len(n_clean) <= 3 or any(char.isdigit() for char in n_clean):
                # Exact match only for formulas, symbols, and short codes
                pattern_parts.append(escaped)
            else:
                # Plural-tolerant for standard English names (e.g. benzene, solvent, amine)
                pattern_parts.append(rf"{escaped}(?:s|es)?")

        combined_regex = re.compile(rf"\b(?:{'|'.join(pattern_parts)})\b", re.IGNORECASE)
        _COMPILED_PATTERNS.append((combined_regex, chem))

    logger.info(f"[CHEM_DB] Loaded {len(_CHEMICAL_ENTRIES)} verified chemicals from {_DB_PATH}")
    return _CHEMICAL_ENTRIES


# Initialize on import
load_chemical_db()


def detect_chemicals(message: str) -> List[Dict[str, Any]]:
    """
    Detects chemicals mentioned in the message using regex.
    Returns list of matched chemical dictionaries (deduplicated by CAS).
    """
    text = message.strip()
    if not text or not _COMPILED_PATTERNS:
        return []

    matched: List[Dict[str, Any]] = []
    seen_cas = set()

    for pattern, chem in _COMPILED_PATTERNS:
        if pattern.search(text):
            cas = chem.get("cas")
            if cas not in seen_cas:
                seen_cas.add(cas)
                matched.append(chem)

    if matched:
        chem_names = [c["name"] for c in matched]
        logger.info(f"[CHEM_DB] Detected chemical(s): {chem_names} in message: {text[:60]!r}")

    return matched


def format_chemical_context_block(chemicals: List[Dict[str, Any]]) -> str:
    """Formats detected chemical records into an authoritative context block."""
    if not chemicals:
        return ""

    lines = ["[VERIFIED CHEMICAL DATABASE (MSDS/ACGIH) — use exact values from here; never invent or guess]"]
    for i, c in enumerate(chemicals, 1):
        hazards_str = ", ".join(c.get("hazards", [])) if isinstance(c.get("hazards"), list) else c.get("hazards", "")
        lines.append(
            f"--- Chemical {i}: {c['name']} ---\n"
            f"- Full Name / Aliases: {c['name']} ({', '.join(c.get('aliases', []))})\n"
            f"- CAS Registry Number: {c['cas']}\n"
            f"- Chemical Formula: {c['formula']}\n"
            f"- Physical State: {c.get('state', 'N/A')}\n"
            f"- Hazard Classification: {hazards_str}\n"
            f"- ACGIH TLV-TWA / Exposure Limits: {c.get('tlv_twa', 'N/A')}\n"
            f"- Symptoms of Exposure: {c.get('exposure_symptoms', 'N/A')}\n"
            f"- Emergency First Aid: {c.get('first_aid', 'N/A')}\n"
            f"- Required PPE: {c.get('ppe', 'N/A')}\n"
            f"- Handling & Storage: {c.get('handling_storage', 'N/A')}\n"
            f"- Refinery Units & Industrial Context: {c.get('refinery_context', 'N/A')}\n"
            f"[SOURCE: Master Chemical Safety DB | CAS: {c['cas']}]"
        )
    return "\n".join(lines)
