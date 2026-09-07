"""
Document Planning and Generation Handler for Word (.docx), Excel (.xlsx), and PowerPoint (.pptx).
Strictly separates LLM planning (JSON) from Python binary file generation.
"""

import json
from typing import AsyncGenerator, Dict, Any, List, Optional
from backend.config import logger
from backend.ollama_client import call_ollama
from backend.db import build_context_messages, save_message
from backend.deliverables import create_deliverable_file

DOC_PLANNER_SYSTEM_PROMPT = """ANTI-HALLUCINATION RULES:
- Answer ONLY from: (a) the user's messages, (b) conversation history, (c) actual tool/sandbox output. Nothing else.
- NEVER invent: numbers, dates, names, standards/clause numbers, quotes, file contents, or "results" of anything we did not actually run.
- If information needed for an answer is missing, ASK one specific question instead of guessing. "I'm not sure, I need X" is always acceptable.
- Never claim to have run, searched, or verified anything that was not actually executed.
- Short and honest beats long and confident-but-wrong.

DOCUMENT PLANNER DIRECTIVE:
You are a document planner. Using ONLY information present in this conversation, output JSON:
{
  "title": "<document title>",
  "filename": "<safe filename with appropriate extension>",
  "blocks": [
    {
      "type": "heading|paragraph|bullets|table|chart",
      "text": "<content or heading text, or 'NEEDS_INPUT' if missing from conversation>",
      "level": 1,
      "items": ["<bullet 1>", "<bullet 2>"],
      "rows": [["Col 1", "Col 2"], ["Val 1", "Val 2"]],
      "question": "<specific question to ask user if text is NEEDS_INPUT>"
    }
  ]
}
If data needed for any section is NOT in the conversation, set that block's text to "NEEDS_INPUT" and add "question": "<what you need>". Never invent numbers, names, dates, or findings. Output ONLY valid JSON."""


def parse_plan_json(raw_text: str) -> Optional[Dict[str, Any]]:
    """Extracts and parses JSON object from model output."""
    raw = raw_text.strip()
    # Strip markdown code fencing if present
    if raw.startswith("```"):
        lines = raw.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw = "\n".join(lines).strip()
        
    try:
        data = json.loads(raw)
        if isinstance(data, dict) and "blocks" in data:
            return data
        elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            return {"title": "Document", "filename": "document.docx", "blocks": data}
        elif isinstance(data, dict):
            return data
    except Exception:
        pass
    return None


async def handle_document_mode(
    mode: str,
    chat_id: str,
    user_message: str,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Executes Document / Excel / PPT mode:
    1. Plan with json_mode=True, temperature 0.3
    2. Check for NEEDS_INPUT blocks -> ask question and pause if so
    3. Generate genuine binary deliverable with Python
    4. Stream progress and emit final file download link.
    """
    logger.info(f"[{mode.upper()}_MODE] chat_id={chat_id} temperature=0.3 mode={mode}")
    
    save_message(chat_id, "user", user_message, mode=mode)
    messages = await build_context_messages(chat_id, DOC_PLANNER_SYSTEM_PROMPT, user_message)
    
    yield {"token": f"Planning {mode.upper()} structure based on conversation data...\n"}
    
    # Step 1: Call Ollama with json_mode=True
    plan_raw = await call_ollama(messages, stream=False, temperature=0.3, json_mode=True)
    plan_data = parse_plan_json(str(plan_raw))
    
    # Step 2: Retry once if JSON parse failed
    if not plan_data:
        yield {"token": "[Validating document schema...]\n"}
        retry_messages = messages + [
            {"role": "assistant", "content": str(plan_raw)},
            {"role": "user", "content": "Return ONLY valid JSON matching the schema."}
        ]
        retry_raw = await call_ollama(retry_messages, stream=False, temperature=0.2, json_mode=True)
        plan_data = parse_plan_json(str(retry_raw))
        
    if not plan_data:
        error_msg = f"Failed to parse document plan from model. Never fabricating unverified data."
        logger.error(error_msg)
        save_message(chat_id, "assistant", error_msg, mode=mode)
        yield {
            "token": f"\n\n**Error:** {error_msg}\nPlease rephrase your request with specific details."
        }
        yield {
            "done": True,
            "generated_file": None,
            "run_output": None,
            "status": "error"
        }
        return

    # Step 3: Check for NEEDS_INPUT blocks
    blocks = plan_data.get("blocks", [])
    missing_inputs = []
    
    for b in blocks:
        text_val = str(b.get("text", "")).strip()
        status_val = str(b.get("status", "")).strip()
        question = b.get("question")
        
        if text_val == "NEEDS_INPUT" or status_val == "NEEDS_INPUT" or question:
            q_text = question or f"Missing required information for section '{b.get('type', 'section')}'."
            missing_inputs.append(q_text)

    if missing_inputs:
        clarifying_question = "\n".join([f"• {q}" for q in missing_inputs])
        response_text = (
            f"To generate this {mode.upper()} document accurately without guessing, I need additional information:\n\n"
            f"{clarifying_question}\n\nPlease reply with these details to build your document."
        )
        logger.info(f"[{mode.upper()}_MODE] NEEDS_INPUT detected. Streaming question to user.")
        save_message(chat_id, "assistant", response_text, mode=mode)
        
        yield {"token": f"\n{response_text}"}
        yield {
            "done": True,
            "generated_file": None,
            "run_output": None,
            "status": "needs_input"
        }
        return

    # Step 4: All data is present -> Build file in Python
    yield {"token": f"\n\nBuilding {mode.upper()} file in Python from verified plan...\n"}
    try:
        deliverable = create_deliverable_file(plan_data, mode=mode, chat_id=chat_id)
        download_url = deliverable["download_url"]
        filename = deliverable["filename"]
        
        msg_content = (
            f"✅ **{mode.upper()} Document Generated:** [{filename}]({download_url})\n\n"
            f"- **Title:** {plan_data.get('title', 'Document')}\n"
            f"- **Sections Built:** {len(blocks)}\n"
            f"- **File Download:** [Download {filename}]({download_url})"
        )
        
        save_message(chat_id, "assistant", msg_content, mode=mode)
        
        yield {"token": f"\n{msg_content}\n"}
        yield {
            "done": True,
            "generated_file": download_url,
            "run_output": None,
            "file_id": deliverable["file_id"],
            "filename": filename,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error building deliverable: {e}", exc_info=True)
        err_msg = f"Failed to generate {mode.upper()} document: {str(e)}"
        save_message(chat_id, "assistant", err_msg, mode=mode)
        yield {"token": f"\n\n**Error:** {err_msg}"}
        yield {
            "done": True,
            "generated_file": None,
            "run_output": None,
            "status": "error"
        }
