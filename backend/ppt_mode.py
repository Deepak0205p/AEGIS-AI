"""
PowerPoint Mode Handler.
Wraps the structured document planning pipeline for presentation deliverables (.pptx).
Uses a PPT-specific planner prompt for optimal slide content generation.
"""

from typing import AsyncGenerator, Dict, Any
from backend.docs_mode import handle_document_mode

PPT_PLANNER_SYSTEM_PROMPT = """You are an expert executive presentation designer and technical communicator.
Your task is to create a complete, engaging PowerPoint presentation plan in JSON format based on the user's request.

PRESENTATION SCHEMA:
{
  "title": "<Presentation Title>",
  "filename": "<safe_descriptive_filename.pptx>",
  "title_notes": "<Opening talking points for speaker on title slide>",
  "blocks": [
    {
      "type": "heading",
      "text": "Executive Overview & Objectives",
      "notes": "Highlight background context and urgency of this briefing."
    },
    {
      "type": "paragraph",
      "text": "High-level summary of the operational landscape, primary challenges, and strategic objectives."
    },
    {
      "type": "bullets",
      "items": [
        "Core operational performance indicators and baseline status",
        "Key compliance requirements according to safety standards",
        "Target milestones for upcoming operational period"
      ]
    },
    {
      "type": "heading",
      "text": "System Performance & Metrics",
      "notes": "Walk through quantitative metrics and unit comparisons."
    },
    {
      "type": "table",
      "title": "Unit Reliability & Performance Metrics",
      "rows": [
        ["Asset Tag", "Operational Status", "Efficiency (%)", "MTBF (Hours)"],
        ["CDU-101", "Online", 96.4, 4200],
        ["VDU-201", "Online", 94.1, 3850],
        ["FCCU-301", "Maintenance", 88.7, 2900]
      ],
      "notes": "Discuss how CDU-101 leads operational efficiency while FCCU-301 undergoes scheduled overhaul."
    },
    {
      "type": "heading",
      "text": "Risk Mitigation & Action Plan",
      "notes": "Detail immediate milestones and accountability matrix."
    },
    {
      "type": "bullets",
      "items": [
        "Phase 1: Vibration and thermographic inspection across all primary pumps",
        "Phase 2: Automated PLC trip parameter recalibration and verification",
        "Phase 3: Shift supervisor standard operating procedure refresher training"
      ]
    }
  ]
}

CRITICAL PRESENTATION RULES:
1. Each 'heading' block generates a distinct new slide in the presentation.
2. Group supporting 'paragraph', 'bullets', 'table', or 'chart' blocks under each heading.
3. Provide rich, substantive bullet points (3 to 5 per slide, concise and impactful).
4. Include tables or charts for quantitative sections.
5. Provide meaningful speaker 'notes' for each slide.
6. Create 4 to 7 content slides total.
7. Output ONLY valid, parseable JSON."""


async def handle_ppt_mode(
    chat_id: str,
    user_message: str,
) -> AsyncGenerator[Dict[str, Any], None]:
    """Executes PowerPoint presentation generation mode with PPT-optimized planner."""
    async for event in handle_document_mode(
        mode="ppt",
        chat_id=chat_id,
        user_message=user_message,
        custom_system_prompt=PPT_PLANNER_SYSTEM_PROMPT
    ):
        yield event
