"""
Dataset Generator for Air-Gapped Multi-Domain Sovereign AI Workbench.
Generates authentic markdown and JSON documents for:
1. Oil Refineries & Upstream E&P (MRPL/ONGC/OISD)
2. PSU Heavy Engineering & Manufacturing (BHEL/SAIL/NTPC/IS/ISO)
3. Defence Manufacturing & Strategic Units (DRDO/HAL/DAP 2020/DGAQA)
4. Government Offices & Secretariat (CSMOP/GFR 2017/RTI 2005)
"""

import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "backend" / "data"
DOCS_DIR = BASE_DIR / "sample_docs"

DATA_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)

for sub in ["refinery", "psu_manufacturing", "defence", "government"]:
    (DOCS_DIR / sub).mkdir(parents=True, exist_ok=True)

DATASET = {
    "refinery": [
        {
            "doc_id": "SOP-OISD-105-PTW",
            "domain": "refinery",
            "title": "OISD-STD-105: Work Permit System & Safety Lockout Procedure",
            "clause": "Clause 4.2 - Hot Work & Confined Space Entry",
            "page": "Page 12-16",
            "keywords": ["ptw", "permit to work", "hot work", "cold work", "confined space", "loto", "oisd-std-105", "gas test", "oxygen", "lel", "h2s"],
            "equipment_tags": ["PTW-01", "CS-004", "F-101", "P-101A"],
            "content": (
                "OISD-STD-105 specifies strict regulatory guidelines for Permit to Work (PTW) across Indian hydrocarbon installations. "
                "1. Hot Work Permit is mandatory for any open-flame, welding, cutting, grinding, or spark-generating activity within battery limits. "
                "2. Gas Testing Protocol: Mandatory multi-gas testing must verify: Oxygen between 19.5% and 23.5% v/v, Combustible gas/vapor (LEL) = 0.0%, "
                "and toxic gas concentration (H2S < 10 ppm, Benzene < 0.02 ppm, CO < 25 ppm) prior to permit issuance. "
                "3. Hot Work permits remain valid for a maximum of 8 hours (single shift) and require mandatory re-validation by Shift In-Charge. "
                "4. Fire watch with charged 10 kg DCP fire extinguisher and pressurized fire water hose is mandatory within 15 meters."
            )
        },
        {
            "doc_id": "SOP-MRPL-CDU-VDU-001",
            "domain": "refinery",
            "title": "Crude Distillation Unit (CDU-1) Atmospheric Column Operating Guidelines",
            "clause": "Operating Manual Sec 3.1",
            "page": "Page 24-28",
            "keywords": ["cdu", "atmospheric tower", "crude distillation", "reflux", "furnace f-101", "skin temperature", "naphtha", "kerosene", "diesel"],
            "equipment_tags": ["C-101", "F-101", "P-101A", "P-101B", "V-102"],
            "content": (
                "Crude Distillation Unit (CDU-1) Operating Manual parameters for Arab Light / High Sulphur crude blend: "
                "1. Atmospheric Distillation Tower (C-101) Top Temperature must be controlled between 110°C and 118°C. "
                "2. Top Operating Pressure is maintained at 1.45 to 1.60 kg/cm²g using overhead reflux drum (V-102) split-range pressure controller. "
                "3. Furnace F-101 Fired Heater: Coil Outlet Temperature (COT) setpoint is 358°C (Max COT 365°C). "
                "4. Furnace Tube Skin Temperature: Maximum allowable tube skin temperature for Cr-Mo tubes is 420°C. Alarms activate at 405°C. "
                "5. Heavy Naphtha cut-point 140°C-175°C, Kerosene/ATF cut-point 175°C-240°C, Gas Oil (HSD) cut-point 240°C-360°C."
            )
        },
        {
            "doc_id": "SOP-MRPL-PUMP-ISO-10816",
            "domain": "refinery",
            "title": "Mechanical Reliability Standard: Centrifugal Pump Vibration & Bearing Monitoring",
            "clause": "Standard ISO 10816-3 & API 610",
            "page": "Page 8-11",
            "keywords": ["vibration", "centrifugal pump", "iso 10816", "bearing temperature", "p-101a", "rms velocity", "unbalance", "misalignment"],
            "equipment_tags": ["P-101A", "P-101B", "P-202A", "P-301"],
            "content": (
                "Vibration Velocity Severity criteria as per ISO 10816-3 (Rigid Foundation, Group 1/2 Industrial Machines): "
                "1. Zone A (Newly Commissioned / Good): Overall vibration RMS velocity < 2.3 mm/s. "
                "2. Zone B (Acceptable for Long-term Operation): 2.3 mm/s to 4.5 mm/s RMS. "
                "3. Zone C (Warning / Alert Limit): 4.5 mm/s to 7.1 mm/s RMS — schedule vibration spectral analysis (1X unbalance, 2X misalignment, blade pass). "
                "4. Zone D (Danger / Immediate Shutdown Trip): > 7.1 mm/s RMS. "
                "5. Bearing Housing Temperature: Maximum allowable bearing metal temp is 85°C (185°F). Alarm set at 75°C."
            )
        },
        {
            "doc_id": "SOP-API-510-VESSELS",
            "domain": "refinery",
            "title": "API 510: Pressure Vessel Inspection Code & Corrosion Allowance",
            "clause": "API 510 Section 7.1",
            "page": "Page 45-49",
            "keywords": ["api 510", "pressure vessel", "inspection", "corrosion rate", "minimum thickness", "ultrasonic", "utm", "hydrotest"],
            "equipment_tags": ["V-101", "V-102", "C-101", "D-201"],
            "content": (
                "API 510 defines the in-service inspection, repair, alteration, and re-rating of pressure vessels: "
                "1. Remaining Life Calculation: Remaining Life = (t_actual - t_required) / Corrosion Rate (mm/year). "
                "2. Short-term Corrosion Rate: Cr = (t_previous - t_actual) / time elapsed between inspections. "
                "3. Inspection Intervals: Internal or on-stream inspection interval shall not exceed one-half the remaining life of the vessel or 10 years, whichever is less. "
                "4. If remaining life is less than 4 years, inspection interval is full remaining life up to maximum 2 years. "
                "5. Pressure Safety Valve (PSV) pop testing interval for clean service is 5 years; for corrosive/dirty hydrocarbon service is 3 years."
            )
        },
        {
            "doc_id": "SOP-ONGC-WELL-001",
            "domain": "refinery",
            "title": "ONGC Standard Well Engineering & Blowout Preventer (BOP) Test Procedures",
            "clause": "Drilling Manual Vol 2 Sec 4",
            "page": "Page 88-92",
            "keywords": ["bop", "blowout preventer", "drilling", "well control", "mud weight", "hydrostatic pressure", "annular", "pipe rams"],
            "equipment_tags": ["BOP-01", "RIG-SB-04", "WELL-14"],
            "content": (
                "ONGC Deep Drilling & Well Engineering Standard Operating Procedures: "
                "1. Hydrostatic Pressure Formula: P_hydrostatic (psi) = 0.052 * Mud Weight (ppg) * True Vertical Depth TVD (ft). "
                "2. BOP Pressure Testing Schedule: Low pressure test at 250-300 psi for 5 minutes, followed by High pressure test to maximum rated working pressure (5,000 / 10,000 psi) for 10 minutes. "
                "3. BOP testing frequency: Prior to drilling out casing shoe, after any disconnect of wellhead seals, and every 14 or 21 days maximum during active drilling. "
                "4. Kick Detection: Immediate shut-in mandatory if active pit volume increases by > 10 barrels or flow rate out exceeds flow rate in during circulation."
            )
        }
    ],
    "psu_manufacturing": [
        {
            "doc_id": "SOP-PSU-TURBINE-001",
            "domain": "psu_manufacturing",
            "title": "BHEL / NTPC 500MW/660MW Supercritical Steam Turbine Operational Limits & Vibration Baseline",
            "clause": "TG-OPS-STD-03",
            "page": "Page 18-22",
            "keywords": ["turbine", "steam turbine", "bhel", "ntpc", "rotor vibration", "bearing", "heat rate", "critical speed", "supercritical"],
            "equipment_tags": ["TG-501", "TG-01", "BFP-01", "CEP-02"],
            "content": (
                "Supercritical & Subcritical Steam Turbine (TG-501) Engineering Specifications: "
                "1. Shaft Vibration Limits as per ISO 7919-2 / ISO 10816: Normal steady operation < 45 micrometers peak-to-peak. Alarm at 80 micrometers. Trip setpoint at 120 micrometers. "
                "2. Bearing Metal Temperature: Normal operating temperature is 65°C to 80°C. Alarm threshold is 95°C; emergency auto-trip threshold is 105°C. "
                "3. Turbine Barring Gear (Turning Gear): Mandatory engagement at 120-150 RPM during cooldown until HP casing inner metal temperature drops below 150°C to prevent rotor bowing. "
                "4. Heat Rate: Design Gross Turbine Heat Rate (GTHR) for 660MW Supercritical unit is 1,840 kcal/kWh at 247 kg/cm² main steam pressure and 565°C / 593°C reheat temperature."
            )
        },
        {
            "doc_id": "SOP-PSU-BOILER-002",
            "domain": "psu_manufacturing",
            "title": "Indian Boiler Regulations (IBR 1950) & Master Fuel Trip (MFT) Interlock Logic",
            "clause": "IBR Regulation 382 & ASME Sec I",
            "page": "Page 34-39",
            "keywords": ["boiler", "ibr 1950", "drum level", "mft", "master fuel trip", "furnace pressure", "safety valve", "bhel"],
            "equipment_tags": ["SG-01", "APH-01", "FD-01", "ID-01"],
            "content": (
                "High Pressure Utility Boiler Safety Interlocks under Indian Boiler Regulations (IBR 1950): "
                "1. Boiler Drum Level Protection: Normal water level (NWL) is 0 mm. High-High trip (+200 mm above NWL) and Low-Low trip (-200 mm below NWL) trigger instantaneous Master Fuel Trip (MFT). "
                "2. Furnace Draft / Pressure Protection: Furnace pressure High-High (+120 mmWC) or Low-Low (-120 mmWC) initiates MFT to prevent structural implosion or rupture. "
                "3. Loss of Both Induced Draft (ID) Fans or Both Forced Draft (FD) Fans trips fuel supply immediately within 0.5 seconds. "
                "4. Boiler Safety Valves: Set pressure tolerance is +/- 1% for design pressures over 50 kg/cm². Safety valves must relieve 100% maximum continuous rating (MCR) without pressure rising > 6% over design."
            )
        },
        {
            "doc_id": "SOP-PSU-GEM-GFR-003",
            "domain": "psu_manufacturing",
            "title": "Public Procurement, GeM Evaluation & GFR 2017 Commercial Guidelines for PSUs",
            "clause": "Manual for Procurement of Goods Sec 5.2",
            "page": "Page 56-62",
            "keywords": ["gem", "tender", "gfr 2017", "public procurement", "l1 evaluation", "make in india", "msme", "earnest money", "bg"],
            "equipment_tags": ["GEM-BID-01", "PO-PSU-99"],
            "content": (
                "General Financial Rules (GFR 2017) and Government e-Marketplace (GeM) Tender Evaluation Procedure: "
                "1. Determination of L1 (Lowest Evaluated Techno-Commercially Responsive Bidder): Comparative Statement must calculate total landed cost including basic price, freight, transit insurance, and GST less applicable Input Tax Credit (ITC). "
                "2. Public Procurement (Preference to Make in India) Order: Class-I Local Suppliers (local content >= 50%) receive purchase preference within a margin of 20% over L1 if L1 is not a Class-I supplier. "
                "3. Micro and Small Enterprises (MSEs): MSE bidders quoting price within price band of L1 + 15% are eligible for supply of 25% of total tender quantity subject to matching L1 price. "
                "4. Performance Security / Bank Guarantee (PBG): Standard PBG is 3% to 5% of contract value valid for 60 days beyond completion of warranty obligations."
            )
        },
        {
            "doc_id": "SOP-PSU-STEEL-004",
            "domain": "psu_manufacturing",
            "title": "SAIL / RINL Blast Furnace & Steel Melting Shop Basicity Control Standard",
            "clause": "IS 2062 & Metallurgy Standard Q-14",
            "page": "Page 15-18",
            "keywords": ["blast furnace", "sail", "steel melting", "basicity", "slag", "is 2062", "hot metal", "desulphurisation"],
            "equipment_tags": ["BF-01", "BOF-02", "CC-01"],
            "content": (
                "Blast Furnace Slag & Metallurgy Quality Guidelines for Structural Steel Production: "
                "1. Slag Basicity Index: Binary Basicity B2 = %CaO / %SiO2 must be strictly maintained between 1.15 and 1.25 for optimal desulphurisation and alkali removal. "
                "2. Hot Metal Temperature at tap hole is maintained at 1,480°C to 1,510°C. Silicon (Si) content target is 0.45% to 0.65%. "
                "3. IS 2062 Structural Steel Grade E250 / E350: Yield Strength minimum 250 MPa / 350 MPa, Tensile Strength 410-530 MPa, Minimum Elongation 23%, and Charpy V-notch impact test at 0°C / -20°C."
            )
        }
    ],
    "defence": [
        {
            "doc_id": "SOP-DEF-DAP-2020-001",
            "domain": "defence",
            "title": "Defence Acquisition Procedure (DAP 2020) - SQR Formulation & Field Evaluation Trials",
            "clause": "DAP 2020 Chapter II Clause 14 & 18",
            "page": "Page 42-49",
            "keywords": ["dap 2020", "sqr", "gsqr", "field evaluation", "trial directive", "dgaqa", "make-i", "make-ii", "iddm"],
            "equipment_tags": ["LCA-MK1", "ALH-D02", "DRG-DEF-401"],
            "content": (
                "Defence Acquisition Procedure (DAP 2020) Staff Qualitative Requirements (SQRs) and Trial Directives: "
                "1. SQR Classification: SQRs must clearly delineate 'Essential Parameters-A' (critical operational capabilities verified during initial Field Evaluation Trials) and 'Essential Parameters-B' (capabilities achievable within agreed developmental milestones). "
                "2. Field Evaluation Trials (FET): Equipment must be tested under User Trial Directives across designated operational environments (Extreme High Altitude, Desert/High Temperature, and Marine/Humid Coastal). "
                "3. Indigenisation Content (IC): Buy (Indian-IDDM) requires minimum 50% indigenous content. Make-I category requires minimum 50% IC; Make-II requires 50% IC with complete design ownership residing in India. "
                "4. Single Bid Scenario: At FET stage, single bid situations require Approval of Competent Financial Authority (CFA) or Defence Acquisition Council (DAC)."
            )
        },
        {
            "doc_id": "SOP-DEF-MIL-810H-002",
            "domain": "defence",
            "title": "MIL-STD-810H: Environmental Engineering Considerations & Laboratory Climatic Trials",
            "clause": "MIL-STD-810H Methods 501.7 & 502.7",
            "page": "Page 74-82",
            "keywords": ["mil-std-810h", "environmental testing", "high temperature", "low temperature", "vibration trial", "salt fog", "defence quality"],
            "equipment_tags": ["SYS-AV-01", "RAD-401", "EW-POD-09"],
            "content": (
                "MIL-STD-810H Environmental Testing Standards for Tactical Defence Electronics & Subsystems: "
                "1. Method 501.7 (High Temperature): Operating temperature qualification between +55°C and +71°C continuous for 48 hours; Storage test at +85°C. "
                "2. Method 502.7 (Low Temperature): Extreme Cold operational testing at -40°C (High Altitude Leh/Ladakh baseline) and -50°C storage. "
                "3. Method 509.7 (Salt Fog Corrosion): 5% NaCl saline atmosphere exposure for 48 hours followed by 48 hours drying, repeated for 4 cycles to qualify coastal/naval installations. "
                "4. Method 514.8 (Random Vibration): Tactical wheeled and tracked vehicle vibration spectral density curve from 10 Hz to 2,000 Hz at 5.4 Grms for 6 hours per axis."
            )
        },
        {
            "doc_id": "SOP-DEF-DGAQA-FAI-003",
            "domain": "defence",
            "title": "DGAQA Quality Assurance & First Article Inspection (FAI) Standard",
            "clause": "DGAQA Document QA-PROC-14",
            "page": "Page 11-15",
            "keywords": ["dgaqa", "first article inspection", "fai", "quality assurance", "aerospace", "hal", "certificate of conformance", "coc"],
            "equipment_tags": ["AIRCRAFT-SU-30", "LCH-001", "DRG-AERO-108"],
            "content": (
                "Directorate General of Aeronautical Quality Assurance (DGAQA) Inspection Standards: "
                "1. First Article Inspection (FAI) per AS9102 / DGAQA protocol is mandatory for new aerospace production batches, major design tooling modifications, or manufacturing location changes. "
                "2. Raw Material Traceability: 100% test certificates with heat number, chemical spectro analysis, and ultrasonic NDT reports must be verified against Mill Test Certificates before machining. "
                "3. Fasteners and Structural Riveting: 100% torque audit and dye penetrant inspection (DPI) records are stamped by DGAQA resident inspector prior to sub-assembly box closure. "
                "4. Certificate of Conformance (CoC): Signed by both Contractor Quality Head and Authorized DGAQA Quality Officer before despatch."
            )
        },
        {
            "doc_id": "SOP-DEF-AIRGAP-SEC-004",
            "domain": "defence",
            "title": "Air-Gap Network Isolation & Sovereign Cryptographic Verification Specification",
            "clause": "MoD Cyber Security Manual Sec 8.4",
            "page": "Page 22-26",
            "keywords": ["air gap", "sovereign", "cybersecurity", "zero egress", "network isolation", "tempest", "cryptographic", "sha256"],
            "equipment_tags": ["SEC-NODE-01", "GPU-SRV-AIRGAP"],
            "content": (
                "Sovereign Air-Gap Network Security & Isolation Criteria for Defence R&D Units: "
                "1. Physical & Logical Air-Gap: Host servers executing sensitive knowledge work must have zero WAN physical uplinks, disabled 802.11 Wi-Fi, Bluetooth, and cellular modems at BIOS/kernel level. "
                "2. Real-time Outbound Socket Guard: Runtime network monitors must enforce 0 bytes egress to external IP addresses. Any non-loopback outbound SYN packet triggers immediate alert and connection termination. "
                "3. Data Deliverables: All generated reports (DOCX, PPTX, XLSX) must be cryptographically hashed using SHA-256 for local audit provenance and non-repudiation. "
                "4. On-Premise GPU Inference: LLM models must run entirely inside workstation VRAM/RAM via local Ollama socket without telemetry or external API calls."
            )
        }
    ],
    "government": [
        {
            "doc_id": "SOP-GOV-CSMOP-2019",
            "domain": "government",
            "title": "Central Secretariat Manual of Office Procedure (CSMOP 2019) - File Handling & Cabinet Note Formulation",
            "clause": "CSMOP Chapter 7 & 11",
            "page": "Page 85-94",
            "keywords": ["csmop", "cabinet note", "inter-ministerial", "secretariat", "office procedure", "approval note", "file numbering", "dopt"],
            "equipment_tags": ["CAB-NOTE-01", "FILE-SEC-2026"],
            "content": (
                "Central Secretariat Manual of Office Procedure (CSMOP 2019) Mandatory Rules: "
                "1. Structure of a Cabinet Note: Every Note for the Cabinet must contain: (a) Statement of Proposal, (b) Background, (c) Inter-Ministerial Consultations with verbatim views of Ministry of Law, Ministry of Finance (Dept of Expenditure) and NITI Aayog, (d) Financial Implications, and (e) Paragraph for Decision (Para for approval). "
                "2. Time Limit for Inter-Ministerial Consultation: Sponsoring Ministry must give 15 working days for comments. If no reply is received within 15 days, concurrence is presumed. "
                "3. Note Page Limit: The main Cabinet Note should not exceed 10 pages; exhaustive data should be placed as Annexures / Appendices. "
                "4. Language and Tone: Impersonal passive third-person formal tone ('The approval of the Cabinet is solicited for...')."
            )
        },
        {
            "doc_id": "SOP-GOV-RTI-2005",
            "domain": "government",
            "title": "Right to Information (RTI) Act 2005 - Disposal Protocol & Section 8/9 Exemptions",
            "clause": "RTI Act 2005 Section 7 & 8",
            "page": "Page 14-19",
            "keywords": ["rti", "rti act 2005", "cpio", "section 8", "exemption", "first appellate", "30 days", "public interest"],
            "equipment_tags": ["RTI-DISP-01", "CPIO-SEC-04"],
            "content": (
                "Right to Information (RTI) Act 2005 Statutory Compliance Guidelines for CPIOs: "
                "1. Timelines for Information Supply: Information must be supplied within 30 days of application receipt (within 48 hours if life or liberty of a person is involved). "
                "2. Exemption from Disclosure under Section 8(1): Information cannot be disclosed if it prejudicially affects: (a) sovereignty and integrity of India, security, strategic scientific or economic interests of the State (Sec 8(1)(a)), (b) commercial confidence, trade secrets or intellectual property (Sec 8(1)(d)), (c) cabinet papers including deliberations of Council of Ministers before decision is taken (Sec 8(1)(i)), or (d) personal information with no public interest (Sec 8(1)(j)). "
                "3. Severability under Section 10: If part of the document is exempt, non-exempt parts must be provided after redacting exempt portions. "
                "4. Mandatory Appellate Details: Every rejection or partial supply letter must contain name, designation, and office address of the First Appellate Authority (FAA) and 30-day appeal timeline."
            )
        },
        {
            "doc_id": "SOP-GOV-GFR-RULE-166",
            "domain": "government",
            "title": "General Financial Rules (GFR 2017) Rule 166: Single Tender Nomination Procurement",
            "clause": "GFR 2017 Rule 166 & 167",
            "page": "Page 48-52",
            "keywords": ["gfr 2017", "rule 166", "single tender", "nomination", "proprietary article", "pac", "public finance"],
            "equipment_tags": ["GFR-RULE-166", "PAC-CERT-01"],
            "content": (
                "General Financial Rules (GFR 2017) Procurement on Nomination / Single Tender Basis (Rule 166): "
                "1. Conditions for Single Tender Enquiry: Procurement without competition is permitted only: (a) It is in the knowledge of the user department that only a particular firm is manufacturer of the required goods (Proprietary Article Certificate - PAC), (b) In case of emergency arising out of natural disasters or security situations, (c) For technical compatibility reasons with existing equipment. "
                "2. Proprietary Article Certificate (PAC): Must be signed by an officer not below the level of Joint Secretary / General Manager certifying that no other make/model is acceptable. "
                "3. Price Reasonableness: On single tender procurement, price reasonableness must be established through cost breakdown audit or comparison with past supplied rates to other government entities."
            )
        },
        {
            "doc_id": "SOP-GOV-CCS-CONDUCT-1964",
            "domain": "government",
            "title": "Central Civil Services (Conduct) Rules 1964: Official Communications & Digital Conduct",
            "clause": "CCS Rules Rule 3 & 11",
            "page": "Page 8-12",
            "keywords": ["ccs conduct", "official secrets act", "government employee", "confidentiality", "conduct rules", "dopt"],
            "equipment_tags": ["CCS-RULE-1964", "GOV-RULE-03"],
            "content": (
                "Central Civil Services (Conduct) Rules 1964 Mandatory Obligations: "
                "1. Rule 3: Every government servant shall at all times maintain absolute integrity, devotion to duty, and do nothing which is unbecoming of a Government servant. "
                "2. Rule 11 (Communication of Official Information): No government employee shall communicate directly or indirectly any official document or classified information to any unauthorized person except in accordance with general or special order of Government. "
                "3. AI and Public Cloud Usage Directive: Classified files, draft cabinet notes, unreleased trade designs, or sensitive government correspondences must NOT be uploaded to public commercial cloud AI tools. Processing must remain strictly on-premises on authorized sovereign hardware."
            )
        }
    ]
}

# 1. Write structured JSON files to backend/data/
master_json_path = DATA_DIR / "enterprise_rag_dataset.json"
with open(master_json_path, "w", encoding="utf-8") as f:
    json.dump(DATASET, f, indent=2)
print(f"Generated master JSON dataset at: {master_json_path}")

for domain, docs in DATASET.items():
    domain_json_path = DATA_DIR / f"sops_{domain}.json"
    with open(domain_json_path, "w", encoding="utf-8") as f:
        json.dump(docs, f, indent=2)
    print(f"Generated {domain} JSON dataset with {len(docs)} documents at: {domain_json_path}")

# 2. Write readable Markdown files to sample_docs/ for direct UI upload and reading
total_md = 0
for domain, docs in DATASET.items():
    for doc in docs:
        doc_filename = f"{doc['doc_id']}.md"
        doc_path = DOCS_DIR / domain / doc_filename
        
        md_content = f"""# {doc['title']}
**Document Reference:** `{doc['doc_id']}` | **Domain:** `{doc['domain'].upper()}`  
**Regulatory Clause:** {doc['clause']} | **Page / Section:** {doc['page']}  
**Equipment Tags:** {', '.join(doc['equipment_tags'])}  
**Keywords:** {', '.join(doc['keywords'])}

---

## Technical & Regulatory Policy Content

{doc['content']}

---

*Verified On-Premises Master Technical Specification — Grounded for Sovereign RAG Indexing.*
"""
        with open(doc_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        total_md += 1

print(f"\nSuccessfully created {total_md} authentic Markdown documents across 4 domain directories in 'sample_docs/'!")
