"""
Document Template Registry for Air-Gapped Local AI Backend.
Maps intents to structured document templates with mandatory sections.
Templates enforce NEEDS_INPUT protocol — never invent data.
"""

from typing import Dict, Any, List, Optional


# Template sections for each document type
TEMPLATE_SECTIONS: Dict[str, List[Dict[str, Any]]] = {
    "shift_handover": {
        "title": "Shift Handover Log",
        "sections": [
            {"type": "heading", "text": "Shift Handover Report", "level": 1},
            {"type": "table", "text": "Shift Details", "fields": [
                "Date", "Shift", "In-Charge", "Handed Over To"
            ]},
            {"type": "heading", "text": "Process Status", "level": 2},
            {"type": "table", "text": "Key Parameters", "fields": [
                "Unit", "Parameter", "Value", "Status"
            ]},
            {"type": "heading", "text": "Active Permits", "level": 2},
            {"type": "bullets", "text": "Open PTW/LOTO entries"},
            {"type": "heading", "text": "Pending Actions", "level": 2},
            {"type": "bullets", "text": "Outstanding tasks for next shift"},
            {"type": "heading", "text": "Safety Observations", "level": 2},
            {"type": "paragraph", "text": "Any safety notes or near-miss observations"},
        ],
    },
    "daily_production_report": {
        "title": "Daily Production Report (DPR)",
        "sections": [
            {"type": "heading", "text": "Daily Production Report", "level": 1},
            {"type": "table", "text": "Production Summary", "fields": [
                "Unit", "Target", "Actual", "Variance"
            ]},
            {"type": "heading", "text": "Crude Processing", "level": 2},
            {"type": "table", "text": "Crude Distillation", "fields": [
                "Parameter", "Value", "Unit"
            ]},
            {"type": "heading", "text": "Product Quality", "level": 2},
            {"type": "table", "text": "Lab Analysis", "fields": [
                "Product", "Test", "Result", "Spec"
            ]},
            {"type": "heading", "text": "Utility Consumption", "level": 2},
            {"type": "table", "text": "Utilities", "fields": [
                "Utility", "Consumption", "Unit"
            ]},
            {"type": "heading", "text": "Notable Events", "level": 2},
            {"type": "bullets", "text": "Key events during the shift"},
        ],
    },
    "inspection_report": {
        "title": "Inspection Report",
        "sections": [
            {"type": "heading", "text": "Equipment Inspection Report", "level": 1},
            {"type": "table", "text": "Equipment Details", "fields": [
                "Tag", "Description", "Service", "Last Inspection"
            ]},
            {"type": "heading", "text": "Inspection Findings", "level": 2},
            {"type": "table", "text": "Measurement Data", "fields": [
                "Parameter", "Previous Reading", "Current Reading", "Minimum Required", "Unit"
            ]},
            {"type": "heading", "text": "Condition Assessment", "level": 2},
            {"type": "paragraph", "text": "Overall condition and observations"},
            {"type": "heading", "text": "Recommendations", "level": 2},
            {"type": "bullets", "text": "Recommended actions and next inspection date"},
        ],
    },
    "incident_report": {
        "title": "Incident Report",
        "sections": [
            {"type": "heading", "text": "Incident / Near-Miss Report", "level": 1},
            {"type": "table", "text": "Incident Details", "fields": [
                "Date", "Time", "Location", "Reported By"
            ]},
            {"type": "heading", "text": "Description", "level": 2},
            {"type": "paragraph", "text": "Detailed description of the incident"},
            {"type": "heading", "text": "Immediate Actions Taken", "level": 2},
            {"type": "bullets", "text": "Actions taken immediately after incident"},
            {"type": "heading", "text": "Root Cause Analysis", "level": 2},
            {"type": "paragraph", "text": "Root cause investigation findings"},
            {"type": "heading", "text": "Corrective Actions", "level": 2},
            {"type": "bullets", "text": "Corrective and preventive actions with responsible persons and timelines"},
            {"type": "heading", "text": "Risk Assessment", "level": 2},
            {"type": "table", "text": "Risk Matrix", "fields": [
                "Hazard", "Likelihood", "Consequence", "Risk Level"
            ]},
        ],
    },
    "mock_drill_report": {
        "title": "Mock Drill Report",
        "sections": [
            {"type": "heading", "text": "Mock Drill / Emergency Exercise Report", "level": 1},
            {"type": "table", "text": "Drill Details", "fields": [
                "Date", "Drill Type", "Location", "Conducted By"
            ]},
            {"type": "heading", "text": "Scenario", "level": 2},
            {"type": "paragraph", "text": "Drill scenario description"},
            {"type": "heading", "text": "Response Summary", "level": 2},
            {"type": "bullets", "text": "Key response actions and timeline"},
            {"type": "heading", "text": "Performance Assessment", "level": 2},
            {"type": "table", "text": "Assessment", "fields": [
                "Criteria", "Rating", "Remarks"
            ]},
            {"type": "heading", "text": "Lessons Learned", "level": 2},
            {"type": "bullets", "text": "Improvement areas and action items"},
        ],
    },
    "approval_note": {
        "title": "Approval Note / Technical Evaluation",
        "sections": [
            {"type": "heading", "text": "Technical Evaluation / Approval Note", "level": 1},
            {"type": "table", "text": "Subject Details", "fields": [
                "Subject", "Reference", "Date", "Prepared By"
            ]},
            {"type": "heading", "text": "Background", "level": 2},
            {"type": "paragraph", "text": "Context and background of the request"},
            {"type": "heading", "text": "Technical Assessment", "level": 2},
            {"type": "paragraph", "text": "Technical analysis and evaluation"},
            {"type": "heading", "text": "Commercial Evaluation", "level": 2},
            {"type": "table", "text": "Cost Comparison", "fields": [
                "Item", "Option A", "Option B"
            ]},
            {"type": "heading", "text": "Recommendation", "level": 2},
            {"type": "paragraph", "text": "Final recommendation and justification"},
            {"type": "heading", "text": "Approvals", "level": 2},
            {"type": "table", "text": "Approval Chain", "fields": [
                "Role", "Name", "Signature", "Date"
            ]},
        ],
    },
    "breakdown_analysis": {
        "title": "Breakdown / Failure Analysis",
        "sections": [
            {"type": "heading", "text": "Equipment Breakdown Analysis", "level": 1},
            {"type": "table", "text": "Breakdown Details", "fields": [
                "Tag", "Date of Failure", "Run Hours", "Severity"
            ]},
            {"type": "heading", "text": "Failure Description", "level": 2},
            {"type": "paragraph", "text": "Detailed description of the failure"},
            {"type": "heading", "text": "Root Cause", "level": 2},
            {"type": "paragraph", "text": "Root cause analysis findings"},
            {"type": "heading", "text": "Corrective Action", "level": 2},
            {"type": "bullets", "text": "Repair actions taken"},
            {"type": "heading", "text": "Parts Replaced", "level": 2},
            {"type": "table", "text": "Spare Parts", "fields": [
                "Part", "Specification", "Qty", "Source"
            ]},
            {"type": "heading", "text": "Recommendations", "level": 2},
            {"type": "bullets", "text": "Preventive measures to avoid recurrence"},
        ],
    },
    "dpr": {
        "title": "Daily Progress Report",
        "sections": [
            {"type": "heading", "text": "Daily Progress Report", "level": 1},
            {"type": "table", "text": "Project Info", "fields": [
                "Project", "Date", "Prepared By"
            ]},
            {"type": "heading", "text": "Work Completed", "level": 2},
            {"type": "bullets", "text": "Activities completed today"},
            {"type": "heading", "text": "Work in Progress", "level": 2},
            {"type": "bullets", "text": "Ongoing activities"},
            {"type": "heading", "text": "Issues / Blockers", "level": 2},
            {"type": "bullets", "text": "Issues requiring management attention"},
            {"type": "heading", "text": "Tomorrow's Plan", "level": 2},
            {"type": "bullets", "text": "Planned activities for next day"},
        ],
    },
    "indent_letter": {
        "title": "Indent / Purchase Requisition",
        "sections": [
            {"type": "heading", "text": "Material Indent / Purchase Requisition", "level": 1},
            {"type": "table", "text": "Indent Details", "fields": [
                "Indent No", "Date", "Required By", "Requested By"
            ]},
            {"type": "heading", "text": "Material Requirements", "level": 2},
            {"type": "table", "text": "Bill of Materials", "fields": [
                "Item", "Description", "Specification", "Qty", "Unit"
            ]},
            {"type": "heading", "text": "Justification", "level": 2},
            {"type": "paragraph", "text": "Reason for requirement and urgency"},
            {"type": "heading", "text": "Budget Allocation", "level": 2},
            {"type": "table", "text": "Budget", "fields": [
                "Cost Center", "WBS", "Estimated Cost"
            ]},
        ],
    },
    "circular": {
        "title": "Circular / Office Order",
        "sections": [
            {"type": "heading", "text": "Circular / Office Order", "level": 1},
            {"type": "table", "text": "Circular Details", "fields": [
                "Reference No", "Date", "Issued By", "To"
            ]},
            {"type": "heading", "text": "Subject", "level": 2},
            {"type": "paragraph", "text": "Subject of the circular"},
            {"type": "heading", "text": "Details", "level": 2},
            {"type": "paragraph", "text": "Detailed instructions or information"},
            {"type": "heading", "text": "Compliance Required", "level": 2},
            {"type": "bullets", "text": "Action items and compliance requirements"},
        ],
    },
    # --- PSU Manufacturing Domain Templates ---
    "gem_tender_eval": {
        "title": "GeM Tender & Commercial Evaluation",
        "sections": [
            {"type": "heading", "text": "Public Procurement & GeM Bid Evaluation Note", "level": 1},
            {"type": "table", "text": "Tender Overview", "fields": [
                "Bid No / GeM Ref", "Department", "Estimated Value (INR)", "Bid Closing Date"
            ]},
            {"type": "heading", "text": "Technical Qualification Summary", "level": 2},
            {"type": "table", "text": "Vendor Evaluation", "fields": [
                "Bidder Name", "OEM Status", "Tech Compliance (Yes/No)", "Deviation Remarks"
            ]},
            {"type": "heading", "text": "Commercial & L1 Determination", "level": 2},
            {"type": "table", "text": "Financial Comparative Statement", "fields": [
                "Bidder", "Base Price", "GST / Taxes", "Landed Cost (INR)", "Rank (L1/L2/L3)"
            ]},
            {"type": "heading", "text": "Make in India (DPIIT) & MSME Preference", "level": 2},
            {"type": "paragraph", "text": "Local content percentage verification and purchase preference eligibility"},
            {"type": "heading", "text": "Competent Financial Authority (CFA) Recommendation", "level": 2},
            {"type": "paragraph", "text": "Clear justification for award recommendation to L1 bidder under GFR 2017"},
        ],
    },
    "board_note": {
        "title": "PSU Board / Management Note",
        "sections": [
            {"type": "heading", "text": "Memorandum for Board of Directors / Management Committee", "level": 1},
            {"type": "table", "text": "Agenda Metadata", "fields": [
                "Agenda Item No", "Division/Unit", "Target Meeting Date", "Sponsored Director"
            ]},
            {"type": "heading", "text": "1. Statement of Proposal & Objective", "level": 2},
            {"type": "paragraph", "text": "Concise statement of executive action or Capex expenditure requiring approval"},
            {"type": "heading", "text": "2. Background & Strategic Rationale", "level": 2},
            {"type": "paragraph", "text": "Operational context, capacity expansion, energy transition, or statutory mandate"},
            {"type": "heading", "text": "3. Financial Implications & Cost-Benefit Analysis", "level": 2},
            {"type": "table", "text": "Financial Summary", "fields": [
                "Particulars", "Budgeted Outlay", "Source of Funds (Internal/Debt)", "Projected IRR / Payback"
            ]},
            {"type": "heading", "text": "4. Risk Matrix & Mitigation Strategy", "level": 2},
            {"type": "bullets", "text": "Technical, market, and regulatory risks with safeguards"},
            {"type": "heading", "text": "5. Draft Board Resolution", "level": 2},
            {"type": "paragraph", "text": "Exact text of the resolution proposed for adoption by the Board"},
        ],
    },
    "vendor_negotiation": {
        "title": "Vendor Negotiation Record",
        "sections": [
            {"type": "heading", "text": "Commercial Negotiation Minutes & Price Settlement", "level": 1},
            {"type": "table", "text": "Procurement Details", "fields": [
                "Negotiation Date", "Vendor Name", "Original Bid Value", "Negotiation Committee Members"
            ]},
            {"type": "heading", "text": "Points of Discussion", "level": 2},
            {"type": "bullets", "text": "Negotiation on unit rates, payment milestones, LD clauses, warranty, and AMC"},
            {"type": "heading", "text": "Price Reduction Agreed", "level": 2},
            {"type": "table", "text": "Savings Summary", "fields": [
                "Item Description", "Original Quoted", "Final Agreed Price", "Net Savings Achieved"
            ]},
            {"type": "heading", "text": "Sign-off & Undertaking", "level": 2},
            {"type": "paragraph", "text": "Formal concurrence by Vendor Representative and PSU Committee"},
        ],
    },
    # --- Defence Domain Templates ---
    "dap_sqr_compliance": {
        "title": "DAP 2020 SQR Compliance Matrix",
        "sections": [
            {"type": "heading", "text": "Defence Acquisition Procedure (DAP) - Staff Qualitative Requirements (SQR) Compliance", "level": 1},
            {"type": "table", "text": "Program Meta", "fields": [
                "Project / System Name", "Procurement Category (Make-I/Make-II/IDDM)", "Service (Army/Navy/AirForce)", "Security Classification"
            ]},
            {"type": "heading", "text": "Detailed Technical & Environmental Compliance", "level": 2},
            {"type": "table", "text": "SQR Parameter Audit", "fields": [
                "SQR Clause", "Requirement Description", "Tested / Offered Spec", "Compliance (Complied/Deviated)", "Verification Method (Lab/Field Trial)"
            ]},
            {"type": "heading", "text": "Indigenisation & Local Content (IC %)", "level": 2},
            {"type": "paragraph", "text": "Breakdown of domestic subsystem sourcing vs imported components"},
            {"type": "heading", "text": "Trial Directives & Field Evaluation Report", "level": 2},
            {"type": "bullets", "text": "Desert/high-altitude/saline trial logs and EMI/EMC compliance status"},
        ],
    },
    "security_audit_airgap": {
        "title": "Defence IT/OT Security & Air-Gap Compliance Certificate",
        "sections": [
            {"type": "heading", "text": "Air-Gap Network Isolation & Security Verification Audit", "level": 1},
            {"type": "table", "text": "Audit Info", "fields": [
                "Facility / Lab", "Inspected Unit", "Classification Level", "Auditor Name & Unit"
            ]},
            {"type": "heading", "text": "1. Physical & RF Isolation Checks", "level": 2},
            {"type": "bullets", "text": "Verification of Faraday shielding, TEMPEST boundaries, and disabled wireless NICs"},
            {"type": "heading", "text": "2. Outbound Network & Socket Audit", "level": 2},
            {"type": "table", "text": "Interface Verification", "fields": [
                "NIC / Port", "Allowed Destination", "Observed Packets", "Leakage Status (Zero/Violation)"
            ]},
            {"type": "heading", "text": "3. Removable Media & Firmware Hash Integrity", "level": 2},
            {"type": "paragraph", "text": "SHA-256 hash checksums of deployed binaries and air-gap transfer logs"},
            {"type": "heading", "text": "Auditor Certification & Clearance", "level": 2},
            {"type": "paragraph", "text": "Formal declaration of sovereign air-gap isolation compliant with MoD guidelines"},
        ],
    },
    "technical_drawing_review": {
        "title": "Engineering Drawing & P&ID Review Note",
        "sections": [
            {"type": "heading", "text": "Engineering / Scanned Drawing Verification Report", "level": 1},
            {"type": "table", "text": "Drawing Metadata", "fields": [
                "Drawing No", "Revision", "System/Equipment", "Reviewed By / Discipline"
            ]},
            {"type": "heading", "text": "Design Parameter Verification", "level": 2},
            {"type": "table", "text": "Dimensional & Material Checks", "fields": [
                "Feature / Line Tag", "Design Standard (ASME/MIL-STD)", "Specified Value", "Drawing Value", "Concurrence"
            ]},
            {"type": "heading", "text": "Discrepancy / Redline Findings", "level": 2},
            {"type": "bullets", "text": "Clashes, unverified tie-in points, missing relief valves or tolerances"},
            {"type": "heading", "text": "Approval Recommendation", "level": 2},
            {"type": "paragraph", "text": "Approved for Construction (AFC) / Return with Comments (RWC)"},
        ],
    },
    # --- Government / Secretariat Domain Templates ---
    "cabinet_note": {
        "title": "Cabinet / Ministry Note",
        "sections": [
            {"type": "heading", "text": "Cabinet Note / Inter-Ministerial Note for Decision", "level": 1},
            {"type": "table", "text": "File Metadata", "fields": [
                "File No", "Ministry / Department", "Subject", "Date"
            ]},
            {"type": "heading", "text": "1. Proposal", "level": 2},
            {"type": "paragraph", "text": "The specific approval or policy sanction being sought from the Cabinet"},
            {"type": "heading", "text": "2. Background & Genesis", "level": 2},
            {"type": "paragraph", "text": "Historical trajectory, earlier approvals, committee recommendations"},
            {"type": "heading", "text": "3. Inter-Ministerial Consultations", "level": 2},
            {"type": "table", "text": "Stakeholder Views", "fields": [
                "Ministry/Dept Consulted", "Views/Comments", "Response of Sponsoring Ministry"
            ]},
            {"type": "heading", "text": "4. Financial Implications & Budgetary Provision", "level": 2},
            {"type": "paragraph", "text": "Total expenditure, phasing across financial years, and concurrence of Ministry of Finance (Dept of Expenditure)"},
            {"type": "heading", "text": "5. Approval Sought (Para for Decision)", "level": 2},
            {"type": "paragraph", "text": "Exact operative paragraphs where sanction of the competent authority is requested"},
        ],
    },
    "official_gazette": {
        "title": "Statutory Order / Gazette Notification",
        "sections": [
            {"type": "heading", "text": "Gazette Notification / Statutory Order", "level": 1},
            {"type": "table", "text": "Notification Record", "fields": [
                "Notification Ref", "Authority", "Effective Date", "Publication Part/Section"
            ]},
            {"type": "heading", "text": "Preamble & Statutory Authority", "level": 2},
            {"type": "paragraph", "text": "Exercise of powers conferred by relevant Section of the Enacted Act"},
            {"type": "heading", "text": "Operative Provisions & Rules", "level": 2},
            {"type": "bullets", "text": "Numbered rules, amendments, exemptions, or mandatory compliances"},
            {"type": "heading", "text": "Schedule / Form Appendices", "level": 2},
            {"type": "table", "text": "Prescribed Standards/Fees", "fields": [
                "Item No", "Category", "Prescribed Parameter / Rate", "Enforcement Date"
            ]},
        ],
    },
    "rti_reply": {
        "title": "RTI Disposal & Information Reply",
        "sections": [
            {"type": "heading", "text": "Right to Information (RTI) Act 2005 - Formal Disposal Note", "level": 1},
            {"type": "table", "text": "RTI Details", "fields": [
                "RTI Registration No", "Date Received", "CPIO / PIO", "Applicant Name"
            ]},
            {"type": "heading", "text": "Point-wise Query & Official Response", "level": 2},
            {"type": "table", "text": "Query Mapping", "fields": [
                "Query No", "Information Sought", "Official Fact-Grounded Response / Exemption Clause"
            ]},
            {"type": "heading", "text": "Appellate Authority Information", "level": 2},
            {"type": "paragraph", "text": "Name, designation, and address of the First Appellate Authority with 30-day appeal window notice"},
        ],
    },
}

# Intent -> template mapping
INTENT_TO_TEMPLATE = {
    # Shift handover
    "shift handover": "shift_handover",
    "handover": "shift_handover",
    "shift log": "shift_handover",
    "shift change": "shift_handover",
    "shift交接": "shift_handover",
    # DPR
    "daily production report": "daily_production_report",
    "dpr": "daily_production_report",
    "production report": "daily_production_report",
    # Inspection
    "inspection report": "inspection_report",
    "inspection": "inspection_report",
    "thickness": "inspection_report",
    "corrosion": "inspection_report",
    "ut reading": "inspection_report",
    "utm": "inspection_report",
    # Incident
    "incident report": "incident_report",
    "incident": "incident_report",
    "accident": "incident_report",
    "near miss": "incident_report",
    "oil spill": "incident_report",
    "fire": "incident_report",
    "gas leak": "incident_report",
    # Mock drill
    "mock drill": "mock_drill_report",
    "drill report": "mock_drill_report",
    "emergency drill": "mock_drill_report",
    # Approval
    "approval note": "approval_note",
    "technical evaluation": "approval_note",
    "evaluation note": "approval_note",
    "approval": "approval_note",
    # Breakdown
    "breakdown": "breakdown_analysis",
    "failure analysis": "breakdown_analysis",
    "equipment failure": "breakdown_analysis",
    "breakdown analysis": "breakdown_analysis",
    # DPR (project)
    "progress report": "dpr",
    "daily progress": "dpr",
    "project status": "dpr",
    # Indent
    "indent": "indent_letter",
    "purchase requisition": "indent_letter",
    "material indent": "indent_letter",
    "pr": "indent_letter",
    # Circular
    "circular": "circular",
    "office order": "circular",
    "office circular": "circular",
    # PSU Domain Intents
    "gem tender": "gem_tender_eval",
    "gem bid": "gem_tender_eval",
    "tender evaluation": "gem_tender_eval",
    "bid evaluation": "gem_tender_eval",
    "board note": "board_note",
    "board memorandum": "board_note",
    "agenda note": "board_note",
    "vendor negotiation": "vendor_negotiation",
    "price negotiation": "vendor_negotiation",
    "commercial negotiation": "vendor_negotiation",
    # Defence Domain Intents
    "sqr": "dap_sqr_compliance",
    "sqr compliance": "dap_sqr_compliance",
    "dap compliance": "dap_sqr_compliance",
    "defence trial": "dap_sqr_compliance",
    "air-gap audit": "security_audit_airgap",
    "airgap audit": "security_audit_airgap",
    "security audit": "security_audit_airgap",
    "air gap certificate": "security_audit_airgap",
    "drawing review": "technical_drawing_review",
    "pid review": "technical_drawing_review",
    "p&id review": "technical_drawing_review",
    "scanned drawing": "technical_drawing_review",
    # Government Domain Intents
    "cabinet note": "cabinet_note",
    "inter-ministerial note": "cabinet_note",
    "ministry note": "cabinet_note",
    "gazette": "official_gazette",
    "statutory order": "official_gazette",
    "gazette notification": "official_gazette",
    "rti": "rti_reply",
    "rti response": "rti_reply",
    "rti reply": "rti_reply",
}


def detect_template(message: str) -> Optional[str]:
    """
    Detects the document template intent from a message.
    Returns template key or None if no template match.
    """
    text = message.strip().lower()
    for intent, template in INTENT_TO_TEMPLATE.items():
        if intent in text:
            return template
    return None


def get_template_sections(template_key: str) -> Optional[Dict[str, Any]]:
    """Returns template definition with sections."""
    return TEMPLATE_SECTIONS.get(template_key)


def get_template_for_docs(message: str) -> Optional[Dict[str, Any]]:
    """
    Combined: detect template from message and return full template definition.
    Returns None if no template match.
    """
    key = detect_template(message)
    if key:
        tpl = TEMPLATE_SECTIONS.get(key)
        if tpl:
            return {"template_key": key, **tpl}
    return None
