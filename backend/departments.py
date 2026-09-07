"""
Department Detection for Air-Gapped Local AI Backend.
Maps messages to refinery departments using keyword + equipment-tag heuristics.
Deterministic: word-boundary matching, most keyword hits wins, ties broken by tags.
"""

import re
from typing import Tuple, Optional


# Department keyword lists — word-boundary matching
DEPARTMENT_KEYWORDS = {
    "operations": [
        "operation", "operating", "process", "unit", "tower", "column",
        "reactor", "furnace", "heater", "exchanger", "separator", "drum",
        "vessel", "flow", "pressure", "temperature", "level", "control",
        "valve", "pump", "compressor", "turbine", "shift", "log",
        "handover", "startup", "shutdown", "trip", "interlock",
        "setpoint", "alarm", " trip ", "cd", "vdu", "cdu", "crude",
        "distillation", "desalter", "reformer", "cracker", "column",
    ],
    "maintenance": [
        "maintenance", "repair", "overhaul", "turnaround", "shutdown",
        "bearing", "seal", "alignment", "balancing", "vibration",
        "lubrication", "grease", "oil change", "filter", "gasket",
        "bolting", "torque", "welding", "hot work", "cold work",
        "breakdown", "failure", "fix", "corrective", "preventive",
        "predictive", "condition monitoring",
    ],
    "inspection": [
        "inspection", "inspector", "ndt", "ut", "pt", "mt", "rt",
        "radiography", "ultrasonic", "thickness", "corrosion", "erosion",
        "crack", "leak", "damage", "degradation", "remaining life",
        "fitness", "fad", "api 510", "api 570", "api 653",
        "condition assessment", "survey", "psv", "safety valve",
        "calibration", "pop test",
    ],
    "hse": [
        "safety", "hazard", "risk", "incident", "accident", "near miss",
        "fire", "explosion", "gas leak", "h2s", "toxic", "confined space",
        "work at height", "scaffolding", "ppe", "permit", "ptw", "loto",
        "emergency", "evacuation", "drill", "first aid", "environment",
        "emission", "effluent", "waste", "spill", "oil spill", "oisd",
        "osha", "environmental",
    ],
    "planning": [
        "plan", "planning", "schedule", "schedule", "milestone",
        "gantt", "critical path", "resource", "mobilization",
        "demobilization", "turnaround planning", "project schedule",
        "baseline", "forecast", "lookahead",
    ],
    "projects": [
        "project", "engineering", "design", "detailed engineering",
        "feasibility", "conceptual", "basic engineering", "procurement",
        "construction", "commissioning", "installation", "fabrication",
        "piping", "structural", "civil", "electrical", "instrument",
        "e&i", "mcc", "plc", "dcs",
    ],
    "tech_services": [
        "technical service", "process engineering", "process design",
        "simulation", "hysis", "aspen", "heat exchanger design",
        "relief sizing", "flare sizing", "pipe stress", "pipeline",
        "hydraulic", "thermodynamic", "property", "composition",
    ],
    "qc_lab": [
        "qc", "quality control", "laboratory", "lab", "testing",
        "sample", "analysis", "viscosity", "density", "flash point",
        "pour point", "sulfur", "water content", "bs&w", "tbn",
        "elemental", "xrf", "gc", "hplc",
    ],
    "oil_movement": [
        "oil movement", "tank farm", "tank", "storage", "blending",
        "loading", "unloading", "pipeline transfer", "metering",
        " Custody Transfer", "tank gauging", "ullage", "level",
        "tk-", "slop",
    ],
    "materials": [
        "material", "store", "warehouse", "inventory", "spare part",
        "consumable", "chemical", "catalyst", "additive", "lube oil",
        "grease", "spare", "material receipt", "gate pass",
    ],
    "finance": [
        "budget", "cost", "expenditure", "capex", "opex", "billing",
        "invoice", "payment", "po", "purchase order", "rate contract",
        "estimation", "quotation", "tender", "financial",
    ],
    "hr": [
        "hr", "human resource", "leave", "attendance", "payroll",
        "training", "induction", "policy", "grievance", "appraisal",
        "recruitment", "onboarding", "roster", "shift schedule",
    ],
    "legal": [
        "legal", "compliance", "contract", "agreement", "memorandum",
        "terms", "condition", "liability", "penalty", "arbitration",
        "regulation", "statutory",
    ],
    "it": [
        "it", "information technology", "software", "hardware",
        "network", "server", "database", "backup", "cybersecurity",
        "firewall", "vpn", "active directory", "email system",
    ],
    "general": [],  # catch-all
}

# Equipment tag prefix -> department mapping (TAG_REGISTRY)
# Patterns match tags anywhere in the text (no ^ anchor)
TAG_REGISTRY = {
    r"\bF-?\d+": "operations",
    r"\b[PK]-?\d+": "maintenance",
    r"\b(?:E|HEX)-?\d+": "inspection",
    r"\bTK-?\d+": "oil_movement",
    r"\b[VR]-?\d+": "operations",
    r"\bMOV-?\d+": "operations",
    r"\bPSV-?\d+": "inspection",
    r"\b(?:FI|TI|PI|LI|FCV|TCV|PCV)-?\d+": "inspection",
}

_TAG_PATTERNS: dict[str, re.Pattern] = {}
for _pat, _dept in TAG_REGISTRY.items():
    if _dept not in _TAG_PATTERNS:
        _TAG_PATTERNS[_dept] = re.compile(_pat, re.IGNORECASE)
    else:
        # Combine patterns for same department
        _TAG_PATTERNS[_dept] = re.compile(
            _TAG_PATTERNS[_dept].pattern + "|" + _pat, re.IGNORECASE
        )


def detect_department(message: str) -> Tuple[str, Optional[str]]:
    """
    Detects the refinery department relevant to a message.
    Returns (department_name, trigger_reason).
    
    Algorithm:
    1. Check equipment tags first (highest confidence)
    2. Count keyword hits per department (word-boundary matching)
    3. Most hits wins; ties broken by first match
    4. No matches -> "general"
    """
    text = message.strip()
    text_lower = text.lower()

    # 0. HSE critical phrases get highest priority (safety incidents override equipment tags)
    hse_critical = ["oil spill", "gas leak", "near miss", "fire alarm", "safety hazard",
                    "confined space", "work at height", "oil leak", "h2s leak",
                    "explosion", "toxic release"]
    for phrase in hse_critical:
        if phrase in text_lower:
            return "hse", f"keyword_{phrase}"

    # 1. Equipment tag detection
    for dept, pattern in _TAG_PATTERNS.items():
        m = pattern.search(text)
        if m:
            return dept, f"equipment_tag_{m.group(0).upper()}"

    # 2. Keyword counting with word boundaries
    # HSE gets priority: check HSE multi-word phrases first
    text_lower_lower = text_lower
    hse_phrases = ["oil spill", "gas leak", "near miss", "fire alarm", "safety hazard",
                   "confined space", "work at height", "oil leak"]
    for phrase in hse_phrases:
        if phrase in text_lower_lower:
            return "hse", f"keyword_{phrase}"

    scores: dict[str, int] = {}
    triggers: dict[str, str] = {}

    for dept, keywords in DEPARTMENT_KEYWORDS.items():
        if not keywords:
            continue
        count = 0
        for kw in keywords:
            # Word boundary match for single words, substring for phrases
            if " " in kw:
                if kw in text_lower:
                    count += 1
                    if not triggers.get(dept):
                        triggers[dept] = f"keyword_{kw}"
            else:
                if re.search(rf"\b{re.escape(kw)}\b", text_lower):
                    count += 1
                    if not triggers.get(dept):
                        triggers[dept] = f"keyword_{kw}"
        if count > 0:
            scores[dept] = count

    if scores:
        best_dept = max(scores, key=scores.get)
        return best_dept, triggers.get(best_dept, f"keyword_match")

    return "general", "no_match"
