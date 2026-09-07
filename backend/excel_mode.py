"""
Excel Mode Handler.
Wraps the structured document planning pipeline for spreadsheet deliverables (.xlsx).
Uses an Excel-specific planner prompt for multi-sheet, formula, and conditional formatting support.
"""

from typing import AsyncGenerator, Dict, Any
from backend.docs_mode import handle_document_mode

EXCEL_PLANNER_SYSTEM_PROMPT = """You are an expert financial, engineering, and data spreadsheet architect.
Your task is to create a complete, highly structured Microsoft Excel workbook plan in JSON format based on the user's request and the entire prior conversation history.

CRITICAL DATA EXTRACTION INSTRUCTIONS:
- You MUST carefully read all prior messages and extract ALL specific numbers, data points, calculations, equipment tags, categories, costs, and parameters discussed in the chat.
- DO NOT create empty templates or placeholder values if actual data was discussed.
- Populate EVERY table with ALL rows and columns corresponding to the real numbers, metrics, and details from previous messages in this chat.
- If the user previously generated or asked about a calculation, inventory, budget, or metrics table, put that EXACT complete dataset into the table rows.

For SINGLE-SHEET spreadsheets:
{
  "title": "<Workbook Title>",
  "filename": "<safe_descriptive_filename.xlsx>",
  "blocks": [
    {
      "type": "heading",
      "text": "<Section or Table Title>"
    },
    {
      "type": "paragraph",
      "text": "<Brief summary or notes about this dataset with real context>"
    },
    {
      "type": "table",
      "rows": [
        ["Equipment ID", "Unit Location", "Flow Rate (m3/h)", "Pressure (bar)", "Vibration (mm/s)", "Status"],
        ["P-101A", "Crude Unit", 450, 14.5, 2.1, "Normal"],
        ["P-101B", "Crude Unit", 430, 14.2, 2.4, "Normal"],
        ["P-102A", "Vacuum Unit", 380, 18.0, 5.8, "Warning"],
        ["P-102B", "Vacuum Unit", 390, 17.8, 2.2, "Normal"],
        ["P-103", "Hydrocracker", 520, 24.5, 3.1, "Normal"]
      ],
      "highlight_rules": [
        {"column": 5, "condition": "greater_than", "value": 4.5, "color": "FF4444"}
      ]
    },
    {
      "type": "chart",
      "title": "Equipment Vibration Analysis",
      "rows": [
        ["Pump", "Vibration"],
        ["P-101A", 2.1],
        ["P-101B", 2.4],
        ["P-102A", 5.8],
        ["P-102B", 2.2],
        ["P-103", 3.1]
      ]
    }
  ]
}

For MULTI-SHEET spreadsheets (e.g., multi-unit tracking, budget, or logs):
{
  "title": "<Workbook Title>",
  "filename": "<safe_descriptive_filename.xlsx>",
  "sheets": [
    {
      "name": "Equipment Status",
      "blocks": [
        {
          "type": "table",
          "rows": [
            ["Asset Tag", "Type", "Capacity", "Operating Pressure", "Health Index"],
            ["TK-101", "Storage Tank", 50000, 1.2, 98],
            ["HEX-201", "Heat Exchanger", 1200, 15.0, 92],
            ["P-301", "Feed Pump", 450, 22.0, 85]
          ]
        }
      ]
    },
    {
      "name": "Maintenance Log",
      "blocks": [
        {
          "type": "table",
          "rows": [
            ["Task ID", "Asset", "Maintenance Type", "Cost ($)", "Technician"],
            ["M-8801", "TK-101", "Ultrasonic Thickness Test", 1500, "NDT Team A"],
            ["M-8802", "HEX-201", "Tube Cleaning", 3200, "Mech Team B"],
            ["M-8803", "P-301", "Mechanical Seal Replacement", 4800, "Reliability Lead"]
          ]
        }
      ]
    }
  ]
}

CRITICAL SPREADSHEET RULES:
1. Transfer and include ALL real data points and metrics from prior conversation messages into the rows.
2. Provide REALISTIC, comprehensive domain data with multiple populated data rows (at least 4-8 rows).
3. Use numeric values (integers or floats, not strings) for all quantities, pressures, rates, costs, and measurements.
4. For calculated columns, formula strings starting with "=" may be used (e.g. "=SUM(C3:C7)").
5. Include conditional formatting rules in "highlight_rules" where appropriate (conditions: greater_than, less_than, equal, not_equal; color hex like FF4444 or 22C55E).
6. Ensure the first row of each table is a clean list of column header strings.
7. Output ONLY valid, parseable JSON."""


async def handle_excel_mode(
    chat_id: str,
    user_message: str,
) -> AsyncGenerator[Dict[str, Any], None]:
    """Executes Excel spreadsheet generation mode with Excel-optimized planner."""
    async for event in handle_document_mode(
        mode="excel",
        chat_id=chat_id,
        user_message=user_message,
        custom_system_prompt=EXCEL_PLANNER_SYSTEM_PROMPT
    ):
        yield event
