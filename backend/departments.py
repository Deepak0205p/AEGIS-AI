"""
Department Detection for Air-Gapped Local AI Backend.
Maps messages to departments using keyword + equipment-tag heuristics.
Supports multiple industrial domains: Refinery, PSU Manufacturing, Defence, Government.
Deterministic: word-boundary matching, most keyword hits wins, ties broken by tags.
"""

import re
from typing import Tuple, Optional


# Department keyword lists — word-boundary matching
# Refinery domain departments (original)
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

# PSU Manufacturing department keywords
PSU_DEPARTMENT_KEYWORDS = {
    "production": [
        "production", "manufacturing", "output", "tonnage", "yield",
        "melting", "casting", "forging", "machining", "assembly",
        "turbine", "generator", "boiler", "steam", "rotor",
        "stator", "heat rate", "efficiency", "load", "unit",
    ],
    "quality_control": [
        "quality", "qc", "qa", "iso 9001", "non-conformity", "nc",
        "capa", "audit", "testing", "metallurgy", "hardness",
        "tensile", "impact", "chemical composition", "spectrometer",
    ],
    "erection_commissioning": [
        "erection", "commissioning", "installation", "alignment",
        "testing", "pre-commissioning", "trial run", "punch list",
        "handover", "site", "foundation", "grouting",
    ],
    "design_engineering": [
        "design", "engineering", "drawing", "calculation",
        "specification", "bill of material", "3d model", "cad",
        "fem", "stress analysis", "thermal", "structural",
    ],
    "maintenance": [
        "maintenance", "overhaul", "repair", "breakdown", "preventive",
        "predictive", "vibration", "bearing", "alignment", "balancing",
        "lubrication", "welding", "ndt", "shutdown",
    ],
    "hse": [
        "safety", "hazard", "risk", "incident", "fire", "ppe",
        "permit", "confined space", "work at height", "environment",
        "emission", "effluent", "ibr", "boiler inspection",
    ],
    "materials": [
        "material", "store", "inventory", "spare", "procurement",
        "indent", "purchase", "vendor", "catalogue",
    ],
    "hr": [
        "hr", "human resource", "leave", "training", "policy",
        "attendance", "recruitment", "appraisal",
    ],
    "finance": [
        "budget", "cost", "expenditure", "billing", "invoice",
        "tender", "contract", "estimation",
    ],
    "it": [
        "it", "software", "network", "erp", "sap", "database",
    ],
    "general": [],
}

# Defence Manufacturing department keywords
DEFENCE_DEPARTMENT_KEYWORDS = {
    "production_shop": [
        "production", "manufacturing", "assembly", "shop floor",
        "machining", "fabrication", "integration", "line",
        "sub-assembly", "final assembly", "jig", "fixture",
    ],
    "quality_assurance_dgaqa": [
        "quality", "qa", "qc", "dgaqa", "inspection", "ndt",
        "acceptance", "lot testing", "proof testing", "mil-std",
        "jsg", "calibration", "gauge", "measurement",
    ],
    "design_rnd": [
        "design", "r&d", "research", "development", "prototype",
        "cad", "fem", "simulation", "analysis", "testing",
        "pdr", "cdr", "design review",
    ],
    "avionics": [
        "avionics", "electronics", "radar", "ew", "navigation",
        "communication", "display", "hud", "mfd", "software",
        "do-178c", "embedded", "fpga", "pcb",
    ],
    "armament_testing": [
        "ammunition", "weapon", "firing", "proof", "ballistic",
        "propellant", "explosive", "ordnance", "warhead",
        "range", "target", "velocity", "accuracy",
    ],
    "classified_docs": [
        "classified", "secret", "confidential", "restricted",
        "security", "clearance", "handling", "shredding",
        "official secrets", "movement register",
    ],
    "stores_logistics": [
        "store", "logistics", "inventory", "spare", "material",
        "receipt", "dispatch", "packaging", "preservation",
    ],
    "maintenance": [
        "maintenance", "repair", "overhaul", "mro", "servicing",
        "amc", "warranty", "breakdown",
    ],
    "hse": [
        "safety", "hazard", "fire", "emergency", "ppe",
        "environment", "incident", "drill",
    ],
    "hr": [
        "hr", "leave", "training", "induction", "policy",
    ],
    "security": [
        "security", "access control", "cctv", "perimeter",
        "guard", "pass", "biometric", "visitor",
    ],
    "general": [],
}

# Government Office department keywords
GOVT_DEPARTMENT_KEYWORDS = {
    "establishment": [
        "establishment", "posting", "transfer", "promotion",
        "seniority", "deputation", "cadre", "dpc",
        "confirmation", "probation", "service record",
    ],
    "finance_accounts": [
        "finance", "accounts", "budget", "expenditure", "pfms",
        "be", "re", "supplementary", "appropriation", "audit",
        "cag", "internal audit", "utilization certificate",
    ],
    "general_administration": [
        "administration", "office", "stationery", "furniture",
        "vehicle", "housekeeping", "maintenance", "building",
        "cpwd", "dsr", "works", "repair",
    ],
    "policy_planning": [
        "policy", "planning", "scheme", "program", "mission",
        "committee", "task force", "working group", "cabinet",
        "efc", "pib", "appraisal", "monitoring",
    ],
    "legal": [
        "legal", "court", "case", "writ", "contempt",
        "rti", "appeal", "arbitration", "contract",
        "agreement", "gazette", "notification",
    ],
    "rti_grievance": [
        "rti", "right to information", "cpio", "grievance",
        "cpgrams", "complaint", "public grievance",
        "section 8", "appeal", "cic",
    ],
    "parliament_questions": [
        "parliament", "lok sabha", "rajya sabha", "starred",
        "unstarred", "question", "assurance", "calling attention",
        "adjournment", "zero hour",
    ],
    "vigilance": [
        "vigilance", "cvc", "cbi", "inquiry", "investigation",
        "integrity", "property return", "disproportionate assets",
    ],
    "it_egovernance": [
        "it", "e-governance", "digital", "website", "portal",
        "nic", "software", "network", "cyber", "email",
    ],
    "hr": [
        "hr", "leave", "training", "ccs", "conduct rules",
        "pension", "nps", "gratuity", "attendance",
    ],
    "general": [],
}

# Domain → Department Keywords mapping
DOMAIN_DEPARTMENT_KEYWORDS = {
    "refinery": DEPARTMENT_KEYWORDS,
    "psu_manufacturing": PSU_DEPARTMENT_KEYWORDS,
    "defence": DEFENCE_DEPARTMENT_KEYWORDS,
    "government": GOVT_DEPARTMENT_KEYWORDS,
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
    Detects the department relevant to a message using active domain's keyword map.
    Returns (department_name, trigger_reason).
    
    Algorithm:
    1. Check HSE/safety critical phrases (highest priority, all domains)
    2. Check equipment tags (refinery domain)
    3. Count keyword hits per department (word-boundary matching) using active domain keywords
    4. Most hits wins; ties broken by first match
    5. No matches -> "general"
    """
    # Get active domain's keyword map
    try:
        from backend.domains import get_active_domain
        active_domain = get_active_domain()
    except Exception:
        active_domain = "refinery"

    dept_keywords = DOMAIN_DEPARTMENT_KEYWORDS.get(active_domain, DEPARTMENT_KEYWORDS)

    text = message.strip()
    text_lower = text.lower()

    # 0. HSE/Safety critical phrases get highest priority (all domains)
    hse_critical = ["oil spill", "gas leak", "near miss", "fire alarm", "safety hazard",
                    "confined space", "work at height", "oil leak", "h2s leak",
                    "explosion", "toxic release", "accident", "emergency"]
    hse_key = "hse" if "hse" in dept_keywords else "general"
    for phrase in hse_critical:
        if phrase in text_lower:
            return hse_key, f"keyword_{phrase}"

    # 1. Equipment tag detection (primarily for refinery/PSU domains)
    for dept, pattern in _TAG_PATTERNS.items():
        m = pattern.search(text)
        if m:
            # Map tag department to active domain's department if it exists
            if dept in dept_keywords:
                return dept, f"equipment_tag_{m.group(0).upper()}"
            # Fallback: return with general tag note
            return "general", f"equipment_tag_{m.group(0).upper()}"

    # 2. Keyword counting with word boundaries using domain-specific keywords
    scores: dict[str, int] = {}
    triggers: dict[str, str] = {}

    for dept, keywords in dept_keywords.items():
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
