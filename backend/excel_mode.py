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
        ["<Column 1 Header>", "<Column 2 Header>", "<Column 3 Header (Metric)>", "<Status / Category>"],
        ["<Item 1>", "<Category A>", 145.5, "Active"],
        ["<Item 2>", "<Category A>", 210.0, "Active"],
        ["<Item 3>", "<Category B>", 320.8, "Review"],
        ["<Item 4>", "<Category B>", 180.2, "Active"]
      ],
      "highlight_rules": [
        {"column": 3, "condition": "greater_than", "value": 300, "color": "FF4444"}
      ]
    },
    {
      "type": "chart",
      "title": "<Chart Title relevant to the dataset>",
      "rows": [
        ["<Category Header>", "<Metric Header>"],
        ["<Item 1>", 145.5],
        ["<Item 2>", 210.0],
        ["<Item 3>", 320.8],
        ["<Item 4>", 180.2]
      ]
    }
  ]
}

For MULTI-SHEET spreadsheets:
{
  "title": "<Workbook Title>",
  "filename": "<safe_descriptive_filename.xlsx>",
  "sheets": [
    {
      "name": "<Sheet 1 Name>",
      "blocks": [
        {
          "type": "table",
          "rows": [
            ["<Col 1 Header>", "<Col 2 Header>", "<Col 3 Header>", "<Col 4 Header>"],
            ["<Data 1A>", "<Data 1B>", 1500, "Approved"],
            ["<Data 2A>", "<Data 2B>", 3200, "Pending"]
          ]
        }
      ]
    },
    {
      "name": "<Sheet 2 Name>",
      "blocks": [
        {
          "type": "table",
          "rows": [
            ["<Col 1 Header>", "<Col 2 Header>", "<Col 3 Header>", "<Col 4 Header>"],
            ["<Data 3A>", "<Data 3B>", 450, "Complete"],
            ["<Data 4A>", "<Data 4B>", 620, "In Progress"]
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
