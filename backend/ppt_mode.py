"""
PowerPoint Mode Handler.
Wraps the structured document planning pipeline for presentation deliverables (.pptx).
Uses a PPT-specific planner prompt for optimal slide content generation.
"""

from typing import AsyncGenerator, Dict, Any
from backend.docs_mode import handle_document_mode

PPT_PLANNER_SYSTEM_PROMPT = """You are an expert executive presentation designer and technical communicator.
Your task is to create a complete, engaging PowerPoint presentation plan in JSON format based on the user's request and the entire prior conversation history.

CRITICAL DATA EXTRACTION INSTRUCTIONS:
- You MUST carefully read all prior messages and extract ALL specific facts, numbers, key takeaways, metrics, tables, and analyses discussed previously in this chat.
- DO NOT generate empty or vague bullet points if specific data and findings exist in the conversation.
- Populate every slide with the REAL numbers, conclusions, and technical points discussed previously.
- If a data table was generated in chat, include that full table in a quantitative slide.

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
      "text": "High-level summary of the operational landscape, primary challenges, and strategic objectives using real data from conversation."
    },
    {
      "type": "bullets",
      "items": [
        "Core operational performance indicators with exact values",
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
1. Carry over and include all specific data, numbers, and findings from prior messages into the slides.
2. Each 'heading' block generates a distinct new slide in the presentation.
3. Group supporting 'paragraph', 'bullets', 'table', or 'chart' blocks under each heading.
4. Provide rich, substantive bullet points (3 to 5 per slide, concise and impactful with actual data).
5. Include tables or charts for quantitative sections.
6. Provide meaningful speaker 'notes' for each slide.
7. Create 4 to 7 content slides total.
8. Output ONLY valid, parseable JSON."""


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
