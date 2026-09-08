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

DOC_PLANNER_SYSTEM_PROMPT = """You are an expert technical author, executive editor, and enterprise document architect.
Your objective: Autonomously design and author a comprehensive, fully tailored document (.docx) based on the user's specific request and domain.

AUTONOMOUS DOCUMENT DESIGN PRINCIPLES:
1. TOTAL STRUCTURAL FREEDOM: Do NOT follow a canned template. YOU autonomously decide the ideal structure, section hierarchy (H1, H2, H3), depth of prose, number of sections, tables, bullet lists, or callouts best suited to the topic.
2. ADAPTIVE FORMATTING:
   - For an SOP or Standard: Write formal procedures, step-by-step numbered steps, safety warnings, and compliance criteria.
   - For an Inspection / Technical Report: Structure background, inspection methodology, measurement tables, findings, and action items.
   - For an Essay / Overview / Brief: Use rich narrative prose across well-structured sections and key data points.
3. IN-DEPTH, PROFESSIONAL WRITING: Write rich, detailed, articulate prose. Provide substantial domain-accurate detail, context, and complete tables.
4. STRICT TOPIC FIDELITY: Maintain 100% focus on the user's prompt.

OUTPUT JSON SCHEMA:
Return ONLY valid JSON matching this schema:
{
  "title": "Document Title",
  "filename": "document_name.docx",
  "blocks": [
    { "type": "heading", "text": "Section Title", "level": 1 },
    { "type": "paragraph", "text": "Comprehensive paragraph text..." },
    { "type": "bullets", "items": ["Key point 1", "Key point 2"] },
    { "type": "table", "rows": [["Col 1", "Col 2"], ["Val 1", "Val 2"]] }
  ]
}

RULES:
- Return ONLY the raw JSON object. Do not include markdown code block backticks, comments, or explanations outside the JSON."""


def parse_plan_json(raw_text: str) -> Optional[Dict[str, Any]]:
    """Extracts and parses JSON object from model output with multi-strategy fallbacks and truncated JSON auto-repair."""
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

    for candidate in [cleaned, raw]:
        try:
            data = json.loads(candidate)
            if isinstance(data, dict):
                return data
            elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                return {"title": "Document", "filename": "document.docx", "blocks": data}
        except Exception:
            pass

    # Strategy 2: Regex extract outermost JSON object {...}
    match = re.search(r'(\{[\s\S]*\})', raw)
    if match:
        try:
            data = json.loads(match.group(1))
            if isinstance(data, dict):
                return data
        except Exception:
            pass

    # Strategy 3: Truncated JSON Auto-Closer
    # If the JSON was cut off due to token length, automatically close unclosed strings, arrays, and braces
    try:
        partial = raw
        if "{" in partial:
            partial = partial[partial.find("{"):]
            # Close unclosed strings
            if partial.count('"') % 2 != 0:
                partial += '"'
            # Close brackets and braces
            open_brackets = partial.count('[') - partial.count(']')
            open_braces = partial.count('{') - partial.count('}')
            partial += (']' * max(0, open_brackets)) + ('}' * max(0, open_braces))
            data = json.loads(partial)
            if isinstance(data, dict) and ("blocks" in data or "title" in data or "sheets" in data):
                logger.info("[DOCS_MODE] Successfully auto-repaired truncated JSON document plan")
                return data
    except Exception:
        pass

    # Strategy 4: Fallback parser from prose/markdown (convert any text response into clean docx blocks)
    if len(raw) > 30 and not raw.startswith("{"):
        blocks = []
        for line in raw.split("\n"):
            line_s = line.strip()
            if not line_s:
                continue
            if line_s.startswith("#"):
                lvl = min(3, len(line_s) - len(line_s.lstrip("#")))
                blocks.append({"type": "heading", "text": line_s.lstrip("# ").strip(), "level": max(1, lvl)})
            elif line_s.startswith(("-", "*", "•")):
                blocks.append({"type": "bullets", "items": [line_s.lstrip("-*• ").strip()]})
            else:
                blocks.append({"type": "paragraph", "text": line_s})
        if blocks:
            logger.info("[DOCS_MODE] Converted markdown/prose output into structured document blocks")
            return {"title": "Document", "filename": "document.docx", "blocks": blocks}

    return None


async def handle_document_mode(
    mode: str,
    chat_id: str,
    user_message: str,
    custom_system_prompt: Optional[str] = None,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Executes Document / Excel / PPT mode:
    1. Plan with json_mode=True, max_tokens=8192 for full documents
    2. Check for explicit NEEDS_INPUT blocks -> ask question and pause if so
    3. Generate genuine binary deliverable with Python
    4. Stream progress and emit final file download link.
    """
    logger.info(f"[{mode.upper()}_MODE] chat_id={chat_id} temperature=0.3 mode={mode}")
    
    system_prompt = custom_system_prompt if custom_system_prompt else DOC_PLANNER_SYSTEM_PROMPT
    save_message(chat_id, "user", user_message, mode=mode)
    messages = await build_context_messages(chat_id, system_prompt, user_message)
    
    yield {"token": f"Planning {mode.upper()} structure based on conversation data...\n"}
    
    # Step 1: Call Ollama with json_mode=True and balanced token ceiling
    plan_raw = await call_ollama(messages, stream=False, temperature=0.3, max_tokens=4096, json_mode=True)
    plan_data = parse_plan_json(str(plan_raw))
    
    # Step 2: Retry once if JSON parse failed
    if not plan_data:
        yield {"token": "[Validating document schema...]\n"}
        retry_messages = messages + [
            {"role": "assistant", "content": str(plan_raw)},
            {"role": "user", "content": "Return ONLY valid JSON matching the schema."}
        ]
        retry_raw = await call_ollama(retry_messages, stream=False, temperature=0.2, max_tokens=4096, json_mode=True)
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
