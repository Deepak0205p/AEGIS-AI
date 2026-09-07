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

DOC_PLANNER_SYSTEM_PROMPT = """You are an expert document architect and technical writer for an industrial enterprise platform.
Your task is to create a complete, comprehensive, and highly professional document plan in JSON format based on the user's request.

DOCUMENT SCHEMA:
{
  "title": "<Professional Document Title>",
  "filename": "<safe_descriptive_filename.docx>",
  "blocks": [
    {
      "type": "heading",
      "text": "Executive Summary",
      "level": 1
    },
    {
      "type": "paragraph",
      "text": "Detailed, thorough paragraph explaining the objective, scope, background, and operational context."
    },
    {
      "type": "bullets",
      "items": [
        "Key operational parameter or requirement 1",
        "Key operational parameter or requirement 2",
        "Key operational parameter or requirement 3"
      ]
    },
    {
      "type": "heading",
      "text": "Technical Specifications & Parameters",
      "level": 1
    },
    {
      "type": "table",
      "rows": [
        ["Parameter / Component", "Design Spec", "Operating Range", "Status"],
        ["Operating Pressure", "15.2 bar", "14.0 - 16.5 bar", "Normal"],
        ["Process Temperature", "240 °C", "220 - 260 °C", "Normal"],
        ["Flow Rate", "450 m3/h", "400 - 500 m3/h", "Optimal"]
      ]
    },
    {
      "type": "heading",
      "text": "Standard Operating & Safety Procedures",
      "level": 1
    },
    {
      "type": "bullets",
      "items": [
        "Pre-start inspection of all isolation valves and pressure relief devices",
        "Continuous monitoring of differential pressure and seal flush systems",
        "Emergency shutdown protocol execution upon high vibration alarm"
      ]
    }
  ]
}

RULES:
1. Always generate a COMPLETE, ready-to-render document with multi-paragraph content, structured tables, and clear headings (level 1, 2, 3).
2. Populate realistic, domain-accurate engineering/operational data, metrics, standards, and procedures.
3. Use a mix of headings, paragraphs, bullet lists, and tables to make the document rich and well-structured.
4. Output ONLY valid, parseable JSON. Do not include markdown commentary or reasoning outside the JSON."""


def parse_plan_json(raw_text: str) -> Optional[Dict[str, Any]]:
    """Extracts and parses JSON object from model output with multi-strategy fallbacks."""
    if not raw_text:
        return None
    import re
    raw = raw_text.strip()
    
    # Strategy 1: Strip markdown code fencing if present
    cleaned = raw
    if "```json" in cleaned:
        cleaned = cleaned.split("```json")[1].split("```")[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```")[1].split("```")[0].strip()

    try:
        data = json.loads(cleaned)
        if isinstance(data, dict) and ("blocks" in data or "sheets" in data or "title" in data):
            return data
        elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            return {"title": "Document", "filename": "document.docx", "blocks": data}
        elif isinstance(data, dict):
            return data
    except Exception:
        pass

    # Strategy 2: Direct load on raw
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    # Strategy 3: Regex extract outermost JSON object {...}
    match = re.search(r'(\{[\s\S]*\})', raw)
    if match:
        try:
            data = json.loads(match.group(1))
            if isinstance(data, dict):
                return data
        except Exception:
            pass

    return None


async def handle_document_mode(
    mode: str,
    chat_id: str,
    user_message: str,
    custom_system_prompt: Optional[str] = None,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Executes Document / Excel / PPT mode:
    1. Plan with json_mode=True, temperature 0.3
    2. Check for explicit NEEDS_INPUT blocks -> ask question and pause if so
    3. Generate genuine binary deliverable with Python
    4. Stream progress and emit final file download link.
    """
    logger.info(f"[{mode.upper()}_MODE] chat_id={chat_id} temperature=0.3 mode={mode}")
    
    system_prompt = custom_system_prompt if custom_system_prompt else DOC_PLANNER_SYSTEM_PROMPT
    save_message(chat_id, "user", user_message, mode=mode)
    messages = await build_context_messages(chat_id, system_prompt, user_message)
    
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
        error_msg = f"Failed to parse document plan from model."
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

    # Normalize plan_data
    if "blocks" not in plan_data and "sheets" not in plan_data:
        plan_data["blocks"] = [{"type": "paragraph", "text": str(plan_data.get("description") or user_message)}]

    # Step 3: Check for explicit NEEDS_INPUT blocks
    blocks = plan_data.get("blocks", [])
    missing_inputs = []
    
    for b in blocks:
        if not isinstance(b, dict):
            continue
        text_val = str(b.get("text", "")).strip()
        status_val = str(b.get("status", "")).strip()
        question = b.get("question")
        
        if (text_val == "NEEDS_INPUT" or status_val == "NEEDS_INPUT") and question:
            missing_inputs.append(question)

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
