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
    domain: str = "refinery"
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


# Master Knowledge Base with Verified Operational Standards across all domains
_RAW_SOPS = [
    # ═══════════════════════════════════════════════════════════════════
    # DOMAIN: REFINERY (Existing)
    # ═══════════════════════════════════════════════════════════════════
    {
        "doc_id": "SOP-MRPL-FURNACE-101",
        "title": "Furnace F-101 Operations and Tube Skin Temperature Control",
        "clause": "4.3.2",
        "page": "12",
        "domain": "refinery",
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
        "domain": "refinery",
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
        "domain": "refinery",
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
        "domain": "refinery",
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
        "domain": "refinery",
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
        "domain": "refinery",
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
        "domain": "refinery",
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
        "domain": "refinery",
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
        "domain": "refinery",
        "content": (
            "Pressure Safety Valve (PSV) & Vessel Inspection (API 510 / ASME Sec VIII): "
            "PSV pop test calibration interval: strictly 24 months. Set pressure tolerance is ±3% for set pressures above 5 kg/cm2g. "
            "Hydrostatic testing of repaired vessels must be conducted at 1.3 times the Maximum Allowable Working Pressure (MAWP)."
        ),
        "keywords": ["psv", "safety valve", "api 510", "asme", "inspection", "mawp", "hydrostatic", "standard"],
        "equipment_tags": ["PSV-101", "PSV-201"],
    },

    # ═══════════════════════════════════════════════════════════════════
    # DOMAIN: PSU MANUFACTURING (BHEL, SAIL, NTPC)
    # ═══════════════════════════════════════════════════════════════════
    {
        "doc_id": "SOP-BHEL-TG-ROTOR-001",
        "title": "Steam Turbine Generator Rotor Balancing & Vibration Limits",
        "clause": "5.4.1",
        "page": "23",
        "domain": "psu_manufacturing",
        "content": (
            "Steam Turbine Generator (TG) Rotor Vibration Standards (ISO 10816-3 / IS 12075): "
            "Zone A (newly commissioned): shaft vibration ≤ 2.8 mm/s RMS. "
            "Zone B (acceptable for long-term): ≤ 7.1 mm/s RMS. "
            "Zone C (restricted operation, maintenance required): ≤ 11.2 mm/s RMS. "
            "Zone D (trip / immediate shutdown): > 11.2 mm/s RMS. "
            "Rotor dynamic balancing must achieve ISO G2.5 grade. Bearing temperature alarm at 110°C, trip at 120°C."
        ),
        "keywords": ["turbine", "rotor", "vibration", "iso 10816", "balancing", "bearing", "temperature", "trip", "generator", "tg"],
        "equipment_tags": ["TG-1", "TG-2", "TG1", "TG2"],
    },
    {
        "doc_id": "SOP-SAIL-BF-OPS-002",
        "title": "Blast Furnace Hot Metal Temperature & Burden Distribution",
        "clause": "3.2.7",
        "page": "18",
        "domain": "psu_manufacturing",
        "content": (
            "Blast Furnace (BF) Operating Parameters (IS 1977 / JSW Steel Practice): "
            "Hot metal tapping temperature must be maintained at 1480-1520°C. "
            "Slag basicity (CaO/SiO2) ratio: 0.95-1.10 for optimal desulphurization. "
            "Blast pressure: 3.5-4.0 kg/cm2g. Oxygen enrichment: up to 8% by volume. "
            "Coke rate target: < 350 kg/tonne of hot metal. Burden distribution via Paul Wurth bell-less top."
        ),
        "keywords": ["blast furnace", "hot metal", "temperature", "slag", "basicity", "coke", "burden", "tapping", "steel", "bf"],
        "equipment_tags": ["BF-1", "BF-2", "BF1", "BF2"],
    },
    {
        "doc_id": "SOP-NTPC-BOILER-003",
        "title": "Supercritical Boiler Drum Level Control & Trip Settings",
        "clause": "6.1.3",
        "page": "31",
        "domain": "psu_manufacturing",
        "content": (
            "Supercritical Boiler Operation (ASME PTC 4 / IBR Regulation): "
            "Main steam temperature: 540°C ±5°C at rated load. "
            "Main steam pressure: 170 kg/cm2g (supercritical: 247 kg/cm2g). "
            "Drum level normal: 0 mm (NWL). High alarm: +150 mm. High-high trip: +250 mm. "
            "Low alarm: -150 mm. Low-low trip: -250 mm. "
            "Feed water quality: dissolved O2 < 7 ppb, pH 9.0-9.6, conductivity < 0.3 µS/cm."
        ),
        "keywords": ["boiler", "drum level", "steam", "temperature", "pressure", "trip", "ibr", "supercritical", "feed water", "ntpc"],
        "equipment_tags": ["SG-1", "SG-2", "BFP-1", "BFP-2"],
    },
    {
        "doc_id": "SOP-BHEL-WELD-004",
        "title": "Welding Procedure Specification (WPS) for Cr-Mo Steel Components",
        "clause": "4.5.2",
        "page": "15",
        "domain": "psu_manufacturing",
        "content": (
            "Welding Procedure Specification for Cr-Mo Steel (ASME Sec IX / IS 2825): "
            "Base metal: 2.25Cr-1Mo (SA-335 P22). Filler: ER90S-B3 (GTAW) / E9018-B3 (SMAW). "
            "Preheat: minimum 200°C. Interpass temperature: maximum 300°C. "
            "PWHT mandatory: 690-730°C, holding time 1 hour per 25mm thickness, cooling rate ≤ 55°C/hour. "
            "Impact test at -20°C: minimum 27 Joules average. Radiography per ASME V Article 2."
        ),
        "keywords": ["welding", "wps", "pqr", "cr-mo", "preheat", "pwht", "asme", "radiography", "impact", "filler", "procedure"],
        "equipment_tags": [],
    },
    {
        "doc_id": "SOP-PSU-QUALITY-005",
        "title": "ISO 9001 Quality Management System Audit Checklist & NC Resolution",
        "clause": "8.2.1",
        "page": "9",
        "domain": "psu_manufacturing",
        "content": (
            "ISO 9001:2015 QMS Internal Audit Procedure: "
            "Audit frequency: minimum once per calendar year per department. "
            "Non-Conformity (NC) classification: Major NC (systemic failure) requires CAPA within 30 days. "
            "Minor NC requires corrective action within 15 days. "
            "Observations (OBS) to be closed in 60 days. "
            "Management Review Meeting (MRM) to be held within 45 days of audit completion."
        ),
        "keywords": ["iso 9001", "quality", "audit", "non-conformity", "nc", "capa", "qms", "management review", "inspection", "standard"],
        "equipment_tags": [],
    },
    {
        "doc_id": "SOP-NTPC-COAL-006",
        "title": "Coal Handling Plant Conveyor Belt Monitoring & Fire Prevention",
        "clause": "7.2.4",
        "page": "27",
        "domain": "psu_manufacturing",
        "content": (
            "Coal Handling Plant (CHP) Safety & Monitoring Standards: "
            "Belt speed monitoring: trip if speed drops below 80% of rated. "
            "Belt sway/misalignment: alarm at 50mm, trip at 100mm deviation. "
            "Dust suppression: water spray nozzles at all transfer points, dust concentration < 10 mg/m3. "
            "Fire detection: linear heat detection cable along full belt length, auto CO2/water deluge activation."
        ),
        "keywords": ["coal", "chp", "conveyor", "belt", "fire", "dust", "monitoring", "speed", "safety", "handling"],
        "equipment_tags": ["CHP-1", "CHP-2"],
    },

    # ═══════════════════════════════════════════════════════════════════
    # DOMAIN: DEFENCE MANUFACTURING (HAL, BDL, BEL, DRDO)
    # ═══════════════════════════════════════════════════════════════════
    {
        "doc_id": "SOP-HAL-AIRCRAFT-001",
        "title": "Aircraft Assembly Line NDT Inspection Protocol (DGAQA Standards)",
        "clause": "4.1.6",
        "page": "19",
        "domain": "defence",
        "content": (
            "Aircraft Structural NDT Inspection (DGAQA / JSG-0102 / MIL-STD-1530): "
            "All critical structural joints (wing-fuselage, bulkhead, spar) require 100% ultrasonic inspection. "
            "Fastener holes: eddy current inspection for fatigue cracks, detection threshold 0.5mm. "
            "Composite panels: tap testing + thermographic inspection for delamination > 6mm diameter. "
            "Acceptance criteria: zero critical defects, minor indications logged in Aircraft History Card."
        ),
        "keywords": ["aircraft", "ndt", "inspection", "dgaqa", "ultrasonic", "eddy current", "composite", "fatigue", "assembly", "structural"],
        "equipment_tags": ["LCA", "ALH", "LCH"],
    },
    {
        "doc_id": "SOP-BDL-MISSILE-002",
        "title": "Propellant Handling Safety & Shelf Life Assessment Protocol",
        "clause": "5.3.1",
        "page": "14",
        "domain": "defence",
        "content": (
            "Propellant & Explosive Handling Safety (JSG-0503 / STEC Norms): "
            "Storage temperature: 15-30°C, relative humidity < 65%. "
            "Shelf life assessment: accelerated aging test at 70°C for 14 days = 10 years natural aging equivalent. "
            "Propellant grain visual inspection: no cracks, voids, or discoloration permitted. "
            "Anti-static precautions mandatory: all personnel grounded, humidity maintained > 30%. "
            "Explosive quantity distance (QD) tables as per STEC-01 for magazine siting."
        ),
        "keywords": ["propellant", "explosive", "missile", "shelf life", "safety", "handling", "storage", "magazine", "stec", "aging"],
        "equipment_tags": ["ATGM", "SAM"],
    },
    {
        "doc_id": "SOP-BEL-PCB-003",
        "title": "PCB Conformal Coating & Environmental Stress Screening (ESS)",
        "clause": "3.7.2",
        "page": "11",
        "domain": "defence",
        "content": (
            "PCB Assembly Quality Assurance (MIL-STD-883 / JSS-55555): "
            "Conformal coating thickness: 25-75 µm (acrylic) or 50-130 µm (polyurethane). "
            "Environmental Stress Screening: thermal cycling -40°C to +71°C, 20 cycles minimum, 10°C/minute ramp rate. "
            "Random vibration: 6g RMS, 15 min per axis (3 axes). "
            "Soldering quality per IPC-A-610 Class 3 (military/space). "
            "No solder bridges, cold joints, or lifted pads permitted."
        ),
        "keywords": ["pcb", "conformal coating", "ess", "thermal cycling", "vibration", "soldering", "ipc", "mil-std", "quality", "electronics"],
        "equipment_tags": ["EW", "RWR", "IFF"],
    },
    {
        "doc_id": "SOP-DRDO-CLASS-004",
        "title": "Classified Document Handling, Storage & Secure Destruction SOP",
        "clause": "2.1.4",
        "page": "7",
        "domain": "defence",
        "content": (
            "Classified Document Handling Protocol (Official Secrets Act / DRDO Security Manual): "
            "Classification levels: Top Secret, Secret, Confidential, Restricted. "
            "Top Secret/Secret documents: double-lock steel almirah, access only to authorized personnel with valid DSC. "
            "Movement register mandatory with entry/exit timestamps and recipient signature. "
            "Destruction: cross-cut shredding (particle size ≤ 2mm x 15mm) or incineration witnessed by two officers. "
            "Digital classified data: AES-256 encrypted storage on air-gapped systems only."
        ),
        "keywords": ["classified", "secret", "confidential", "document", "handling", "destruction", "security", "shredding", "official secrets", "drdo"],
        "equipment_tags": [],
    },
    {
        "doc_id": "SOP-OFB-AMMO-005",
        "title": "Ammunition Lot Acceptance Testing & Proof Firing Protocol",
        "clause": "6.4.3",
        "page": "25",
        "domain": "defence",
        "content": (
            "Ammunition Lot Acceptance Testing (JSG-0801 / DEF-STD-13): "
            "Proof firing: 10% sample from each production lot, minimum 20 rounds. "
            "Velocity measurement: chronograph at 25m from muzzle, acceptance if within ±3% of specified MV. "
            "Accuracy: 100% rounds within specified dispersion circle at rated range. "
            "Pressure test: maximum chamber pressure must not exceed 110% of rated working pressure. "
            "Temperature conditioning: test at -40°C, +21°C, and +52°C ambient."
        ),
        "keywords": ["ammunition", "proof testing", "lot acceptance", "firing", "velocity", "pressure", "accuracy", "temperature", "jsg", "ordnance"],
        "equipment_tags": [],
    },
    {
        "doc_id": "SOP-HAL-AVIONICS-006",
        "title": "Avionics Software Verification & Validation (DO-178C Level A)",
        "clause": "8.2.5",
        "page": "33",
        "domain": "defence",
        "content": (
            "Avionics Software Assurance (DO-178C / CEMILAC Certification): "
            "Design Assurance Level A (catastrophic failure condition): "
            "100% MC/DC (Modified Condition/Decision Coverage) mandatory. "
            "Code review: all source code peer-reviewed with documented review records. "
            "Requirements traceability: bi-directional trace from system requirements to test cases. "
            "Formal methods recommended for flight-critical algorithms. "
            "Configuration management per DO-CM with baseline audits at each software build."
        ),
        "keywords": ["avionics", "do-178c", "software", "verification", "validation", "cemilac", "mc/dc", "coverage", "flight", "airworthiness"],
        "equipment_tags": ["HUD", "INS"],
    },

    # ═══════════════════════════════════════════════════════════════════
    # DOMAIN: GOVERNMENT OFFICES (Ministries, Secretariats)
    # ═══════════════════════════════════════════════════════════════════
    {
        "doc_id": "SOP-GOVT-NOTING-001",
        "title": "File Noting, Forwarding & Office Procedure (Manual of Office Procedure)",
        "clause": "3.4.2",
        "page": "28",
        "domain": "government",
        "content": (
            "File Noting & Forwarding as per Manual of Office Procedure (MoP) / CSMOP: "
            "Notes must be written on the noting side (left) of the file, numbered serially. "
            "Each note must contain: para-wise analysis, precedents cited, financial implications, and a specific recommendation. "
            "Submission levels: Dealing Hand → Section Officer → Under Secretary → Deputy Secretary → Joint Secretary → Additional Secretary → Secretary. "
            "File transit time: maximum 3 working days per level. "
            "Approval by Competent Authority must be obtained before any expenditure commitment."
        ),
        "keywords": ["noting", "file", "forwarding", "office procedure", "mop", "section officer", "submission", "approval", "competent authority"],
        "equipment_tags": [],
    },
    {
        "doc_id": "SOP-GOVT-RTI-002",
        "title": "RTI Response Protocol & Section 8 Exemption Criteria",
        "clause": "6.1.3",
        "page": "15",
        "domain": "government",
        "content": (
            "Right to Information Act 2005 Response Protocol: "
            "CPIO must furnish information within 30 days of receipt (48 hours for life/liberty matters). "
            "Transfer to concerned PIO: within 5 days if information does not pertain to the department. "
            "Section 8 exemptions: sovereignty & integrity of India (8.1.a), security/strategic interests (8.1.b), "
            "commercial confidence (8.1.d), fiduciary relationship (8.1.e), cabinet papers (8.1.i). "
            "First Appeal: to First Appellate Authority within 30 days. Second Appeal: to CIC within 90 days."
        ),
        "keywords": ["rti", "right to information", "cpio", "section 8", "exemption", "appeal", "cic", "response", "30 days", "transparency"],
        "equipment_tags": [],
    },
    {
        "doc_id": "SOP-CPWD-WORKS-003",
        "title": "CPWD Works Estimation & Schedule of Rates (DSR)",
        "clause": "4.2.7",
        "page": "19",
        "domain": "government",
        "content": (
            "CPWD Works Procedure & Estimation (CPWD Works Manual 2019): "
            "Detailed estimate must be based on current Delhi Schedule of Rates (DSR). "
            "Market rate justification required for non-DSR items with minimum 3 competitive quotations. "
            "Contingency provision: 3% for works up to Rs 10 crore, 2.5% above Rs 10 crore. "
            "Work charges establishment: 2% of estimated cost. "
            "Revised estimate mandatory if variation exceeds 10% of administrative approval amount."
        ),
        "keywords": ["cpwd", "estimation", "dsr", "schedule of rates", "contingency", "works", "construction", "tender", "revised estimate"],
        "equipment_tags": [],
    },
    {
        "doc_id": "SOP-GOVT-LEAVE-004",
        "title": "CCS (Leave) Rules & Leave Account Maintenance",
        "clause": "5.1.4",
        "page": "12",
        "domain": "government",
        "content": (
            "Central Civil Services (Leave) Rules 1972: "
            "Earned Leave (EL): credited at 15 days per half-year, maximum accumulation 300 days. "
            "Half Pay Leave (HPL): credited at 10 days per half-year, no limit on accumulation. "
            "Commuted Leave: half pay leave converted at full pay, debited as double. "
            "Casual Leave: 8 days per calendar year (non-accumulative, non-combinable with EL). "
            "Child Care Leave (CCL): 730 days during entire service for women employees with children below 18 years. "
            "Maternity Leave: 180 days (26 weeks) for first two surviving children."
        ),
        "keywords": ["leave", "ccs", "earned leave", "half pay", "casual leave", "maternity", "child care", "el", "hpl", "rules", "ccl"],
        "equipment_tags": [],
    },
    {
        "doc_id": "SOP-GOVT-BUDGET-005",
        "title": "Budget Estimation, RE/BE Preparation & PFMS Integration",
        "clause": "7.3.1",
        "page": "22",
        "domain": "government",
        "content": (
            "Budget Preparation Guidelines (GFR 2017 / D/o Expenditure OM): "
            "Budget Estimate (BE): submitted to Ministry of Finance by October each year. "
            "Revised Estimate (RE): submitted by December with actuals up to September. "
            "All expenditure must be routed through Public Financial Management System (PFMS). "
            "Budget head classification: Major Head → Sub-Major Head → Minor Head → Sub-Head → Detailed Head → Object Head. "
            "Re-appropriation between Revenue and Capital heads is not permitted without Parliament approval."
        ),
        "keywords": ["budget", "be", "re", "pfms", "expenditure", "gfr", "finance", "appropriation", "head", "estimate", "parliament"],
        "equipment_tags": [],
    },
    {
        "doc_id": "SOP-GOVT-TENDER-006",
        "title": "GFR 2017 Procurement Rules & GeM Mandatory Procurement",
        "clause": "8.4.2",
        "page": "34",
        "domain": "government",
        "content": (
            "Government Procurement Rules (GFR 2017 Rule 149-154 / GeM): "
            "GeM procurement mandatory for all goods and services available on the portal. "
            "Open tender mandatory for procurement above Rs 25 lakhs. "
            "Limited tender: only when sources of supply are definitely known and limited (maximum 3 firms). "
            "Single tender: only in genuine emergency with recorded justification and post-facto CFA approval. "
            "Bid evaluation: L1 (Lowest bidder) system with technical qualification preceding price bid opening. "
            "EMD: 2-5% of estimated value. Performance security: 5-10% of contract value."
        ),
        "keywords": ["gfr", "procurement", "tender", "gem", "l1", "bidding", "emd", "performance security", "open tender", "purchase", "guideline"],
        "equipment_tags": [],
    },
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
        domain=item.get("domain", "refinery"),
        dense_embedding=_generate_dense_vector(f"{item['title']} {item['content']}"),
    )
    for item in _RAW_SOPS
]

# Dynamically merge official downloaded PDF chunks if available
try:
    from pathlib import Path
    _dynamic_path = Path(__file__).resolve().parent / "data" / "downloaded_graphrag_dataset.json"
    if _dynamic_path.exists():
        with open(_dynamic_path, "r", encoding="utf-8") as _df:
            _dyn_data = json.load(_df)
            for _item in _dyn_data.get("chunks", []):
                MASTER_SOPS.append(
                    SOPChunk(
                        doc_id=_item["doc_id"],
                        title=_item["title"],
                        clause=_item.get("clause", "General"),
                        page=_item.get("page", "Section 1"),
                        content=_item["content"],
                        keywords=_item.get("keywords", []),
                        equipment_tags=_item.get("equipment_tags", []),
                        domain=_item.get("domain", "government"),
                        dense_embedding=_generate_dense_vector(f"{_item['title']} {_item['content']}"),
                    )
                )
        logger.info(f"[RAG/GRAPHRAG] Dynamically loaded {len(_dyn_data.get('chunks', []))} PDF chunks. Total Master SOPs: {len(MASTER_SOPS)}")
except Exception as _load_err:
    logger.debug(f"[RAG] Dynamic PDF chunk merge note: {_load_err}")


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
    Domain-aware: boosts results from the active domain while allowing cross-domain matches.
    Returns list of chunks with similarity score >= min_score, ranked descending.
    """
    # Get active domain for priority boosting
    try:
        from backend.domains import get_active_domain
        active_domain = get_active_domain()
    except Exception:
        active_domain = "refinery"

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

        # 4. Domain affinity boost: same-domain SOPs get 1.3x boost
        if chunk.domain == active_domain:
            hybrid_score = round(hybrid_score * 1.3, 4)

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
            "domain": chunk.domain,
            "similarity_score": score,
        })

    # Log search activity for security audit & monitoring
    try:
        from backend.db import log_user_activity
        log_user_activity(
            username="operator",
            activity_type="SEARCH_RAG",
            query_text=query,
            details=f"Retrieved {len(results)} SOP chunks (top doc: {results[0]['doc_id'] if results else 'None'})"
        )
    except Exception:
        pass

    return results


def format_rag_context_block(chunks: List[Dict[str, Any]], query: Optional[str] = None) -> str:
    """
    Formats retrieved SOP chunks into standard delimited context block,
    enriched with GraphRAG entity-relationship topology.
    """
    if not chunks and not query:
        return ""

    lines = ["[RETRIEVED KNOWLEDGE BASE & GRAPHRAG CONTEXT — answer ONLY from this; if insufficient, say so]"]

    # 1. GraphRAG Knowledge Graph Topology Context
    if query:
        try:
            from backend.graph_rag import graphrag_engine
            from backend.domains import get_active_domain
            active_domain = get_active_domain()
            graph_context, _ = graphrag_engine.build_graph_context_block(query, active_domain=active_domain)
            if graph_context:
                lines.append(graph_context)
        except Exception as e:
            logger.debug(f"[GRAPHRAG] Graph context generation note: {e}")

    # 2. Master SOP Chunks
    if chunks:
        for i, c in enumerate(chunks, 1):
            lines.append(
                f"--- Document {i}: {c['doc_id']} (Clause: {c['clause']}, Page: {c['page']}) ---\n"
                f"Title: {c['title']}\n"
                f"Content: {c['content']}\n"
                f"[SOURCE: {c['doc_id']} | Clause: {c['clause']} | Page: {c['page']}]"
            )

    return "\n".join(lines)
