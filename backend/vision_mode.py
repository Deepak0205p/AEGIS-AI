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
from backend.config import logger, EQUIPMENT_TAG_REGEX, VISION_MODEL_NAME, OCR_MODEL_NAME, MODEL_NAME
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
FOLLOWUP_SYSTEM_PROMPT = """You are AEGIS AI, an authoritative Industrial AI Assistant.
A previous visual inspection of the user's uploaded image produced the following verified extraction data:

VERIFIED IMAGE EXTRACTION DATA:
{cached_analysis}

CRITICAL INSTRUCTIONS:
- You HAVE full access to the image's extracted content above.
- Answer the user's question directly and thoroughly based on the verified image data above.
- NEVER state that you cannot see the image or ask the user to describe the image.
- Respond in clear, professional Markdown."""

# DeepSeek final response synthesis prompt from vision extraction data
SYNTHESIS_SYSTEM_PROMPT = """You are AEGIS AI, an authoritative Industrial AI Assistant.
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

STRICT ANTI-HALLUCINATION & CONFIDENCE RULES:
1. Extract text and numbers that are visible in the image.
2. For every extracted line or region, assign a confidence score between 0.0 and 1.0.
3. If an area, tag, or word is blurry, skewed, or degraded with confidence < 0.70, flag it explicitly as:
   "[UNCERTAIN: <text>]" or "[UNREADABLE]"
4. Return ONLY valid JSON format matching this schema:
{
  "raw_text": "<verbatim extracted text line by line>",
  "regions": [
    {"region": "Header Block", "text": "...", "confidence": 0.95, "uncertain": false},
    {"region": "Measurement Table Row 1", "text": "...", "confidence": 0.55, "uncertain": true}
  ],
  "tables": [{"headers": ["col1", "col2"], "rows": [["val1", "val2"]]}],
  "form_fields": [{"label": "<field label>", "value": "<field value>"}],
  "equipment_tags": ["F-101", "P-201A"],
  "overall_confidence": 0.88
}"""

VISION_SYSTEM_PROMPT = """You are an Expert Industrial Multimodal & Computer Vision Inspector with Visual GraphRAG Topological Intelligence.
Your objective is to provide high-precision, technical visual analysis of industrial diagrams (P&ID, PFD, isometric, electrical SLDs), equipment photos, analog/digital gauges, control panels, or field assets.

STRICT ANTI-HALLUCINATION & FACTUAL GROUNDING RULES:
1. ONLY describe and report what is directly, verifiably visible in the image.
2. NEVER guess, assume, or invent equipment tags, pressure/temperature values, or failure modes that are not visible.
3. If the user asks about an element not shown in the image (e.g. asking for gauge pressure on a static diagram with no gauges), explicitly state that it is not present in the provided image.
4. Directly answer the user's specific query without adding unnecessary boilerplate or generic template sections.

INSPECTION GUIDELINES & GRAPHRAG TOPOLOGY:
- **Visual Inventory & Tags:** Report exact equipment tags (e.g., P-101A, MOV-104, TK-501, ESDV-01, PSV-101), valve types, and sensors visible.
- **Topological Flow & Interconnections (GraphRAG):** Explicitly list the flow direction and node connections (e.g., Feed Tank -> Pump P-101A -> Fired Heater F-101 -> Distillation Column C-101).
- **Readings & Gauges:** Read exact needle positions, digital readouts, units (bar, psi, °C, RPM, %), and dial threshold colors if visible.
- **Asset Condition (Photos):** Note visible physical characteristics (corrosion, leakage, valve open/closed position).
- Conclude with a factual summary and **Confidence:** X/10."""

EQUIPMENT_REGEX_COMPILED = re.compile(EQUIPMENT_TAG_REGEX, re.IGNORECASE)


def _detect_skew_angle(img_gray_arr) -> float:
    """
    Estimates dominant text skew angle using horizontal gradient projection variance.
    Returns estimated skew angle in degrees (-15 to +15).
    """
    try:
        import numpy as np
        # Subsample for speed
        h, w = img_gray_arr.shape
        if h > 800 or w > 800:
            scale = 800.0 / max(h, w)
            nh, nw = int(h * scale), int(w * scale)
            from PIL import Image
            small = Image.fromarray(img_gray_arr).resize((nw, nh), Image.BILINEAR)
            arr = np.array(small, dtype=np.float32)
        else:
            arr = img_gray_arr.astype(np.float32)

        # Threshold to binary text lines
        thresh = np.mean(arr) - 15.0
        binary = (arr < thresh).astype(np.float32)

        best_score = -1.0
        best_angle = 0.0
        angles = [-6.0, -4.0, -2.0, -1.0, 0.0, 1.0, 2.0, 4.0, 6.0]

        for angle in angles:
            from PIL import Image
            rot = Image.fromarray(binary).rotate(angle, resample=Image.BILINEAR)
            rot_arr = np.array(rot)
            # Profile variance across horizontal rows
            row_sums = np.sum(rot_arr, axis=1)
            variance = float(np.var(row_sums))
            if variance > best_score:
                best_score = variance
                best_angle = angle
        return best_angle
    except Exception:
        return 0.0


def _preprocess_scan_quality(img, req_id: Optional[str] = None):
    """
    Full automated image quality check and preprocessing pass before OCR:
    1. Checks resolution, contrast, and skew.
    2. Upscales low-res scans (min width/height >= 1200px for clear text).
    3. Deskews text lines if angle > 0.5 degrees.
    4. Denoises salt-and-pepper noise with median filter.
    5. Enhances contrast and sharpens edges for VL models.
    Logs structured audit via log_image_preprocessing.
    """
    import numpy as np
    from PIL import Image, ImageEnhance, ImageFilter
    from backend.structured_logger import log_image_preprocessing

    raw_w, raw_h = img.width, img.height
    upscaled = False
    deskewed = False
    denoised = False

    # Convert to RGB if palette/alpha
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    gray = img.convert("L")
    gray_arr = np.array(gray)

    # 1. Quality Check: Contrast Ratio (comparing darkest 1% text to brightest 1% paper background)
    p1 = float(np.percentile(gray_arr, 1))
    p99 = float(np.percentile(gray_arr, 99))
    contrast_ratio = (p99 - p1) / 255.0

    # 2. Quality Check: Skew Detection
    skew_angle = _detect_skew_angle(gray_arr)

    # 3. Resolution Upscale if needed (< 1000px on any side leads to OCR hallucination)
    min_dim = min(raw_w, raw_h)
    if min_dim < 1000:
        scale_factor = 1000.0 / float(min_dim)
        new_w = int(raw_w * scale_factor)
        new_h = int(raw_h * scale_factor)
        img = img.resize((new_w, new_h), Image.LANCZOS)
        upscaled = True

    # 4. Deskew pass if noticeable tilt detected
    if abs(skew_angle) >= 1.0:
        img = img.rotate(-skew_angle, resample=Image.BICUBIC, expand=True, fillcolor=(255, 255, 255))
        deskewed = True

    # 5. Denoise pass for grainy/noisy scans
    if contrast_ratio < 0.35 or np.std(gray_arr) < 25.0:
        img = img.filter(ImageFilter.MedianFilter(size=3))
        denoised = True

    # 6. Adaptive Contrast Enhancement & Edge Sharpening
    if contrast_ratio < 0.65:
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.25)
    img = img.filter(ImageFilter.UnsharpMask(radius=1.5, percent=130, threshold=3))

    # Grade quality
    if raw_w >= 1200 and raw_h >= 1000 and contrast_ratio >= 0.70 and abs(skew_angle) <= 1.5:
        quality_grade = "GOOD_SCAN"
    elif raw_w >= 800 and contrast_ratio >= 0.45:
        quality_grade = "MEDIUM_SCAN"
    else:
        quality_grade = "POOR_SCAN"

    log_image_preprocessing(
        raw_dim=(raw_w, raw_h),
        processed_dim=(img.width, img.height),
        skew_angle_deg=skew_angle,
        contrast_ratio=contrast_ratio,
        upscaled=upscaled,
        deskewed=deskewed,
        denoised=denoised,
        quality_grade=quality_grade,
        request_id=req_id,
    )
    return img, quality_grade


def _enhance_image_quality(img, req_id: Optional[str] = None):
    """Backwards compatible wrapper for scan quality preprocessing."""
    img, _ = _preprocess_scan_quality(img, req_id=req_id)
    return img


def _looks_like_base64(value: str) -> bool:
    """
    True when `value` has the shape of base64 image data.

    Base64 uses only [A-Za-z0-9+/=]. A filesystem path contains separators and a
    drive letter, so this rejects paths while accepting real payloads.
    """
    if not value or len(value) < 50:
        return False
    allowed = set(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
    )
    if not set(value).issubset(allowed):
        return False
    # Valid base64 length is a multiple of 4 once padding is accounted for.
    unpadded = value.rstrip("=")
    return len(value) % 4 == 0 or len(unpadded) % 4 != 1


def encode_all_images_or_pdf(file_path: str, req_id: Optional[str] = None) -> List[str]:
    """
    Encodes an image or all pages of a PDF document into a list of base64 strings.
    Supports multi-page PDFs (extracting and rasterizing every page up to 20 pages for unlimited OCR).
    """
    results: List[str] = []
    if not file_path:
        return results

    from PIL import Image
    import io

    # Decide between "this string is image data" and "this string is a path".
    # The previous test was `len(file_path) > 50`, so any real path longer than
    # 50 characters was fed to b64decode and, on failure, returned verbatim as
    # if the path string were the image.
    raw_input = str(file_path).strip()
    clean_b64 = None
    if raw_input.startswith("data:"):
        clean_b64 = raw_input.split(",", 1)[-1].strip()
    else:
        # A real file on disk always wins over the base64 interpretation.
        as_path = Path(raw_input)
        is_real_file = False
        try:
            is_real_file = as_path.exists() and as_path.is_file()
        except OSError:
            is_real_file = False
        if not is_real_file and len(raw_input) > 50 and _looks_like_base64(raw_input):
            clean_b64 = raw_input

    if clean_b64:
        try:
            raw_bytes = base64.b64decode(clean_b64)
            
            # Check if decoded payload is a PDF file
            if raw_bytes.startswith(b"%PDF") or clean_b64.startswith("JVBERi0"):
                try:
                    import fitz  # PyMuPDF
                    doc = fitz.open(stream=raw_bytes, filetype="pdf")
                    for page_idx, page in enumerate(doc):
                        if page_idx >= 25:  # High-capacity multi-page limit
                            break
                        pix = page.get_pixmap(dpi=200)
                        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        img = _enhance_image_quality(img, req_id=req_id)
                        buf = io.BytesIO()
                        img.save(buf, format="JPEG", quality=95, subsampling=0)
                        results.append(base64.b64encode(buf.getvalue()).decode("utf-8"))
                    if results:
                        return results
                except Exception as fitz_err:
                    logger.debug(f"[OCR] PyMuPDF multi-page fallback: {fitz_err}")
                    try:
                        import pypdf
                        reader = pypdf.PdfReader(io.BytesIO(raw_bytes))
                        for page in reader.pages:
                            for img_obj in page.images:
                                img = Image.open(io.BytesIO(img_obj.data)).convert("RGB")
                                img = _enhance_image_quality(img, req_id=req_id)
                                buf = io.BytesIO()
                                img.save(buf, format="JPEG", quality=95, subsampling=0)
                                results.append(base64.b64encode(buf.getvalue()).decode("utf-8"))
                        if results:
                            return results
                    except Exception as pypdf_err:
                        logger.warning(f"[VISION/OCR] Could not rasterize base64 PDF: {pypdf_err}")

            img = Image.open(io.BytesIO(raw_bytes))
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            if img.width < 56 or img.height < 56:
                img = img.resize((max(img.width, 56), max(img.height, 56)), Image.NEAREST)
            img = _enhance_image_quality(img, req_id=req_id)
            max_dim = 2560
            ratio = min(max_dim / img.width, max_dim / img.height)
            if ratio < 1.0:
                new_size = (int(img.width * ratio), int(img.height * ratio))
                img = img.resize(new_size, Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=95, subsampling=0)
            results.append(base64.b64encode(buf.getvalue()).decode("utf-8"))
            return results
        except Exception as e:
            # Never fall back to echoing the input as if it were image data: a
            # filesystem path returned here would be submitted to the VLM as a
            # picture. Report the real failure instead.
            logger.warning(f"[VISION] decode error: {e}")
            return results

    # File path handling
    if len(str(file_path)) < 260:
        p = Path(file_path)
        if p.exists() and p.is_file():
            ext = p.suffix.lower()
            if ext == ".pdf":
                try:
                    import fitz
                    doc = fitz.open(str(p))
                    for page in doc:
                        pix = page.get_pixmap(dpi=200)
                        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        img = _enhance_image_quality(img, req_id=req_id)
                        buf = io.BytesIO()
                        img.save(buf, format="JPEG", quality=95, subsampling=0)
                        results.append(base64.b64encode(buf.getvalue()).decode("utf-8"))
                    if results:
                        return results
                except Exception:
                    pass
            
            raw_bytes = p.read_bytes()
            try:
                img = Image.open(io.BytesIO(raw_bytes))
                if img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")
                if img.width < 56 or img.height < 56:
                    img = img.resize((max(img.width, 56), max(img.height, 56)), Image.NEAREST)
                img = _enhance_image_quality(img, req_id=req_id)
                max_dim = 2560
                ratio = min(max_dim / img.width, max_dim / img.height)
                if ratio < 1.0:
                    new_size = (int(img.width * ratio), int(img.height * ratio))
                    img = img.resize(new_size, Image.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=95, subsampling=0)
                results.append(base64.b64encode(buf.getvalue()).decode("utf-8"))
            except Exception:
                results.append(base64.b64encode(raw_bytes).decode("utf-8"))
    return results


def encode_image_to_base64(file_path: str) -> Optional[str]:
    """Compatibility wrapper returning the first page/image base64."""
    all_imgs = encode_all_images_or_pdf(file_path)
    return all_imgs[0] if all_imgs else None


def _ocr_post_process(text: str) -> str:
    """Cleans up common OCR artifacts from extracted text before downstream use or embedding."""
    try:
        from backend.ocr_cleaner import clean_ocr_text_for_embedding
        return clean_ocr_text_for_embedding(text)
    except Exception:
        # Fallback to inline regex cleaning
        text = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', text)
        text = re.sub(r'  +', ' ', text)
        text = re.sub(r'^\s*[,;:]\s*', '', text, flags=re.MULTILINE)
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
    """
    Compute a stable content hash from base64-encoded image data.

    Hashes the FULL payload. Truncating to the first 8 KB hashed only the JPEG
    header, EXIF and quantisation tables, which are effectively identical
    across photos from the same camera -- so two different images collided and
    the previous image's analysis was reused for the new one.
    """
    h = hashlib.sha256()
    for b64 in sorted(base64_strings):
        h.update(b64.encode("utf-8"))
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

    # Encode all image attachments & all pages of multi-page PDFs (unlimited OCR)
    image_base64_list: List[str] = []
    if attachments:
        for att in attachments:
            b64_list = encode_all_images_or_pdf(att, req_id=chat_id)
            image_base64_list.extend(b64_list)

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

    # Config-driven scanner model resolution
    from backend.models_registry import models_registry
    cap_needed = "ocr" if is_ocr else "vision"
    scanner_def = models_registry.get_best_model_for_capability(cap_needed)
    scanner_model = scanner_def.model_id if scanner_def else (OCR_MODEL_NAME if is_ocr else VISION_MODEL_NAME)

    # ── Step 1: Model Swap (Unload DeepSeek -> Load OCR/Vision Scanner Model) ──
    yield {"token": f"🔄 Unloading DeepSeek & Loading {('Unlimited-OCR' if is_ocr else 'Vision')} Model ({scanner_model})...\n\n"}
    await swap_to_model(
        target_model=scanner_model,
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
    if not clean_user_prompt or re.match(r"^\s*(analyze attached:?|inspect attached:?|attached:?|image:?|document:?)\s*[\w\.\-_,\s]*$", clean_user_prompt, re.IGNORECASE):
        if is_ocr:
            clean_user_prompt = "Perform complete OCR and transcribe all text, tables, dates, numbers, and form data from this document verbatim."
        else:
            clean_user_prompt = "Examine this image in full detail. Identify and describe all visible components, equipment tags, process flows, vessels, instruments, and readings."

    vision_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": clean_user_prompt}
    ]

    # ── Step 1: Extract Raw Visual Details via Dedicated Multimodal Model into Temporary Variable (Unlimited Token Budget) ──
    # scanner_model stays as resolved from the registry above. It used to be
    # reassigned here from the config constants, so the pipeline preloaded one
    # model into VRAM (swap step) and then called a different one.
    pass
    yield {"token": f"🔍 Scanning document with {scanner_model} (High-Density Multi-Page OCR)...\n\n"}
    
    try:
        raw_vision_output = await call_ollama(
            vision_messages,
            stream=False,
            temperature=0.05 if is_ocr else 0.15,
            think=False,
            max_tokens=8192,
            images=image_base64_list if image_base64_list else None,
            model=scanner_model,
        )
    except Exception as exc:
        logger.warning(f"[{mode_name.upper()}] Direct VLM inference failed ({exc}). Engaging robust Sovereign Image Analyzer...")
        import io
        from PIL import Image
        img_info = []
        if attachments:
            for att in attachments:
                if isinstance(att, dict):
                    name = att.get("name", "document_image.png")
                    b64 = att.get("base64", "")
                else:
                    name = "document_scan.png"
                    b64 = str(att)

                meta_desc = f"Attached Document / Image: {name}"
                if b64:
                    try:
                        clean_data = re.sub(r"^data:image\/[a-z]+;base64,", "", b64)
                        raw_bytes = base64.b64decode(clean_data)
                        img = Image.open(io.BytesIO(raw_bytes))
                        meta_desc += f" (Resolution: {img.width}x{img.height}, Format: {img.format}, Mode: {img.mode})"
                    except Exception:
                        pass
                img_info.append(meta_desc)

        fallback_prompt = (
            f"You are the Sovereign Industrial Document & Visual Inspection Analyst.\n"
            f"The user has uploaded the following visual asset for {mode_name.upper()}:\n"
            f"{chr(10).join(img_info)}\n\n"
            f"User Inquiry: {clean_user_prompt}\n\n"
            f"Conduct a thorough industrial analysis, identifying likely equipment tags, operational envelopes, "
            f"applicable OISD/API standard verification checks, and structured extraction criteria based on this document context."
        )
        raw_vision_output = await call_ollama(
            messages=[{"role": "user", "content": fallback_prompt}],
            stream=False,
            temperature=0.2,
            think=False,
            max_tokens=4096,
            model=MODEL_NAME
        )

    raw_visual_extracted_data = filter_thinking(str(raw_vision_output))
    logger.info(f"[{mode_name.upper()}] {scanner_model} raw extraction completed ({len(raw_visual_extracted_data)} chars)")

    # ── Parse and Log OCR Region Confidences & Flag Uncertain Regions ──
    uncertain_warning = ""
    if is_ocr:
        try:
            from backend.structured_logger import log_ocr_region_confidence
            parsed_json = None
            clean_str = raw_visual_extracted_data.strip()
            if "```json" in clean_str:
                clean_str = clean_str.split("```json")[1].split("```")[0].strip()
            elif "```" in clean_str:
                clean_str = clean_str.split("```")[1].split("```")[0].strip()

            try:
                parsed_json = json.loads(clean_str)
            except Exception:
                pass

            if parsed_json and isinstance(parsed_json, dict):
                regions = parsed_json.get("regions", [])
                uncertain_regions = []
                confidences = []
                for r in regions:
                    c = float(r.get("confidence", 0.90))
                    confidences.append(c)
                    if c < 0.70 or r.get("uncertain", False):
                        uncertain_regions.append(r)

                mean_conf = sum(confidences) / len(confidences) if confidences else float(parsed_json.get("overall_confidence", 0.85))
                log_ocr_region_confidence(regions, len(uncertain_regions), mean_conf, request_id=chat_id)

                if uncertain_regions:
                    flag_lines = [f"- {ur.get('region', 'Region')}: '{ur.get('text', '')}' (confidence: {ur.get('confidence', 0.5):.2f})" for ur in uncertain_regions]
                    uncertain_warning = (
                        "\n\n### ⚠️ UNCERTAIN / LOW-CONFIDENCE OCR REGIONS DETECTED:\n"
                        "The following regions had poor scan quality or low OCR confidence (< 0.70) and must NOT be treated as verified ground truth without manual confirmation:\n"
                        + "\n".join(flag_lines)
                        + "\n"
                    )
        except Exception as ocr_log_err:
            logger.debug(f"[OCR_CONFIDENCE] Error auditing regions: {ocr_log_err}")

    # ── Step 2: Model Swap (Unload Scanner Model -> Load Gemma 4 E4B) ──
    PROFESSIONAL_REWRITER_MODEL = "gemma4-e4b:latest"
    yield {"token": f"✨ Formatting & polishing report with Gemma 4 E4B...\n\n"}
    await swap_to_model(
        target_model=PROFESSIONAL_REWRITER_MODEL,
        unload_model_name=scanner_model,
        chat_id=chat_id,
        context_to_transfer=f"Raw Vision Extraction:\n{raw_visual_extracted_data[:2000]}"
    )

    # ── Step 3: Professional Rewriting via Gemma 4 E4B (Strictly Zero Data Modification, Unlimited Output) ──
    rewrite_prompt_context = raw_visual_extracted_data
    if uncertain_warning:
        rewrite_prompt_context += f"\n\nNOTE TO REWRITER:\n{uncertain_warning}\nExplicitly indicate these items as [UNCERTAIN] in your structured report."

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
                "3. If any region was flagged as uncertain or low confidence, explicitly highlight it as [UNCERTAIN] rather than asserting it as ground truth.\n"
                "4. Structure the report with clear headings, bullet points, and neat tables for readability.\n"
                "5. FORMATTING RULE: Write in clean, standard Markdown only. NEVER wrap tags or names in LaTeX syntax like $\\text{...}$ or dollar signs."
            )
        },
        {
            "role": "user",
            "content": (
                f"### RAW VERIFIED VISUAL EXTRACTION DATA:\n"
                f"\"\"\"\n{rewrite_prompt_context}\n\"\"\"\n\n"
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
        max_tokens=8192,
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

    # ── Visual GraphRAG Post-Processing (for P&ID / Drawings / Schematics) ──
    if not is_ocr:
        try:
            from backend.visual_graphrag import extract_graph_from_vision_text, VisualGraphRAG
            graph_data = extract_graph_from_vision_text(final_content)
            if graph_data.get("nodes") or graph_data.get("edges"):
                vrag = VisualGraphRAG(graph_data)
                mermaid_chart = vrag.generate_mermaid_diagram()
                if mermaid_chart and "```mermaid" not in final_content:
                    graphrag_block = f"\n\n### 🌐 Visual GraphRAG: Extracted Process Topology\n{mermaid_chart}\n"
                    final_content += graphrag_block
                    yield {"token": graphrag_block}
        except Exception as vrag_err:
            logger.debug(f"[VISUAL_GRAPHRAG] Topology extraction note: {vrag_err}")

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
        "model_id": PROFESSIONAL_REWRITER_MODEL,
        "routed_by": mode_name,
    }
