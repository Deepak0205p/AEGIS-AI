"""
Domain Registry & Configuration for Multi-Industry Sovereign AI Workbench.
Supports runtime domain switching across Refineries, PSU Manufacturing,
Defence Manufacturing, and Government Offices.
"""

import os
from typing import Dict, Any, Optional, List
from backend.config import logger

# ── Master Domain Registry ──
DOMAIN_REGISTRY: Dict[str, Dict[str, Any]] = {
    "refinery": {
        "name": "Oil Refinery & Petrochemicals",
        "short_name": "Refinery",
        "org_examples": "MRPL, ONGC, IOCL, BPCL, HPCL, GAIL",
        "icon": "🛢️",
        "color": "#F97316",
        "description": "Petroleum refining, upstream E&P, petrochemical processing",
        "system_identity": (
            "You are AEGIS AI, an authoritative Industrial Operations & Plant Safety Assistant "
            "for oil refineries, petrochemical complexes, and upstream E&P facilities (MRPL, ONGC, IOCL style)."
        ),
        "fallback_text": (
            "Operational parameters for this query are not indexed in active Master SOPs "
            "(OISD/API/MRPL). Manual entry or Shift In-Charge sign-off required."
        ),
        "equipment_tag_regex": r"\b[A-Z]{1,4}[-]\d{2,5}[A-Z]?\b",
        "rag_domain_keywords": [
            "sop", "manual", "procedure", "standard", "specification", "drawing",
            "pid", "inspection", "approval", "guideline", "policy", "shift",
            "in-charge", "asme", "oisd", "ibr", "as per", "according to",
            "kya procedure", "maintenance", "tmt", "operating limit", "setpoint",
            "loto", "ptw", "vibration", "interlock", "psv", "flare", "corrosion",
        ],
        "welcome_suggestions": [
            {"text": "CDU shift handover log banao", "icon": "📋"},
            {"text": "F-101 furnace tube skin temperature limit?", "icon": "🌡️"},
            {"text": "H2S ka TLV and exposure symptoms?", "icon": "⚗️"},
            {"text": "Calculate reflux ratio: vapor 120 t/h, distillate 30 t/h", "icon": "🔬"},
            {"text": "Oil spill incident report draft karo", "icon": "📝"},
            {"text": "PSV pop test calibration interval as per API 510?", "icon": "🔧"},
        ],
    },
    "psu_manufacturing": {
        "name": "PSU Heavy Engineering & Manufacturing",
        "short_name": "PSU Manufacturing",
        "org_examples": "BHEL, SAIL, NTPC, BEML, HMT, NLC, NALCO",
        "icon": "🏭",
        "color": "#3B82F6",
        "description": "Power generation equipment, steel production, heavy machinery manufacturing",
        "system_identity": (
            "You are AEGIS AI, an authoritative Industrial Engineering & Plant Operations Assistant "
            "for PSU heavy engineering and manufacturing facilities (BHEL, SAIL, NTPC style). "
            "You assist with turbine engineering, boiler operations, steel metallurgy, quality control, "
            "commissioning procedures, and manufacturing process optimization."
        ),
        "fallback_text": (
            "Operational parameters for this query are not indexed in active Master SOPs "
            "(IS/ISO/IBR/ASME standards). Manual entry or Plant In-Charge sign-off required."
        ),
        "equipment_tag_regex": r"\b(?:TG|BFP|CHP|ESP|FD|ID|PA|CEP|HPH|LPH|CT|DM|APH|SG|BF|BOF|CC|RM|FM)[-]?\d{1,5}[A-Z]?\b",
        "rag_domain_keywords": [
            "sop", "manual", "procedure", "standard", "specification", "drawing",
            "inspection", "approval", "guideline", "policy", "commissioning",
            "as per", "according to", "maintenance", "turbine", "boiler",
            "vibration", "metallurgy", "quality", "ibr", "is standard",
            "asme", "iso", "heat rate", "efficiency", "tolerance",
            "welding", "wps", "pqr", "ndt", "radiography",
        ],
        "welcome_suggestions": [
            {"text": "Steam turbine rotor vibration limits as per ISO 10816?", "icon": "⚙️"},
            {"text": "Boiler drum level trip settings kya hai?", "icon": "🌡️"},
            {"text": "Calculate turbine heat rate from given parameters", "icon": "🔬"},
            {"text": "Equipment commissioning checklist banao", "icon": "📋"},
            {"text": "Welding procedure WPS for Cr-Mo steel", "icon": "🔧"},
            {"text": "Daily production log for steel melting shop", "icon": "📝"},
        ],
    },
    "defence": {
        "name": "Defence Manufacturing & R&D",
        "short_name": "Defence",
        "org_examples": "HAL, BDL, BEL, DRDO Labs, OFB/AVANI, MDL, GSL, GRSE",
        "icon": "🛡️",
        "color": "#10B981",
        "description": "Defence equipment manufacturing, avionics, electronics, ordnance, aerospace R&D",
        "system_identity": (
            "You are AEGIS AI, an authoritative Defence Manufacturing & R&D Operations Assistant "
            "for defence PSUs and DRDO laboratories (HAL, BDL, BEL, DRDO style). "
            "You assist with manufacturing quality assurance (DGAQA), NDT inspection, "
            "design reviews, flight/ground testing, classified document handling, "
            "and defence procurement procedures (DPP/DAP)."
        ),
        "fallback_text": (
            "Operational parameters for this query are not indexed in active Master SOPs "
            "(DGAQA/JSG/MIL-STD/DEF-STD standards). Manual entry or Quality In-Charge sign-off required."
        ),
        "equipment_tag_regex": r"\b(?:DRG|ACA|LCA|MBT|UAV|ALH|LCH|ATGM|SAM|EW|RWR|HUD|INS|IFF)[-]?\d{1,5}[A-Z]?\b",
        "rag_domain_keywords": [
            "sop", "manual", "procedure", "standard", "specification", "drawing",
            "inspection", "approval", "guideline", "policy", "testing",
            "as per", "according to", "maintenance", "quality", "dgaqa",
            "mil-std", "def-std", "jsg", "acceptance", "lot testing",
            "ndt", "radiography", "proof testing", "classified", "secret",
            "confidential", "design review", "pdr", "cdr", "flight test",
            "avionics", "airworthiness", "cemilac", "rcma",
        ],
        "welcome_suggestions": [
            {"text": "DGAQA NDT inspection protocol for aircraft assembly?", "icon": "✈️"},
            {"text": "Lot acceptance test report banao for ammunition batch", "icon": "📋"},
            {"text": "Classified document handling procedure kya hai?", "icon": "🔒"},
            {"text": "Design Review Meeting minutes draft karo", "icon": "📝"},
            {"text": "Calculate propellant burn rate from test data", "icon": "🔬"},
            {"text": "Avionics software verification as per DO-178C", "icon": "💻"},
        ],
    },
    "government": {
        "name": "Government Offices & Ministries",
        "short_name": "Government",
        "org_examples": "Ministries, Secretariats, CPWD, Directorates, Commissionerates",
        "icon": "🏛️",
        "color": "#8B5CF6",
        "description": "Administrative offices, policy drafting, RTI compliance, file noting, circulars, budget preparation",
        "system_identity": (
            "You are AEGIS AI, an authoritative Government Administration & Office Procedure Assistant "
            "for Central/State Government offices, Ministries, and Secretariats. "
            "You assist with file noting, office memorandums, RTI responses, cabinet notes, "
            "parliament question replies, budget estimation, GFR procurement rules, "
            "and CCS service rules compliance."
        ),
        "fallback_text": (
            "Specific procedural details for this query are not indexed in active reference manuals "
            "(Manual of Office Procedure/GFR/CCS Rules). Please consult the Section Officer or refer to relevant gazette notification."
        ),
        "equipment_tag_regex": r"\b(?:F\.No\.|File\s*No\.?|OM\s*No\.?|No\.)\s*\d{1,3}[/-]\d{1,4}[/-]\d{2,4}(?:[-][A-Z]+)?\b",
        "rag_domain_keywords": [
            "sop", "manual", "procedure", "rule", "notification", "circular",
            "office memorandum", "om", "guideline", "policy", "gazette",
            "as per", "according to", "gfr", "ccs", "frsr", "rti",
            "noting", "dopt", "cabinet", "parliament", "lok sabha",
            "rajya sabha", "starred", "unstarred", "budget", "expenditure",
            "pfms", "nps", "pension", "leave rules", "conduct rules",
            "vigilance", "cvc", "tender", "procurement",
        ],
        "welcome_suggestions": [
            {"text": "Office Memorandum draft karo regarding revised leave rules", "icon": "📋"},
            {"text": "RTI response protocol under Section 6(1)?", "icon": "📜"},
            {"text": "Cabinet note format for EFC approval", "icon": "🏛️"},
            {"text": "GFR 2017 procurement rules for purchases above 25 lakhs?", "icon": "💰"},
            {"text": "Parliament question reply (unstarred) draft karo", "icon": "📝"},
            {"text": "Calculate gratuity for 14 years service at basic 85,000", "icon": "🔬"},
        ],
    },
}


# ── Runtime Domain State ──
_active_domain: str = os.getenv("AEGIS_DOMAIN", "refinery")


def get_active_domain() -> str:
    """Returns the currently active domain key."""
    global _active_domain
    if _active_domain not in DOMAIN_REGISTRY:
        _active_domain = "refinery"
    return _active_domain


def set_active_domain(domain_key: str) -> bool:
    """
    Sets the active domain at runtime.
    Returns True if the domain was valid and set, False otherwise.
    """
    global _active_domain
    if domain_key in DOMAIN_REGISTRY:
        _active_domain = domain_key
        logger.info(f"[DOMAIN] Active domain switched to: '{domain_key}' ({DOMAIN_REGISTRY[domain_key]['name']})")
        return True
    logger.warning(f"[DOMAIN] Invalid domain key: '{domain_key}'. Available: {list(DOMAIN_REGISTRY.keys())}")
    return False


def get_domain_config(domain_key: Optional[str] = None) -> Dict[str, Any]:
    """Returns the full config dict for the specified or active domain."""
    key = domain_key or get_active_domain()
    return DOMAIN_REGISTRY.get(key, DOMAIN_REGISTRY["refinery"])


def get_active_domain_info() -> Dict[str, Any]:
    """Returns metadata and standard citations for active domain."""
    key = get_active_domain()
    conf = get_domain_config(key)
    standards_map = {
        "refinery": ["OISD-STD-105", "API 510", "API 570", "IS 1448", "IBR 1950"],
        "psu_manufacturing": ["IS 2062", "ISO 10816", "IBR 1950", "ASME Section VIII", "GFR 2017"],
        "defence": ["DAP 2020", "DGAQA QA-PROC", "MIL-STD-810H", "MIL-STD-461G", "JSG Guidelines"],
        "government": ["CSMOP 2019", "GFR 2017", "RTI Act 2005", "DoPT Rules", "CCS Conduct Rules 1964"],
    }
    return {
        "key": key,
        "name": conf.get("name", "Industrial Enterprise"),
        "code": conf.get("short_name", "Enterprise"),
        "icon": conf.get("icon", "🏢"),
        "color": conf.get("color", "#3B82F6"),
        "description": conf.get("description", ""),
        "standards": standards_map.get(key, ["ISO 9001", "IS Standard"]),
        "org_examples": conf.get("org_examples", ""),
    }


def get_all_domains() -> List[Dict[str, Any]]:
    """Returns a list of all domain configs with their keys."""
    return [{"key": k, **v} for k, v in DOMAIN_REGISTRY.items()]


def list_domains() -> List[Dict[str, Any]]:
    """Alias for get_all_domains."""
    return get_all_domains()


def get_system_identity() -> str:
    """Returns the system identity prompt for the active domain."""
    return get_domain_config()["system_identity"]


def get_fallback_text() -> str:
    """Returns the deterministic fallback text for the active domain."""
    return get_domain_config()["fallback_text"]


def get_equipment_tag_regex() -> str:
    """Returns the equipment tag regex for the active domain."""
    return get_domain_config()["equipment_tag_regex"]


def get_rag_keywords() -> List[str]:
    """Returns the RAG domain keywords for the active domain."""
    return get_domain_config()["rag_domain_keywords"]


def get_welcome_suggestions() -> List[Dict[str, str]]:
    """Returns the welcome suggestions for the active domain."""
    return get_domain_config()["welcome_suggestions"]
