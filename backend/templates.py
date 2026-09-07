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
