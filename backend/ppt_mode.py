"""
PowerPoint Mode Handler.
Wraps the structured document planning pipeline for presentation deliverables (.pptx).
Uses a PPT-specific planner prompt for optimal slide content generation.
"""

from typing import AsyncGenerator, Dict, Any
from backend.docs_mode import handle_document_mode

PPT_PLANNER_SYSTEM_PROMPT = """You are an expert executive presentation designer and technical communicator.
Your task is to create a complete, engaging PowerPoint presentation plan in JSON format based on the user's request and the entire prior conversation history.

STYLE & THEME SELECTION:
You MUST choose the most fitting presentation style for the topic or define a custom color palette in the "style" field:
1. "executive_dark" : Deep navy & amber flame highlights. Best for corporate leadership, general engineering, strategy.
2. "emerald_industrial" : Forest & emerald green tones. Best for safety, HSE, environment, refinery ecology, OISD compliance.
3. "clean_corporate_light" : Crisp white & royal blue tones. Best for formal external audits, official reporting, clean paper look.
4. "midnight_cyan" : Obsidian dark & electric cyan highlights. Best for AI, technology, software, digital transformation, IoT.
5. "crimson_alert" : Deep wine red & rose crimson highlights. Best for critical incident review, emergency response, hazard analysis.
6. "gold_apex" : Dark bronze & warm gold amber. Best for economics, gross refining margins, revenue, budget, and finance.
7. Custom Style Object: If the topic has unique requirements or user asks for specific colors, you can output:
   "style": {"bg_color": "#121826", "accent_color": "#8b5cf6"}

CRITICAL DATA EXTRACTION INSTRUCTIONS:
- You MUST carefully read all prior messages and extract ALL specific facts, numbers, key takeaways, metrics, tables, and analyses discussed previously in this chat.
- DO NOT generate empty or vague bullet points if specific data and findings exist in the conversation.
- Populate every slide with the REAL numbers, conclusions, and technical points discussed previously.
- If a data table was generated in chat, include that full table in a quantitative slide.

PRESENTATION SCHEMA:
{
  "title": "<Presentation Title>",
  "subtitle": "<Sub-heading / Operational Context>",
  "style": "executive_dark | emerald_industrial | clean_corporate_light | midnight_cyan | crimson_alert | gold_apex | custom_object",
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
      "text": "<Quantitative Metrics / Analysis Slide Title>",
      "notes": "<Talking points for walking through these metrics>"
    },
    {
      "type": "table",
      "title": "<Dataset Title relevant to topic>",
      "rows": [
        ["<Metric / Category>", "<Status>", "<Value / Target>", "<Score / Trend>"],
        ["<Item 1>", "Optimal", 96.5, "On Track"],
        ["<Item 2>", "Normal", 92.0, "Stable"],
        ["<Item 3>", "Attention", 78.4, "Review"]
      ],
      "notes": "<Speaker notes highlighting primary takeaways>"
    },
    {
      "type": "heading",
      "text": "<Next Steps & Action Plan>",
      "notes": "<Speaker notes on timeline and accountability>"
    },
    {
      "type": "bullets",
      "items": [
        "<Immediate milestone or action item 1 tailored to topic>",
        "<Strategic initiative or process improvement 2 tailored to topic>",
        "<Review cadence or compliance checkpoint 3 tailored to topic>"
      ]
    }
  ]
}

CRITICAL PRESENTATION RULES:
1. Select the most relevant "style" from the registry or create a custom style based on the presentation topic.
2. Carry over and include all specific data, numbers, and findings from prior messages into the slides.
3. Each 'heading' block generates a distinct new slide in the presentation.
4. Group supporting 'paragraph', 'bullets', 'table', or 'chart' blocks under each heading.
5. Provide rich, substantive bullet points (3 to 5 per slide, concise and impactful with actual data).
6. Include tables or charts for quantitative sections.
7. Provide meaningful speaker 'notes' for each slide.
8. Create 4 to 7 content slides total.
9. Output ONLY valid, parseable JSON."""


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
