# Sovereign Industrial AI — Domain Coverage & Test Specification
**Target Industry:** Oil & Gas PSUs / Refineries & Upstream E&P (MRPL & ONGC)  
**Architecture:** Air-Gapped Sovereign AI (FastAPI + Ollama + Local SQLite + Python Sandbox + Deliverable Engine)  
**Document Version:** 2.0.0 | **Last Updated:** 2026-09-06  

---

## Executive Overview
This document provides a comprehensive mapping of operational departments across **Refining & Downstream Petrochemicals** (MRPL style: 15 MMTPA refinery, CDU/VDU, HCU, DHDS, PFCCU, Polypropylene, Aromatics Complex) and **Upstream Exploration & Production** (ONGC style: Drilling, Offshore Platforms, Well Services, Sub-surface, Marine Logistics).

For each department, 10 realistic operator/engineer queries are cataloged, mapped to the system capability required to answer, and marked with their current operational status.

---

## Capability Definitions & Implementation Status

| Capability | Engine / Mechanism | Source of Grounding | Status |
| :--- | :--- | :--- | :--- |
| **Chemical-DB** | Word-boundary regex detector (`backend/chemical_kb.py`) | Verified MSDS & ACGIH JSON (`backend/data/chemical_db.json`) | **IMPLEMENTED** |
| **RAG (Internal SOP)** | Deterministic keyword + dense vector retrieval (`backend/knowledge_base.py`) | Active Master SOP repository (OISD / API / MRPL / ONGC) | **IMPLEMENTED** |
| **Deterministic Fallback** | Guardrail fallback for unindexed internal queries | Exact deterministic compliance notice (Zero hallucination) | **IMPLEMENTED** |
| **Template (Document)** | Structured document planner + Python OpenXML builder | Built-in template registry (`backend/templates.py`) | **IMPLEMENTED** |
| **Calculation (Code)** | Isolated Python sandbox execution (`backend/code_mode.py`) | Verbatim sandbox stdout/stderr with auto-retry | **IMPLEMENTED** |
| **General-Knowledge** | Two-Tier prompt policy (`backend/chat_mode.py`) | General science/definitions with strict numerical guardrails | **IMPLEMENTED** |

---

## Departmental Domain Mapping & Test Specifications

### 1. Operations (Refinery Downstream — CDU / VDU / HCU / PFCCU)
*   **Core Responsibilities:** Continuous crude processing, fractionator stabilization, furnace firing management, desalter operation, catalyst bed temperature control, shift handover, and emergency shutdown management.
*   **Typical Documents:** Shift Handover Log, Daily Production Report (DPR), Unit Operating Logsheet, Startup/Shutdown Checklist.

| # | Sample Operator Query | Required Capability | Implementation Status |
| :--- | :--- | :--- | :--- |
| 1.1 | "CDU shift handover log banao" | Template (Document) | **IMPLEMENTED** (`shift_handover` template + NEEDS_INPUT) |
| 1.2 | "CDU Atmospheric Tower ka top temperature operating limit kya hai?" | RAG (Internal SOP) | **IMPLEMENTED** (Indexed in `SOP-MRPL-CDU-VDU-002`) |
| 1.3 | "Furnace F-101 tube skin temperature max limit kitna hai?" | RAG (Internal SOP) | **IMPLEMENTED** (Indexed in `SOP-MRPL-FURNACE-101`) |
| 1.4 | "F-201 vacuum heater decoking procedure kya hai?" | RAG (Internal SOP) | **IMPLEMENTED** (Indexed in `SOP-MRPL-FURNACE-201`) |
| 1.5 | "F-301 furnace ka burner pressure kitna hona chahiye?" (Unindexed) | Deterministic Fallback | **IMPLEMENTED** (Returns deterministic SOP fallback notice) |
| 1.6 | "What is the principle of fractional distillation?" | General-Knowledge | **IMPLEMENTED** (Tier 2 scientific answer, 2-4 sentences) |
| 1.7 | "Calculate reflux ratio given overhead vapor 120 t/h and distillate 30 t/h" | Calculation (Code) | **IMPLEMENTED** (Runs Python calculation in sandbox) |
| 1.8 | "PFCCU regenerate bed temperature runaway hone pe immediate action kya le?" | RAG (Internal SOP) | **PLANNED** (Needs PFCCU emergency SOP in KB) |
| 1.9 | "LPG wash column caustic circulation check karna hai" | Chemical-DB | **IMPLEMENTED** (Injects NaOH chemical safety profile) |
| 1.10 | "Generate daily production report for Crude Distillation Unit" | Template (Document) | **IMPLEMENTED** (`daily_production_report` template) |

---

### 2. Upstream Drilling Services & Well Engineering (ONGC Style)
*   **Core Responsibilities:** Rigs management, casing design, drilling mud rheology, drill string mechanics, Blowout Preventer (BOP) testing, directional drilling, well control, and Daily Drilling Reports (DDR).
*   **Typical Documents:** Daily Drilling Report (DDR), Well History Report, BOP Test Certificate, Mud Logging Summary.

| # | Sample Operator Query | Required Capability | Implementation Status |
| :--- | :--- | :--- | :--- |
| 2.1 | "Calculate hydrostatic pressure for 10.5 ppg mud at 8,500 ft TVD" | Calculation (Code) | **IMPLEMENTED** (Executes `P = 0.052 * MW * TVD` in sandbox) |
| 2.2 | "What is a Blowout Preventer (BOP) and how does an annular preventer work?" | General-Knowledge | **IMPLEMENTED** (Tier 2 technical definition) |
| 2.3 | "Drilling report template banao for Rig Sagar Bhushan" | Template (Document) | **IMPLEMENTED** (`dpr` template with NEEDS_INPUT) |
| 2.4 | "Deepwater well me methane gas hydrate formation kaise prevent kare?" | Chemical-DB | **IMPLEMENTED** (Injects MEG/Methanol hydrate inhibition data) |
| 2.5 | "H2S presence detected during drilling: immediate wellhead protocol kya hai?" | Chemical-DB + RAG | **IMPLEMENTED** (Injects H2S toxicity limits & SCBA PPE) |
| 2.6 | "ONGC standard mud weight schedule for Cambay basin Well #14" | Deterministic Fallback | **IMPLEMENTED** (Guarded: unindexed well parameter) |
| 2.7 | "Calculate buoyancy factor for 12 ppg drilling mud in steel pipe" | Calculation (Code) | **IMPLEMENTED** (Python calculation sandbox) |
| 2.8 | "Difference between top drive system and rotary table drilling" | General-Knowledge | **IMPLEMENTED** (Tier 2 comparison) |
| 2.9 | "High pressure well acidizing ke liye Formic vs HCl acid compatibility kya hai?" | Chemical-DB | **IMPLEMENTED** (Injects Formic & HCl acid profiles) |
| 2.10 | "Drill stem test (DST) pressure build-up interpretation procedure" | RAG (Internal SOP) | **PLANNED** (Needs ONGC Well Testing SOP in KB) |

---

### 3. Offshore Platforms & Production Facilities (ONGC Style)
*   **Core Responsibilities:** Offshore process platforms (Mumbai High / Neelam / Bassein), oil-gas-water 3-phase separation, TEG gas dehydration, gas compression (HSC/BCP), water injection (WIN), subsea pipeline integrity, helideck operations.
*   **Typical Documents:** Platform Daily Log, Gas Dehydration TEG Analysis, Marine Logistics Manifest, Offshore Safety Induction.

| # | Sample Operator Query | Required Capability | Implementation Status |
| :--- | :--- | :--- | :--- |
| 3.1 | "TEG contactor gas dehydration unit me glycol circulation rate and reboiler temp kya hai?" | Chemical-DB | **IMPLEMENTED** (Injects Triethylene Glycol properties & context) |
| 3.2 | "Offshore process platform 3-phase separator troubleshooting guide" | General-Knowledge | **IMPLEMENTED** (Tier 2 operational explanation) |
| 3.3 | "Offshore Single Point Mooring (SPM) crude loading safety checklist" | RAG (Internal SOP) | **PLANNED** (Needs Marine SPM SOP in KB) |
| 3.4 | "Subsea trunkline mercury contaminant removal guard bed safety" | Chemical-DB | **IMPLEMENTED** (Injects Mercury heavy metal & LME hazards) |
| 3.5 | "Platform emergency evacuation mock drill report draft karo" | Template (Document) | **IMPLEMENTED** (`mock_drill_report` template) |
| 3.6 | "Gas compression platform BCP-B discharge pressure threshold kya hai?" | Deterministic Fallback | **IMPLEMENTED** (Guarded: unindexed platform tag) |
| 3.7 | "Calculate water injection pump flow rate in m3/day from GPM" | Calculation (Code) | **IMPLEMENTED** (Sandbox conversion) |
| 3.8 | "What is an FPSO and how does turret mooring work?" | General-Knowledge | **IMPLEMENTED** (Tier 2 conceptual definition) |
| 3.9 | "Marine logistics OSV vessel chartering approval note banao" | Template (Document) | **IMPLEMENTED** (`approval_note` template) |
| 3.10 | "Sour gas flaring offshore me SO2 emission calculation" | Chemical-DB + Code | **IMPLEMENTED** (Injects SO2 limits + calculates stoich in sandbox) |

---

### 4. Health, Safety & Environment (HSE) & Fire Safety
*   **Core Responsibilities:** Permit to Work (PTW), Lockout/Tagout (LOTO), confined space gas testing, hazardous chemical safety (MSDS), fire protection systems, OISD compliance, effluent treatment & CPCB emissions.
*   **Typical Documents:** Cold/Hot Work Permit, Confined Space Entry Certificate, Incident Investigation Report, Safety Audit Note.

| # | Sample Operator Query | Required Capability | Implementation Status |
| :--- | :--- | :--- | :--- |
| 4.1 | "What is benzene?" | General-Knowledge + Chem-DB | **IMPLEMENTED** (Aromatic C6H6, CAS 71-43-2, TLV 0.02 ppm, Carcinogen) |
| 4.2 | "H2S ka TLV and exposure symptoms?" | Chemical-DB | **IMPLEMENTED** (CAS 7783-06-4, TLV 1 ppm, STEL 5 ppm, knockdown risks) |
| 4.3 | "Permit to Work (PTW) validity and gas testing criteria kya hai?" | RAG (Internal SOP) | **IMPLEMENTED** (Indexed in `SOP-MRPL-HSE-PTW-004`) |
| 4.4 | "Confined space entry ke liye oxygen and toxic gas thresholds?" | RAG (Internal SOP) | **IMPLEMENTED** (Indexed in `SOP-MRPL-HSE-PTW-004`: O2 19.5-23.5%) |
| 4.5 | "Oil spill near storage tank incident report banao" | Template (Document) | **IMPLEMENTED** (`incident_report` template + NEEDS_INPUT) |
| 4.6 | "Hydrofluoric acid (HF) exposure me immediate first aid kya hai?" | Chemical-DB | **IMPLEMENTED** (Injects Calcium Gluconate 2.5% protocol) |
| 4.7 | "Chlorine gas cylinder leak emergency response and PPE" | Chemical-DB | **IMPLEMENTED** (Injects Level A suit, SCBA, TLV 0.1 ppm) |
| 4.8 | "ETP treated effluent discharge limits as per KSPCB/CPCB" | RAG (Internal SOP) | **IMPLEMENTED** (Indexed in `SOP-MRPL-ENV-BRSR-008`: COD/BOD/TSS) |
| 4.9 | "Calculate Fire Water Network replenishment time for 5000 m3 reservoir" | Calculation (Code) | **IMPLEMENTED** (Python calculation sandbox) |
| 4.10 | "What is BLEVE in LPG storage?" | General-Knowledge | **IMPLEMENTED** (Tier 2 safety physics explanation) |

---

### 5. Maintenance (Mechanical, Electrical & Instrumentation)
*   **Core Responsibilities:** Rotating equipment reliability, API 610 centrifugal pump overhauls, vibration analysis, mechanical seal flush plans (API 682), motor control centers (MCC), PLC/DCS calibration, and preventive maintenance.
*   **Typical Documents:** Equipment Breakdown Analysis, PM Work Order, Vibration Survey Log, Calibration Sheet.

| # | Sample Operator Query | Required Capability | Implementation Status |
| :--- | :--- | :--- | :--- |
| 5.1 | "API 610 pump P-101A/B vibration alarm and trip limits kya hai?" | RAG (Internal SOP) | **IMPLEMENTED** (Indexed in `SOP-MRPL-PUMP-610`: 4.5/7.1/9.0 mm/s) |
| 5.2 | "Centrifugal pump breakdown failure analysis report banao" | Template (Document) | **IMPLEMENTED** (`breakdown_analysis` template) |
| 5.3 | "Pump P-205B bearing temperature alarm setting" (Unindexed) | Deterministic Fallback | **IMPLEMENTED** (Deterministic SOP fallback notice) |
| 5.4 | "Mechanical seal flush Plan 11 vs Plan 52 me kya farak hai?" | General-Knowledge | **IMPLEMENTED** (Tier 2 technical engineering comparison) |
| 5.5 | "Compressor K-101 interstage cooler leakage repair SOP" (Unindexed) | Deterministic Fallback | **IMPLEMENTED** (Guarded: unindexed tag) |
| 5.6 | "Calculate centrifugal pump hydraulic power: Flow 250 m3/h, Head 85 m, SG 0.85"| Calculation (Code) | **IMPLEMENTED** (Sandbox Python formula run) |
| 5.7 | "What causes cavitation in industrial pumps?" | General-Knowledge | **IMPLEMENTED** (Tier 2 physics explanation) |
| 5.8 | "Induction motor insulation resistance test (Megger) minimum acceptable value" | General-Knowledge | **IMPLEMENTED** (Tier 2 engineering standard: 1 Mohm/kV + 1) |
| 5.9 | "Control valve FCV-101 pneumatic actuator calibration step-by-step" | RAG (Internal SOP) | **PLANNED** (Needs Instrumentation Calibration SOP in KB) |
| 5.10 | "Nitrogen purging procedure for hydrocarbon pump seal replacement" | Chemical-DB | **IMPLEMENTED** (Injects N2 asphyxiation hazards & purging context) |

---

### 6. Inspection & Condition Monitoring (NDT & Metallurgy)
*   **Core Responsibilities:** Non-destructive testing (UT, RT, MPI, DPT), API 510 pressure vessel inspection, API 570 piping thickness surveys, API 653 storage tank inspection, corrosion probe monitoring, and PSV calibration.
*   **Typical Documents:** Thickness Measurement Report, PSV Pop Test Certificate, Corrosion Rate Survey, Remaining Life Assessment.

| # | Sample Operator Query | Required Capability | Implementation Status |
| :--- | :--- | :--- | :--- |
| 6.1 | "PSV pop test calibration interval and set pressure tolerance as per API 510" | RAG (Internal SOP) | **IMPLEMENTED** (Indexed in `SOP-MRPL-INSP-510`: 24 months, ±3%) |
| 6.2 | "Corrosion monitoring ER probe corrosion rate limit and UT inspection frequency" | RAG (Internal SOP) | **IMPLEMENTED** (Indexed in `SOP-ONGC-CORR-570`: 0.125 mm/yr, 6 months) |
| 6.3 | "F-101 ki inspection frequency kya hai?" (Unindexed inspection SOP) | Deterministic Fallback | **IMPLEMENTED** (Deterministic SOP fallback notice) |
| 6.4 | "Piping ultrasonic thickness measurement inspection report banao" | Template (Document) | **IMPLEMENTED** (`inspection_report` template) |
| 6.5 | "Calculate remaining corrosion life of pipe: current 9.2 mm, min 6.8 mm, rate 0.15 mm/yr" | Calculation (Code) | **IMPLEMENTED** (Sandbox calculation: 16.0 years) |
| 6.6 | "What is High Temperature Hydrogen Attack (HTHA) and Nelson curves?" | General-Knowledge | **IMPLEMENTED** (Tier 2 metallurgy explanation) |
| 6.7 | "Liquid metal embrittlement (LME) of aluminum heat exchangers by mercury" | Chemical-DB | **IMPLEMENTED** (Injects Mercury LME hazards & guard beds) |
| 6.8 | "API 653 tank bottom annular plate minimum thickness criteria" | RAG (Internal SOP) | **PLANNED** (Needs API 653 SOP in KB) |
| 6.9 | "Difference between Ultrasonic Testing (UT) and Radiographic Testing (RT)" | General-Knowledge | **IMPLEMENTED** (Tier 2 NDT comparison) |
| 6.10 | "Hydrostatic test pressure calculation: MAWP 25 kg/cm2g as per ASME Sec VIII" | RAG (Internal SOP) + Code | **IMPLEMENTED** (1.3x MAWP from `SOP-MRPL-INSP-510` -> 32.5 kg/cm2g) |

---

### 7. Quality Control Laboratory (QC Lab)
*   **Core Responsibilities:** Crude assay testing, finished fuel quality certification (BS-VI MS/HSD, ATF Jet A-1), gas chromatography (GC), ASTM distillation, flash point, pour point, sulfur testing, and water content (Karl Fischer).
*   **Typical Documents:** Certificate of Analysis (COA), Lab Test Report, Gas Chromatography Assay, Off-Spec Product Quarantine Notice.

| # | Sample Operator Query | Required Capability | Implementation Status |
| :--- | :--- | :--- | :--- |
| 7.1 | "HSD BS-VI diesel maximum sulfur specification kya hai?" | General-Knowledge | **IMPLEMENTED** (Tier 2 standard: 10 ppm max) |
| 7.2 | "What is Research Octane Number (RON) vs Motor Octane Number (MON)?" | General-Knowledge | **IMPLEMENTED** (Tier 2 fuel chemistry definition) |
| 7.3 | "Aromatics extraction unit me Benzene purity GC test method" | Chemical-DB | **IMPLEMENTED** (Injects Benzene physical/chemical profile) |
| 7.4 | "MTBE gasoline blending additive properties and octane contribution" | Chemical-DB | **IMPLEMENTED** (Injects MTBE CAS 1634-04-4, RON boost context) |
| 7.5 | "ATF Jet A-1 water separation index and freeze point specifications" | Chemical-DB | **IMPLEMENTED** (Injects Aviation Kerosene DEF STAN / IS specs) |
| 7.6 | "Calculate API gravity from Specific Gravity 0.845 at 60°F" | Calculation (Code) | **IMPLEMENTED** (Executes `API = 141.5/SG - 131.5 = 35.96` in sandbox) |
| 7.7 | "What is Reid Vapor Pressure (RVP) in gasoline?" | General-Knowledge | **IMPLEMENTED** (Tier 2 fuel volatility explanation) |
| 7.8 | "Citric acid passivation solution pH range and concentration testing" | Chemical-DB | **IMPLEMENTED** (Injects Citric Acid cleaning profile) |
| 7.9 | "Lab product quality test report for export cargo draft karo" | Template (Document) | **IMPLEMENTED** (`inspection_report` / `dpr` quality sections) |
| 7.10 | "Viscosity Index calculation from kinematic viscosity at 40°C and 100°C" | Calculation (Code) | **IMPLEMENTED** (ASTM D2270 Python script in sandbox) |

---

### 8. Oil Movement & Storage (OM&S / Tank Farm)
*   **Core Responsibilities:** Crude receipt at SPM/jetty, intermediate tank blending, custody transfer metering, finished product dispatch (road tanker, rail gantry, coastal tankers), tank gauging (ullage, water dip), and vapor recovery.
*   **Typical Documents:** Tank Dip Measurement Sheet, Custody Transfer Ticket, Tank Farm Handover Report, Blending Order.

| # | Sample Operator Query | Required Capability | Implementation Status |
| :--- | :--- | :--- | :--- |
| 8.1 | "TK-1002 tank storage transfer log draft karo" | Template (Document) | **IMPLEMENTED** (`shift_handover` with OM&S context) |
| 8.2 | "Calculate gross standard volume (GSV) given dip 12.4m, tank strapping 450 m3/m, VCF 0.985" | Calculation (Code) | **IMPLEMENTED** (Python calculation sandbox) |
| 8.3 | "LPG Horton sphere and mounded bullet safety distance as per OISD-144" | Chemical-DB | **IMPLEMENTED** (Injects LPG BLEVE & deluge requirements) |
| 8.4 | "Bitumen VG-30 storage tank heating temperature requirement" | Chemical-DB | **IMPLEMENTED** (Injects Bitumen heating 140-160°C & boilover hazard) |
| 8.5 | "Heavy Fuel Oil (FO) pipeline pigging and steam tracing guidelines" | Chemical-DB | **IMPLEMENTED** (Injects Heavy Fuel Oil viscosity & heating notes) |
| 8.6 | "What is water bottom draining in crude storage tanks and safety precautions?" | General-Knowledge | **IMPLEMENTED** (Tier 2 safety explanation on static electricity & H2S) |
| 8.7 | "TK-401 floating roof tank secondary seal gap measurement inspection report" | Template (Document) | **IMPLEMENTED** (`inspection_report` template) |
| 8.8 | "Toluene bulk road tanker loading earthing and bonding protocol" | Chemical-DB | **IMPLEMENTED** (Injects Toluene flammability & static earthing) |
| 8.9 | "Custody transfer mass flow meter Coriolis vs turbine meter comparison" | General-Knowledge | **IMPLEMENTED** (Tier 2 instrumentation comparison) |
| 8.10 | "Slop tank skimming and reprocessing operating guideline" | Deterministic Fallback | **IMPLEMENTED** (Guarded fallback for unindexed SOP) |

---

### 9. Materials Management, Procurement & Contracts (GeM & e-MB)
*   **Core Responsibilities:** GeM portal procurement, technical evaluation of tenders, purchase requisitions / indents, inventory stores management, e-Measurement Book (e-MB) recording, contractor compliance (PF/ESIC), and vendor bill clearance.
*   **Typical Documents:** Purchase Indent, Technical Approval Note, e-MB Entry Sheet, Purchase Order Compliance Note.

| # | Sample Operator Query | Required Capability | Implementation Status |
| :--- | :--- | :--- | :--- |
| 9.1 | "GeM procurement and e-MB measurement entry rules as per ONGC SOP" | RAG (Internal SOP) | **IMPLEMENTED** (Indexed in `SOP-ONGC-GEM-PROC-012`: 7 days entry) |
| 9.2 | "Material purchase requisition / indent banao for mechanical spare parts" | Template (Document) | **IMPLEMENTED** (`indent_letter` template + NEEDS_INPUT) |
| 9.3 | "Technical evaluation note / approval note for vendor selection draft karo" | Template (Document) | **IMPLEMENTED** (`approval_note` template) |
| 9.4 | "Contractor statutory compliance required before RA bill clearance" | RAG (Internal SOP) | **IMPLEMENTED** (Indexed in `SOP-ONGC-GEM-PROC-012`: PF/ESIC) |
| 9.5 | "Circular on updated GeM procurement financial powers draft karo" | Template (Document) | **IMPLEMENTED** (`circular` template) |
| 9.6 | "Calculate Economic Order Quantity (EOQ): Annual demand 12,000 units, Order cost 500, Holding 15%" | Calculation (Code) | **IMPLEMENTED** (Python sandbox formula run) |
| 9.7 | "What is Liquidated Damages (LD) clause in PSU engineering contracts?" | General-Knowledge | **IMPLEMENTED** (Tier 2 legal/contract definition) |
| 9.8 | "Gate pass format for outgoing repairable equipment" | Template (Document) | **IMPLEMENTED** (`approval_note` / `indent` format) |
| 9.9 | "Warehouse stock valuation FIFO vs Weighted Average method difference" | General-Knowledge | **IMPLEMENTED** (Tier 2 accounting comparison) |
| 9.10 | "Tender bid validity extension letter draft karo" | Template (Document) | **IMPLEMENTED** (`circular` / `approval_note` template) |

---

### 10. Human Resources (HR), Legal, IT & Universal General Queries
*   **Core Responsibilities:** Shift scheduling, leave management, statutory labor compliance, CISO air-gap telemetry, cybersecurity compliance, and universal conversational assistance.
*   **Typical Documents:** Office Circular, Leave Email, Shift Schedule Note, IT Asset Request.

| # | Sample Operator Query | Required Capability | Implementation Status |
| :--- | :--- | :--- | :--- |
| 10.1 | "write an email to hr for leave" | Chat (Direct Mode) | **IMPLEMENTED** (Instant draft in chat, think:false, dept:hr) |
| 10.2 | "hi" / "hello" | Chat (Direct Mode) | **IMPLEMENTED** (Instant greeting, think:false, RAG skipped) |
| 10.3 | "who are you and what can you do?" | General-Knowledge | **IMPLEMENTED** (REVEAL identity & sovereign air-gap role) |
| 10.4 | "What is photosynthesis?" | General-Knowledge | **IMPLEMENTED** (Tier 2 concise scientific definition, no freeze) |
| 10.5 | "python script first 10 primes" | Calculation (Code) | **IMPLEMENTED** (Generates code, runs in sandbox, emits verified stdout) |
| 10.6 | "Office circular for safety week celebration draft karo" | Template (Document) | **IMPLEMENTED** (`circular` template) |
| 10.7 | "Explain difference between TCP and UDP networking" | General-Knowledge | **IMPLEMENTED** (Tier 2 IT concept explanation) |
| 10.8 | "Calculate employee gratuity for 14 years service at basic 85,000 INR" | Calculation (Code) | **IMPLEMENTED** (Python sandbox statutory calculation) |
| 10.9 | "Why is air-gapped architecture mandatory for critical PSU infrastructure?" | General-Knowledge | **IMPLEMENTED** (Tier 2 sovereign cybersecurity explanation) |
| 10.10 | "Shift roster 3-shift rotation schedule email draft karo" | Chat (Direct Mode) | **IMPLEMENTED** (Direct email drafting in chat) |

---

## Capabilities Implementation Summary Matrix

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        SOVEREIGN REVEAL CAPABILITY MATRIX                              │
├─────────────────────────┬──────────────────────┬─────────────┬─────────────────────────┤
│ Capability Engine       │ Component Module     │ Status      │ Active Verifications    │
├─────────────────────────┼──────────────────────┼─────────────┼─────────────────────────┤
│ Chemical Safety DB      │ backend/chemical_kb  │ IMPLEMENTED │ 40 chemicals, CAS verified│
│ Two-Tier System Policy  │ backend/chat_mode    │ IMPLEMENTED │ Tier 1 strict / Tier 2 GK │
│ Master SOP Hybrid RAG   │ backend/knowledge_kb │ IMPLEMENTED │ Vector + Tag Boost RAG  │
│ Deterministic Fallback  │ backend/config       │ IMPLEMENTED │ Zero hallucination text │
│ Document Builder Engine │ backend/docs_mode    │ IMPLEMENTED │ DOCX/XLSX/PPTX binary   │
│ Code Sandbox Runner     │ backend/sandbox      │ IMPLEMENTED │ Subprocess + Docker img │
│ Heuristic Router        │ backend/router       │ IMPLEMENTED │ Zero-LLM instant route  │
│ Adaptive Thinking Gate  │ backend/router       │ IMPLEMENTED │ think:false on fact/gen │
│ Zero-Leak Token Stripper│ backend/ollama_client│ IMPLEMENTED │ Multi-pass regex filter │
└─────────────────────────┴──────────────────────┴─────────────┴─────────────────────────┘
```
