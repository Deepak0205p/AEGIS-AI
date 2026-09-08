"""
Vision and OCR Execution Mode Handlers.
Processes image attachments for visual reasoning, diagram inspection, and OCR extraction.
Supports multi-image analysis, structured output modes, auto-export to Excel for OCR,
smart caching to avoid redundant re-inference on follow-up questions, and clean VRAM
model swapping (DeepSeek text LLM <-> Gemma multimodal vision model).
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
FOLLOWUP_SYSTEM_PROMPT = """You are REVEAL, an authoritative Industrial AI Assistant.
A previous visual inspection of the user's uploaded image produced the following verified extraction data:

VERIFIED IMAGE EXTRACTION DATA:
{cached_analysis}

CRITICAL INSTRUCTIONS:
- You HAVE full access to the image's extracted content above.
- Answer the user's question directly and thoroughly based on the verified image data above.
- NEVER state that you cannot see the image or ask the user to describe the image.
- Respond in clear, professional Markdown."""

# DeepSeek final response synthesis prompt from vision extraction data
SYNTHESIS_SYSTEM_PROMPT = """You are REVEAL, an authoritative Industrial AI Assistant.
The vision inspection system has scanned the user's image and extracted the following verified visual details:

VERIFIED IMAGE EXTRACTION DATA:
{extracted_data}

CRITICAL INSTRUCTIONS:
- You HAVE full access to the image's extracted content above.
- Deliver a comprehensive, direct, and well-structured response to the user's request based on the extracted data above.
- NEVER state that you cannot view images or ask the user to describe the image.
- Respond in clear, professional GitHub-flavored Markdown."""

SUFFICIENCY_CHECK_PROMPT = """You are a strict Decision Engine.
We previously scanned/analyzed an image and got this PREVIOUS ANALYSIS:
\"\"\"{cached_analysis}\"\"\"

The user is now asking:
\"{user_question}\"

Does this question require re-scanning / re-analyzing the original image because the required information is NOT present or insufficient in the previous analysis?

Reply strictly with a JSON object:
{{"needs_rescan": true/false, "reason": "<short reason>"}}"""

OCR_SYSTEM_PROMPT = """You are a precision Industrial OCR & Document Extraction Assistant.
Your task is to extract, transcribe, and structure text, equipment readings, tag IDs, and numbers from the provided image verbatim.

STRICT ANTI-HALLUCINATION RULES:
1. Extract ONLY text and numbers that are 100% visible and legible in the image.
2. DO NOT guess, fabricate, or invent numbers, tag IDs, dates, or words.
3. If an area or tag is partially obscured or blurry, mark it verbatim as "[UNREADABLE]".
4. Return ONLY valid JSON format.

OUTPUT FORMAT:
{
  "raw_text": "<verbatim extracted text line by line>",
  "tables": [{"headers": ["col1", "col2"], "rows": [["val1", "val2"]]}],
  "form_fields": [{"label": "<field label>", "value": "<field value>"}],
  "equipment_tags": ["F-101", "P-201A"],
  "confidence": 9
}"""

VISION_SYSTEM_PROMPT = """You are an Expert Industrial Multimodal & Computer Vision Inspector.
Your objective is to provide high-precision, technical visual analysis of industrial diagrams (P&ID, PFD, isometric), equipment photos, analog/digital gauges, control panels, or field assets.

STRICT ANTI-HALLUCINATION & FACTUAL GROUNDING RULES:
1. ONLY describe and report what is directly, verifiably visible in the image.
2. NEVER guess, assume, or invent equipment tags, pressure/temperature values, or failure modes that are not visible.
3. If the user asks about an element not shown in the image (e.g. asking for gauge pressure on a static diagram with no gauges), explicitly state that it is not present in the provided image.
4. Directly answer the user's specific query without adding unnecessary boilerplate or generic template sections.

INSPECTION GUIDELINES:
- **Visual Inventory & Tags:** Report exact equipment tags (e.g., P-101A, MOV-104, TK-501), valve types, and sensors visible.
- **Readings & Gauges:** Read exact needle positions, digital readouts, units (bar, psi, °C, RPM, %), and dial threshold colors if visible.
- **Flow Logic (Diagrams):** Trace connections between visible equipment strictly as drawn.
- **Asset Condition (Photos):** Note visible physical characteristics (corrosion, leakage, valve open/closed position).
- Conclude with a factual summary and **Confidence:** X/10."""

EQUIPMENT_REGEX_COMPILED = re.compile(EQUIPMENT_TAG_REGEX, re.IGNORECASE)


def _enhance_image_quality(img):
    """
    Applies subtle adaptive contrast enhancement and sharpening to make fine technical lines,
    needle pointers, and small text tags extremely crisp for VL patch encoders.
    """
    try:
        from PIL import ImageEnhance, ImageFilter
        
        # Mild sharpening to clarify blurry tag numbers and gauge needles
        img = img.filter(ImageFilter.UnsharpMask(radius=1.5, percent=120, threshold=3))
        
        # Slight contrast boost for readable text on technical diagrams
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.15)
    except Exception as e:
        logger.debug(f"[VISION] Enhancement filter skipped: {e}")
    return img


def encode_image_to_base64(file_path: str) -> Optional[str]:
    """
    Encodes an image or PDF file to a base64 string for multimodal inference.
    Supports PNG, JPG, JPEG, TIFF, BMP, WEBP, and single/multi-page PDFs.
    Ensures high-resolution detail retention, crisp contrast, and dimensions >= 56x56.
    """
    try:
        if not file_path:
            return None

        from PIL import Image
        import io

        # Check if already a raw or data-prefixed base64 string
        clean_b64 = None
        if str(file_path).startswith("data:image"):
            clean_b64 = file_path.split(",", 1)[-1].strip()
        elif len(str(file_path)) > 50:
            clean_b64 = str(file_path).strip()

        if clean_b64:
            try:
                raw_bytes = base64.b64decode(clean_b64)
                
                # Check if decoded payload is a PDF file (%PDF- / 0x25 0x50 0x44 0x46)
                if raw_bytes.startswith(b"%PDF") or clean_b64.startswith("JVBERi0"):
                    try:
                        import fitz  # PyMuPDF
                        doc = fitz.open(stream=raw_bytes, filetype="pdf")
                        for page in doc:
                            pix = page.get_pixmap(dpi=200)
                            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                            img = _enhance_image_quality(img)
                            buf = io.BytesIO()
                            img.save(buf, format="JPEG", quality=95, subsampling=0)
                            return base64.b64encode(buf.getvalue()).decode("utf-8")
                    except Exception as pdf_err:
                        try:
                            import pypdf
                            reader = pypdf.PdfReader(io.BytesIO(raw_bytes))
                            for page in reader.pages:
                                for img_obj in page.images:
                                    img = Image.open(io.BytesIO(img_obj.data)).convert("RGB")
                                    img = _enhance_image_quality(img)
                                    buf = io.BytesIO()
                                    img.save(buf, format="JPEG", quality=95, subsampling=0)
                                    return base64.b64encode(buf.getvalue()).decode("utf-8")
                        except Exception as pypdf_err:
                            logger.warning(f"[VISION/OCR] Could not rasterize base64 PDF: {pypdf_err}")

                img = Image.open(io.BytesIO(raw_bytes))
                if img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")
                # Ensure minimum 56x56 dimensions for VL patch embeddings
                if img.width < 56 or img.height < 56:
                    img = img.resize((max(img.width, 56), max(img.height, 56)), Image.NEAREST)
                
                # Apply quality enhancement
                img = _enhance_image_quality(img)

                # Keep higher resolution threshold for technical blueprints (up to 2560px)
                max_dim = 2560
                ratio = min(max_dim / img.width, max_dim / img.height)
                if ratio < 1.0:
                    new_size = (int(img.width * ratio), int(img.height * ratio))
                    img = img.resize(new_size, Image.LANCZOS)
                
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=95, subsampling=0)
                return base64.b64encode(buf.getvalue()).decode("utf-8")
            except Exception as e:
                logger.warning(f"[VISION] decode error: {e}")
                return clean_b64

        # Check if valid file path
        if len(str(file_path)) < 260:
            p = Path(file_path)
            if p.exists() and p.is_file():
                ext = p.suffix.lower()
                
                # Handle PDF document pages
                if ext == ".pdf":
                    try:
                        import pypdf
                        reader = pypdf.PdfReader(str(p))
                        for page in reader.pages:
                            for img_obj in page.images:
                                img = Image.open(io.BytesIO(img_obj.data)).convert("RGB")
                                if img.width < 56 or img.height < 56:
                                    img = img.resize((max(img.width, 56), max(img.height, 56)), Image.NEAREST)
                                img = _enhance_image_quality(img)
                                buf = io.BytesIO()
                                img.save(buf, format="JPEG", quality=95, subsampling=0)
                                return base64.b64encode(buf.getvalue()).decode("utf-8")
                    except Exception as pdf_err:
                        logger.warning(f"[VISION/OCR] PDF image extraction fallback for {p.name}: {pdf_err}")
                
                # Standard image handling with high-fidelity enhancement
                raw_bytes = p.read_bytes()
                try:
                    img = Image.open(io.BytesIO(raw_bytes))
                    if img.mode not in ("RGB", "L"):
                        img = img.convert("RGB")
                    if img.width < 56 or img.height < 56:
                        img = img.resize((max(img.width, 56), max(img.height, 56)), Image.NEAREST)
                    
                    # Apply quality enhancement filter
                    img = _enhance_image_quality(img)

                    max_dim = 2560
                    ratio = min(max_dim / img.width, max_dim / img.height)
                    if ratio < 1.0:
                        new_size = (int(img.width * ratio), int(img.height * ratio))
                        img = img.resize(new_size, Image.LANCZOS)
                    
                    buf = io.BytesIO()
                    img.save(buf, format="JPEG", quality=95, subsampling=0)
                    norm_bytes = buf.getvalue()
                    return base64.b64encode(norm_bytes).decode("utf-8")
                except Exception:
                    return base64.b64encode(raw_bytes).decode("utf-8")
    except Exception as e:
        logger.warning(f"[VISION] Failed to encode image '{str(file_path)[:40]}...': {e}")
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


def _compute_image_hash(base64_strings: List[str]) -> str:
    """Compute a stable content hash from base64-encoded image data."""
    h = hashlib.sha256()
    for b64 in sorted(base64_strings):
        h.update(b64[:8192].encode("utf-8"))
    return h.hexdigest()


async def _check_sufficiency(cached_analysis: str, user_question: str) -> bool:
    """
    Uses the text model (DeepSeek) to check if the cached analysis
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
    Otherwise answers from cache using the main text LLM (DeepSeek).
    """
    mode_name = "ocr" if is_ocr else "vision"
    logger.info(f"[{mode_name.upper()}_CACHE_HIT] Checking sufficiency for chat={chat_id}")

    # ── Sufficiency Check: Does cached analysis have enough info? ──
    yield {"token": f"🧠 Checking cached {mode_name.upper()} analysis...\n\n"}
    needs_rescan = await _check_sufficiency(cached_analysis, user_message)

    if needs_rescan and cached_image_b64:
        # ── Auto Re-scan: Cached analysis is insufficient ──
        logger.info(f"[{mode_name.upper()}_AUTO_RESCAN] Cached analysis insufficient, triggering fresh scan")
        yield {"token": f"🔍 Requested detail not in previous analysis. Re-scanning image...\n\n"}

        # Step 1: Unload DeepSeek -> Load Vision model (Gemma)
        await swap_to_model(
            target_model=VISION_MODEL_NAME,
            unload_model_name=MODEL_NAME,
            chat_id=chat_id,
            context_to_transfer=f"User requested re-inspection: {user_message}"
        )

        system_prompt = OCR_SYSTEM_PROMPT if is_ocr else VISION_SYSTEM_PROMPT
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_message}]

        # Vision extraction pass
        gen_tokens = []
        token_gen = await call_ollama(
            messages,
            stream=False,
            temperature=0.1 if is_ocr else 0.3,
            think=False,
            images=cached_image_b64,
            model=VISION_MODEL_NAME,
        )
        extracted_content = filter_thinking(str(token_gen))

        # Update cache with the fresh extraction
        image_hash = _compute_image_hash(cached_image_b64)
        _vision_cache.store(chat_id, image_hash, extracted_content, is_ocr, cached_image_b64)

        # Step 2: Unload Gemma -> Load DeepSeek
        await swap_to_model(
            target_model=MODEL_NAME,
            unload_model_name=VISION_MODEL_NAME,
            chat_id=chat_id,
            context_to_transfer=f"Vision/OCR Analysis Output:\n{extracted_content[:1500]}"
        )

        # Step 3: DeepSeek answers user query with extracted context
        synthesis_prompt = SYNTHESIS_SYSTEM_PROMPT.format(extracted_data=extracted_content)
        save_message(chat_id, "user", user_message, mode=mode_name)
        synthesis_messages = await build_context_messages(chat_id, synthesis_prompt, user_message)

        final_tokens = []
        token_stream = await call_ollama(
            synthesis_messages,
            stream=True,
            temperature=0.3,
            think=think,
            images=None,
            model=MODEL_NAME,
        )

        async for chunk in token_stream:
            chunk_type = chunk.get("type", "content")
            token_text = chunk.get("token", "")
            if chunk_type == "thinking":
                if think:
                    yield {"thinking": token_text, "event": "step", "step_type": "thought", "content": token_text}
            else:
                final_tokens.append(token_text)
                yield {"token": token_text, "event": "step", "step_type": "token", "content": token_text}

        final_content = filter_thinking("".join(final_tokens))
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

    # ── Cache Sufficient: Answer via main text LLM (DeepSeek) with cached analysis ──
    logger.info(f"[{mode_name.upper()}_CACHE_HIT] Answering follow-up via DeepSeek text LLM for chat={chat_id}")
    yield {"token": f"⚡ Answering from cached {mode_name.upper()} data (no re-scan needed)...\n\n"}

    followup_messages = [
        {
            "role": "system",
            "content": (
                f"{FOLLOWUP_SYSTEM_PROMPT.format(cached_analysis=cached_analysis)}\n\n"
                f"### VERIFIED IMAGE EXTRACTION DATA (ALREADY SCANNED):\n"
                f"{cached_analysis}\n\n"
                f"Use the verified image extraction data above to directly answer the user's follow-up question."
            )
        },
        {
            "role": "user",
            "content": user_message
        }
    ]
    save_message(chat_id, "user", user_message, mode=mode_name)

    gen_tokens = []
    token_gen = await call_ollama(
        followup_messages,
        stream=True,
        temperature=0.3,
        think=think,
        images=None,  # No images — using cached text analysis
        model=MODEL_NAME,  # Use main text model (DeepSeek)
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
    1. Check cache: if image already analyzed in this chat, reuse cache with DeepSeek without loading vision model.
    2. Model Swap 1: Unload DeepSeek -> Load Gemma (VISION_MODEL_NAME).
    3. Multimodal Inference: Gemma extracts visual findings, diagram interpretation, or OCR table/text data.
    4. Store extracted findings in _vision_cache.
    5. Model Swap 2: Unload Gemma -> Load DeepSeek (MODEL_NAME) with visual findings in context handoff.
    6. Synthesis: DeepSeek synthesizes and streams the final, authoritative response to the user.
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
            async for event in _handle_cached_followup(
                chat_id, user_message, cached["analysis"], cached["is_ocr"], think,
                cached_image_b64=cached.get("image_b64_list"),
            ):
                yield event
            return
    elif not image_base64_list:
        # No images attached — check if there's ANY cached analysis for this chat
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
                break

    # Invalidate cache if force re-scan
    if force_rescan and image_base64_list:
        image_hash = _compute_image_hash(image_base64_list)
        _vision_cache.invalidate(chat_id, image_hash)

    # ── Step 1: Model Swap (Unload DeepSeek -> Load Gemma) ──
    yield {"token": f"🔄 Unloading DeepSeek & Loading Vision Model ({VISION_MODEL_NAME})...\n\n"}
    await swap_to_model(
        target_model=VISION_MODEL_NAME,
        unload_model_name=MODEL_NAME,
        chat_id=chat_id,
        context_to_transfer=f"User requested {mode_name.upper()} task: {user_message}"
    )

    # Multi-image comparison prompt
    vision_prompt_text = user_message
    if len(image_base64_list) > 1 and not is_ocr:
        vision_prompt_text = f"{user_message}\n\n[{len(image_base64_list)} images provided. Compare and analyze all images, noting differences and similarities.]"

    vision_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": vision_prompt_text}
    ]

    # ── Direct Stream from Vision Model (Zero-Loss Grounded Generation) ──
    save_message(chat_id, "user", user_message, mode=mode_name)
    
    # Handle empty or attachment-only user prompts
    clean_user_prompt = user_message.strip() if user_message else ""
    if not clean_user_prompt or re.match(r"^\s*(analyze attached:?|inspect attached:?|attached:?|image:?)\s*[\w\.\-_,\s]*$", clean_user_prompt, re.IGNORECASE):
        clean_user_prompt = "Examine this image in full detail. Identify and describe all visible components, equipment tags, process flows, vessels, instruments, and readings."

    vision_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": clean_user_prompt}
    ]

    # ── Step 1: Extract Raw Visual Details via Qwen2.5-VL into Temporary Variable ──
    yield {"token": f"🔍 Scanning image with {VISION_MODEL_NAME}...\n\n"}
    
    raw_vision_output = await call_ollama(
        vision_messages,
        stream=False,
        temperature=0.05 if is_ocr else 0.15,
        think=False,
        images=image_base64_list if image_base64_list else None,
        model=VISION_MODEL_NAME,
    )
    raw_visual_extracted_data = filter_thinking(str(raw_vision_output))
    logger.info(f"[{mode_name.upper()}] Qwen2.5-VL raw extraction completed ({len(raw_visual_extracted_data)} chars)")

    # ── Step 2: Model Swap (Unload Qwen -> Load Gemma 4 E4B) ──
    PROFESSIONAL_REWRITER_MODEL = "gemma4-e4b:latest"
    yield {"token": f"✨ Formatting & polishing report with Gemma 4 E4B...\n\n"}
    await swap_to_model(
        target_model=PROFESSIONAL_REWRITER_MODEL,
        unload_model_name=VISION_MODEL_NAME,
        chat_id=chat_id,
        context_to_transfer=f"Raw Vision Extraction:\n{raw_visual_extracted_data[:2000]}"
    )

    # ── Step 3: Professional Rewriting via Gemma 4 E4B (Strictly Zero Data Modification) ──
    rewrite_messages = [
        {
            "role": "system",
            "content": (
                "You are an Industrial Operations Technical Editor. "
                "You have been provided with raw verified visual inspection data extracted directly from an engineering diagram or image by a vision sensor model. "
                "YOUR SOLE TASK: Rewrite and format this extracted inspection data into a clean, highly professional, executive industrial markdown report.\n\n"
                "STRICT GROUNDING & FIDELITY CONSTRAINTS:\n"
                "1. PRESERVE ALL extracted equipment tags, numbers, vessel names, sensor labels, and readings VERBATIM.\n"
                "2. DO NOT add, invent, modify, or fabricate any data, values, or components not present in the extraction data.\n"
                "3. If the extraction mentions an element is not visible or unreadable, keep it exactly as reported.\n"
                "4. Structure the report with clear headings, bullet points, and neat tables for readability.\n"
                "5. FORMATTING RULE: Write in clean, standard Markdown only. NEVER wrap tags or names in LaTeX syntax like $\\text{...}$ or dollar signs."
            )
        },
        {
            "role": "user",
            "content": (
                f"### RAW VERIFIED VISUAL EXTRACTION DATA:\n"
                f"\"\"\"\n{raw_visual_extracted_data}\n\"\"\"\n\n"
                f"User Instruction: {clean_user_prompt}\n\n"
                f"Please produce a clear, authoritative, and professionally formatted technical inspection report strictly based on the extraction data above."
            )
        }
    ]

    gen_tokens = []
    token_gen = await call_ollama(
        rewrite_messages,
        stream=True,
        temperature=0.2,
        think=think,
        images=None,
        model=PROFESSIONAL_REWRITER_MODEL,
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

    # Cache for follow-ups
    if image_base64_list:
        image_hash = _compute_image_hash(image_base64_list)
        _vision_cache.store(chat_id, image_hash, final_content, is_ocr, image_base64_list)

    # ── OCR Post-Processing if applicable ──
    generated_file = None
    extra_ocr_info = ""
    if is_ocr:
        ocr_data = None
        try:
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
            raw_text = ocr_data.get("raw_text", "")
            if raw_text:
                ocr_data["raw_text"] = _ocr_post_process(raw_text)

            detected_tags = _detect_equipment_tags(ocr_data.get("raw_text", ""))
            existing_tags = set(ocr_data.get("equipment_tags", []))
            ocr_data["equipment_tags"] = list(existing_tags.union(set(detected_tags)))

            xlsx_result = await _auto_export_ocr_to_xlsx(ocr_data, chat_id)
            if xlsx_result:
                generated_file = xlsx_result.get("download_url")
                extra_ocr_info += f"\n\n📊 **Auto-exported {len(ocr_data.get('tables', []))} table(s) to Excel:** [{xlsx_result['filename']}]({xlsx_result['download_url']})"

            if ocr_data.get("equipment_tags"):
                tags_str = ", ".join(ocr_data["equipment_tags"])
                extra_ocr_info += f"\n\n🏷️ **Equipment Tags Detected:** {tags_str}"
        else:
            final_content = _ocr_post_process(final_content)
            detected_tags = _detect_equipment_tags(final_content)
            if detected_tags:
                tags_str = ", ".join(detected_tags)
                extra_ocr_info += f"\n\n🏷️ **Equipment Tags Detected:** {tags_str}"

    if extra_ocr_info:
        final_content += extra_ocr_info
        yield {"token": extra_ocr_info}

    save_message(chat_id, "assistant", final_content, mode=mode_name)
    yield {
        "done": True,
        "generated_file": generated_file,
        "run_output": None,
        "status": "success",
        "event": "final_answer",
        "content": final_content,
        "model_id": VISION_MODEL_NAME,
        "routed_by": mode_name,
    }
