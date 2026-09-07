"""
Vision and OCR Execution Mode Handlers.
Processes image attachments for visual reasoning, diagram inspection, and OCR extraction.
Supports multi-image analysis, structured output modes, auto-export to Excel for OCR,
and smart caching to avoid redundant re-inference on follow-up questions.
"""

import re
import json
import base64
import hashlib
import time
from pathlib import Path
from typing import AsyncGenerator, Dict, Any, List, Optional
from backend.config import logger, EQUIPMENT_TAG_REGEX, VISION_MODEL_NAME, MODEL_NAME
from backend.ollama_client import call_ollama, filter_thinking, swap_to_model
from backend.db import build_context_messages, save_message


# ── Vision/OCR Analysis Cache ──
# Avoids re-running heavy multimodal inference when the user asks follow-up
# questions about the same image. Keyed by (chat_id, image_content_hash).

class VisionCache:
    """
    In-memory cache for vision/OCR analysis results.
    Stores the final analysis output keyed by (chat_id, image_hash).
    TTL-based expiry ensures stale results don't persist forever.
    """
    DEFAULT_TTL = 3600  # 1 hour

    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}

    def _make_key(self, chat_id: str, image_hash: str) -> str:
        return f"{chat_id}::{image_hash}"

    def store(self, chat_id: str, image_hash: str, analysis: str, is_ocr: bool, image_b64_list: Optional[List[str]] = None):
        key = self._make_key(chat_id, image_hash)
        self._store[key] = {
            "analysis": analysis,
            "is_ocr": is_ocr,
            "timestamp": time.time(),
            "image_b64_list": image_b64_list,  # Store for automatic re-scan
        }
        logger.info(f"[VISION_CACHE] Stored analysis for chat={chat_id} hash={image_hash[:16]}... is_ocr={is_ocr}")

    def get(self, chat_id: str, image_hash: str) -> Optional[Dict[str, Any]]:
        key = self._make_key(chat_id, image_hash)
        entry = self._store.get(key)
        if not entry:
            return None
        # Check TTL
        if (time.time() - entry["timestamp"]) > self.DEFAULT_TTL:
            del self._store[key]
            logger.info(f"[VISION_CACHE] Expired entry for chat={chat_id} hash={image_hash[:16]}...")
            return None
        return entry

    def invalidate(self, chat_id: str, image_hash: str):
        key = self._make_key(chat_id, image_hash)
        if key in self._store:
            del self._store[key]
            logger.info(f"[VISION_CACHE] Invalidated cache for chat={chat_id} hash={image_hash[:16]}...")

    def clear_chat(self, chat_id: str):
        """Remove all cached entries for a given chat session."""
        keys_to_remove = [k for k in self._store if k.startswith(f"{chat_id}::")]
        for k in keys_to_remove:
            del self._store[k]
        if keys_to_remove:
            logger.info(f"[VISION_CACHE] Cleared {len(keys_to_remove)} entries for chat={chat_id}")


# Module-level singleton
_vision_cache = VisionCache()

# Pattern to detect user intent to force a re-scan/re-analyze
RESCAN_PATTERN = re.compile(
    r"\b(re[-\s]?scan|re[-\s]?analyze|re[-\s]?read|re[-\s]?extract|re[-\s]?ocr|"
    r"fir\s*se|dobara|phir\s*se|again|fresh|naya|new\s+scan|re[-\s]?process)\b",
    re.IGNORECASE,
)

# Follow-up question system prompt — uses cached analysis context
FOLLOWUP_SYSTEM_PROMPT = """You are an Industrial AI Assistant answering follow-up questions about a previously analyzed image.
The image has already been analyzed. Use the analysis below to answer the user's new question accurately.
Do NOT say "I cannot see the image" — the analysis was done earlier and is provided to you.

PREVIOUS IMAGE ANALYSIS:
{cached_analysis}

Answer the user's question based on the above analysis. Be specific and accurate."""

SUFFICIENCY_CHECK_PROMPT = """You are a strict Decision Engine.
We previously scanned/analyzed an image and got this PREVIOUS ANALYSIS:
\"\"\"{cached_analysis}\"\"\"

The user is now asking:
\"{user_question}\"

Does this question require re-scanning / re-analyzing the original image because the required information is NOT present or insufficient in the previous analysis?

Reply strictly with a JSON object:
{{"needs_rescan": true/false, "reason": "<short reason>"}}"""


def _compute_image_hash(base64_strings: List[str]) -> str:
    """Compute a stable content hash from base64-encoded image data."""
    h = hashlib.sha256()
    for b64 in sorted(base64_strings):
        # Hash first 8KB of each image for speed (sufficient for uniqueness)
        h.update(b64[:8192].encode("utf-8"))
    return h.hexdigest()


async def _check_sufficiency(cached_analysis: str, user_question: str) -> bool:
    """
    Uses the text model (gemma4-e4b) to check if the cached analysis
    contains enough information to answer the user's follow-up question.
    Returns True if re-scan is needed, False if cache is sufficient.
    """
    prompt = SUFFICIENCY_CHECK_PROMPT.format(
        cached_analysis=cached_analysis,
        user_question=user_question,
    )
    try:
        result = await call_ollama(
            messages=[{"role": "user", "content": prompt}],
            stream=False,
            temperature=0.0,
            json_mode=True,
            model=MODEL_NAME,
        )
        parsed = json.loads(result)
        needs_rescan = parsed.get("needs_rescan", False)
        reason = parsed.get("reason", "")
        if isinstance(needs_rescan, str):
            needs_rescan = needs_rescan.lower() == "true"
        logger.info(f"[SUFFICIENCY_CHECK] needs_rescan={needs_rescan} reason={reason}")
        return needs_rescan
    except Exception as e:
        logger.warning(f"[SUFFICIENCY_CHECK] Failed to parse response, defaulting to no-rescan: {e}")
        return False


OCR_SYSTEM_PROMPT = """You are a precision Industrial OCR & Document Extraction Assistant.
Your task is to extract, transcribe, and structure text, equipment readings, tag IDs, and numbers from the provided image verbatim.
Do not hallucinate or invent characters. Transcribe tabular columns, form fields, and error codes accurately.

OUTPUT FORMAT:
Return your response as valid JSON with this structure:
{
  "raw_text": "<full extracted text verbatim>",
  "tables": [{"headers": ["col1", "col2"], "rows": [["val1", "val2"]]}],
  "form_fields": [{"label": "<field label>", "value": "<field value>"}],
  "equipment_tags": ["F-101", "P-201A"],
  "confidence": 8
}

RULES:
1. "raw_text": Transcribe ALL visible text line by line.
2. "tables": If tabular data is visible, extract it with proper headers and rows. If no tables, return empty array.
3. "form_fields": If form-like label:value pairs are visible, extract them. If none, return empty array.
4. "equipment_tags": List all equipment tag IDs matching patterns like X-NNN, XX-NNNN, XXX-NNN (e.g., F-101, CDU-1001, TK-501).
5. "confidence": Self-rate your extraction accuracy from 1-10 (10 = perfect, fully legible).
6. Return ONLY valid JSON. No markdown, no explanation outside the JSON."""

VISION_SYSTEM_PROMPT = """You are an Industrial Computer Vision & Inspection Assistant.
Your task is to visually inspect, interpret, and describe the provided image, engineering diagram, P&ID schematic, or equipment gauge.
Identify components, flow directions, tags, visible corrosion/anomalies, and explain key operational aspects clearly.

At the end of your analysis, add a line:
**Confidence:** X/10 (where X is your self-rated confidence in the visual interpretation)"""

EQUIPMENT_REGEX_COMPILED = re.compile(EQUIPMENT_TAG_REGEX, re.IGNORECASE)


def encode_image_to_base64(file_path: str) -> Optional[str]:
    """
    Encodes an image or PDF file to a base64 string for multimodal inference.
    Supports PNG, JPG, JPEG, TIFF, BMP, WEBP, and single/multi-page PDFs.
    """
    try:
        if not file_path:
            return None
        # Check if already a raw or prefixed base64 string
        if file_path.startswith("data:image"):
            return file_path.split(",", 1)[-1]
        
        # Check if valid file path
        p = Path(file_path)
        if p.exists() and p.is_file():
            from PIL import Image
            import io
            
            ext = p.suffix.lower()
            
            # Handle PDF document pages
            if ext == ".pdf":
                try:
                    import pypdf
                    reader = pypdf.PdfReader(str(p))
                    # Check if pages contain embedded images
                    for page in reader.pages:
                        for img_obj in page.images:
                            img = Image.open(io.BytesIO(img_obj.data)).convert("RGB")
                            buf = io.BytesIO()
                            img.save(buf, format="JPEG", quality=90)
                            return base64.b64encode(buf.getvalue()).decode("utf-8")
                except Exception as pdf_err:
                    logger.warning(f"[VISION/OCR] PDF image extraction fallback for {p.name}: {pdf_err}")
            
            # Standard image handling with RGB normalization & smart resizing
            raw_bytes = p.read_bytes()
            try:
                img = Image.open(io.BytesIO(raw_bytes))
                if img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")
                original_size = img.size
                max_dim = 1920
                ratio = min(max_dim / img.width, max_dim / img.height)
                if ratio < 1.0:
                    new_size = (int(img.width * ratio), int(img.height * ratio))
                    img = img.resize(new_size, Image.LANCZOS)
                
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=88)
                norm_bytes = buf.getvalue()
                return base64.b64encode(norm_bytes).decode("utf-8")
            except Exception:
                # Direct raw bytes fallback
                return base64.b64encode(raw_bytes).decode("utf-8")
        
        # Fallback: check if it's base64 encoded text
        try:
            base64.b64decode(file_path, validate=True)
            return file_path
        except Exception:
            pass
    except Exception as e:
        logger.warning(f"[VISION] Failed to encode image {file_path}: {e}")
    return None


def _ocr_post_process(text: str) -> str:
    """Cleans up common OCR artifacts from extracted text."""
    # Merge hyphenated line breaks: equip-\nment -> equipment
    text = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', text)
    # Remove double spaces
    text = re.sub(r'  +', ' ', text)
    # Remove orphan punctuation at line start
    text = re.sub(r'^\s*[,;:]\s*', '', text, flags=re.MULTILINE)
    # Normalize line endings
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _detect_equipment_tags(text: str) -> List[str]:
    """Extracts all equipment tags from OCR text."""
    matches = EQUIPMENT_REGEX_COMPILED.findall(text)
    return list(set(m.upper() for m in matches))


async def _auto_export_ocr_to_xlsx(ocr_data: Dict, chat_id: str) -> Optional[Dict[str, Any]]:
    """If OCR detected tabular data, auto-generate an XLSX file and return metadata."""
    tables = ocr_data.get("tables", [])
    if not tables:
        return None
    
    try:
        from backend.deliverables import create_deliverable_file
        
        # Build a plan from OCR tables
        blocks = []
        for t_idx, table in enumerate(tables):
            headers = table.get("headers", [])
            rows_data = table.get("rows", [])
            if headers and rows_data:
                all_rows = [headers] + rows_data
                blocks.append({
                    "type": "table",
                    "text": f"OCR Extracted Table {t_idx + 1}",
                    "rows": all_rows
                })
        
        if blocks:
            plan = {
                "title": "OCR Extracted Data",
                "filename": "ocr_extraction.xlsx",
                "blocks": blocks
            }
            result = create_deliverable_file(plan, mode="excel", chat_id=chat_id)
            logger.info(f"[OCR] Auto-exported {len(tables)} tables to XLSX: {result['filename']}")
            return result
    except Exception as e:
        logger.warning(f"[OCR] Auto-export to XLSX failed: {e}")
    
    return None


async def _handle_cached_followup(
    chat_id: str,
    user_message: str,
    cached_analysis: str,
    is_ocr: bool,
    think: bool,
    cached_image_b64: Optional[List[str]] = None,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Handles a follow-up question using cached vision/OCR analysis.
    First checks if the cached analysis has sufficient info via sufficiency check.
    If not sufficient and we have cached image bytes, triggers automatic re-scan.
    Otherwise answers from cache using the text LLM (gemma4-e4b).
    """
    mode_name = "ocr" if is_ocr else "vision"
    logger.info(f"[{mode_name.upper()}_CACHE_HIT] Checking sufficiency for chat={chat_id}")

    # ── Sufficiency Check: Does cached analysis have enough info? ──
    yield {"token": f"🧠 Checking if previous {mode_name.upper()} analysis has the requested details...\n\n"}
    needs_rescan = await _check_sufficiency(cached_analysis, user_message)

    if needs_rescan and cached_image_b64:
        # ── Auto Re-scan: Cached analysis is insufficient ──
        logger.info(f"[{mode_name.upper()}_AUTO_RESCAN] Cached analysis insufficient, triggering fresh scan")
        yield {"token": f"🔍 Requested detail not in previous analysis. Running fresh {mode_name.upper()} scan...\n\n"}

        # Swap: unload text model → load vision model
        await swap_to_model(VISION_MODEL_NAME, MODEL_NAME)

        system_prompt = OCR_SYSTEM_PROMPT if is_ocr else VISION_SYSTEM_PROMPT
        save_message(chat_id, "user", user_message, mode=mode_name)
        messages = await build_context_messages(chat_id, system_prompt, user_message)

        gen_tokens = []
        token_gen = await call_ollama(
            messages,
            stream=True,
            temperature=0.1 if is_ocr else 0.4,
            think=think,
            images=cached_image_b64,
            model=VISION_MODEL_NAME,
        )

        async for chunk in token_gen:
            chunk_type = chunk.get("type", "content")
            token_text = chunk.get("token", "")
            if chunk_type == "thinking":
                if think:
                    yield {"thinking": token_text, "event": "step", "step_type": "thought", "content": token_text}
            else:
                gen_tokens.append(token_text)
                yield {"token": token_text, "event": "step", "step_type": "token", "content": token_text}

        final_content = filter_thinking("".join(gen_tokens))

        # Swap back: unload vision → load text model
        await swap_to_model(MODEL_NAME, VISION_MODEL_NAME)

        # Update cache with the new, more detailed analysis
        if cached_image_b64:
            image_hash = _compute_image_hash(cached_image_b64)
            _vision_cache.store(chat_id, image_hash, final_content, is_ocr, cached_image_b64)

        save_message(chat_id, "assistant", final_content, mode=mode_name)
        yield {
            "done": True,
            "generated_file": None,
            "run_output": None,
            "status": "success",
            "event": "final_answer",
            "content": final_content,
        }
        return

    # ── Cache Sufficient: Answer via text LLM (gemma4-e4b) ──
    logger.info(f"[{mode_name.upper()}_CACHE_HIT] Answering follow-up via text LLM for chat={chat_id}")
    yield {"token": f"⚡ Using cached {mode_name.upper()} analysis (no re-scan needed)...\n\n"}

    # Build system prompt with cached analysis injected
    system_with_context = FOLLOWUP_SYSTEM_PROMPT.format(cached_analysis=cached_analysis)

    save_message(chat_id, "user", user_message, mode=mode_name)
    messages = await build_context_messages(chat_id, system_with_context, user_message)

    gen_tokens = []
    token_gen = await call_ollama(
        messages,
        stream=True,
        temperature=0.3,
        think=think,
        images=None,  # No images — using cached text analysis
        model=MODEL_NAME,  # Use text model (gemma4-e4b)
    )

    async for chunk in token_gen:
        chunk_type = chunk.get("type", "content")
        token_text = chunk.get("token", "")
        if chunk_type == "thinking":
            if think:
                yield {"thinking": token_text, "event": "step", "step_type": "thought", "content": token_text}
        else:
            gen_tokens.append(token_text)
            yield {"token": token_text, "event": "step", "step_type": "token", "content": token_text}

    final_content = filter_thinking("".join(gen_tokens))
    save_message(chat_id, "assistant", final_content, mode=mode_name)
    yield {
        "done": True,
        "generated_file": None,
        "run_output": None,
        "status": "success",
        "event": "final_answer",
        "content": final_content,
    }


async def handle_vision_mode(
    chat_id: str,
    user_message: str,
    attachments: Optional[List[str]] = None,
    is_ocr: bool = False,
    think: bool = False,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Executes Vision or OCR multimodal analysis with:
    - Smart caching: reuses previous analysis for follow-up questions on the same image
    - Multi-image support (encodes all attachments)
    - Image preprocessing (auto-resize >4MB images)
    - Structured OCR output (JSON with tables, form fields, equipment tags)
    - Auto-export OCR tables to XLSX
    - Confidence scoring
    - Force re-scan via keywords like "re-scan", "dobara", "phir se", etc.
    """
    mode_name = "ocr" if is_ocr else "vision"
    system_prompt = OCR_SYSTEM_PROMPT if is_ocr else VISION_SYSTEM_PROMPT
    logger.info(f"[{mode_name.upper()}_MODE] chat_id={chat_id} think={think} attachments={attachments}")

    # Encode all image attachments (multi-image support)
    image_base64_list: List[str] = []
    if attachments:
        for att in attachments:
            b64 = encode_image_to_base64(att)
            if b64:
                image_base64_list.append(b64)

    # ── Cache Check ──
    # If we have images, check if we already analyzed them in this chat
    force_rescan = bool(RESCAN_PATTERN.search(user_message))
    if force_rescan:
        logger.info(f"[{mode_name.upper()}_CACHE] Force re-scan requested by user")

    if image_base64_list and not force_rescan:
        image_hash = _compute_image_hash(image_base64_list)
        cached = _vision_cache.get(chat_id, image_hash)
        if cached:
            logger.info(
                f"[{mode_name.upper()}_CACHE] HIT — reusing cached analysis for chat={chat_id} "
                f"hash={image_hash[:16]}... (age={int(time.time() - cached['timestamp'])}s)"
            )
            # Serve follow-up via text LLM with cached analysis + sufficiency check
            async for event in _handle_cached_followup(
                chat_id, user_message, cached["analysis"], cached["is_ocr"], think,
                cached_image_b64=cached.get("image_b64_list"),
            ):
                yield event
            return
    elif not image_base64_list:
        # No images attached — check if there's ANY cached analysis for this chat
        # This handles the case where user sends a text follow-up without re-attaching the image
        for key, entry in list(_vision_cache._store.items()):
            if key.startswith(f"{chat_id}::") and not force_rescan:
                if (time.time() - entry["timestamp"]) <= VisionCache.DEFAULT_TTL:
                    logger.info(
                        f"[{mode_name.upper()}_CACHE] HIT (no-attachment follow-up) for chat={chat_id}"
                    )
                    async for event in _handle_cached_followup(
                        chat_id, user_message, entry["analysis"], entry["is_ocr"], think,
                        cached_image_b64=entry.get("image_b64_list"),
                    ):
                        yield event
                    return
                break  # Expired — fall through to require re-attachment

    # Invalidate cache if force re-scan
    if force_rescan and image_base64_list:
        image_hash = _compute_image_hash(image_base64_list)
        _vision_cache.invalidate(chat_id, image_hash)

    # ── Fresh Vision/OCR Inference ──
    # Swap: unload text model → load vision model
    yield {"token": f"🔄 Loading vision model for {mode_name.upper()} analysis...\n\n"}
    await swap_to_model(VISION_MODEL_NAME, MODEL_NAME)

    # Multi-image comparison prompt
    if len(image_base64_list) > 1 and not is_ocr:
        user_message = f"{user_message}\n\n[{len(image_base64_list)} images provided. Compare and analyze all images, noting differences and similarities.]"

    save_message(chat_id, "user", user_message, mode=mode_name)
    messages = await build_context_messages(chat_id, system_prompt, user_message)

    yield {"token": f"Processing {mode_name.upper()} analysis on {len(image_base64_list)} image(s)...\n\n"}

    gen_tokens = []
    token_gen = await call_ollama(
        messages,
        stream=True,
        temperature=0.1 if is_ocr else 0.4,
        think=think,
        images=image_base64_list if image_base64_list else None,
        model=VISION_MODEL_NAME,
    )

    async for chunk in token_gen:
        chunk_type = chunk.get("type", "content")
        token_text = chunk.get("token", "")
        if chunk_type == "thinking":
            if think:
                yield {"thinking": token_text, "event": "step", "step_type": "thought", "content": token_text}
        else:
            gen_tokens.append(token_text)
            yield {"token": token_text, "event": "step", "step_type": "token", "content": token_text}

    final_content = filter_thinking("".join(gen_tokens))
    
    # ── OCR Post-Processing ──
    generated_file = None
    if is_ocr:
        # Try to parse structured JSON output
        ocr_data = None
        try:
            # Strip markdown code fencing if present
            clean = final_content.strip()
            if clean.startswith("```"):
                lines = clean.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                clean = "\n".join(lines).strip()
            ocr_data = json.loads(clean)
        except (json.JSONDecodeError, ValueError):
            pass
        
        if ocr_data and isinstance(ocr_data, dict):
            # Clean up raw text
            raw_text = ocr_data.get("raw_text", "")
            if raw_text:
                ocr_data["raw_text"] = _ocr_post_process(raw_text)
            
            # Auto-detect equipment tags if model missed them
            detected_tags = _detect_equipment_tags(ocr_data.get("raw_text", ""))
            existing_tags = set(ocr_data.get("equipment_tags", []))
            ocr_data["equipment_tags"] = list(existing_tags.union(set(detected_tags)))
            
            # Auto-export tables to XLSX
            xlsx_result = await _auto_export_ocr_to_xlsx(ocr_data, chat_id)
            if xlsx_result:
                generated_file = xlsx_result.get("download_url")
                export_msg = f"\n\n📊 **Auto-exported {len(ocr_data.get('tables', []))} table(s) to Excel:** [{xlsx_result['filename']}]({xlsx_result['download_url']})"
                final_content += export_msg
                yield {"token": export_msg}
            
            # Highlight equipment tags in output
            if ocr_data.get("equipment_tags"):
                tags_str = ", ".join(ocr_data["equipment_tags"])
                tag_msg = f"\n\n🏷️ **Equipment Tags Detected:** {tags_str}"
                final_content += tag_msg
                yield {"token": tag_msg}
        else:
            # Freeform text mode — still apply post-processing
            final_content = _ocr_post_process(final_content)
            
            # Auto-detect equipment tags
            detected_tags = _detect_equipment_tags(final_content)
            if detected_tags:
                tags_str = ", ".join(detected_tags)
                tag_msg = f"\n\n🏷️ **Equipment Tags Detected:** {tags_str}"
                final_content += tag_msg
                yield {"token": tag_msg}

    # ── Store result in cache for future follow-ups (including image bytes for re-scan) ──
    if image_base64_list:
        image_hash = _compute_image_hash(image_base64_list)
        _vision_cache.store(chat_id, image_hash, final_content, is_ocr, image_base64_list)

    # Swap back: unload vision model → load text model (gemma4-e4b)
    await swap_to_model(MODEL_NAME, VISION_MODEL_NAME)
    
    save_message(chat_id, "assistant", final_content, mode=mode_name)
    yield {
        "done": True,
        "generated_file": generated_file,
        "run_output": None,
        "status": "success",
        "event": "final_answer",
        "content": final_content,
    }
