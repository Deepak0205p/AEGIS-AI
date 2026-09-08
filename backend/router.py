"""
Heuristic Router & Execution Policy for Air-Gapped Local AI Backend.
Performs fast, deterministic keyword/regex matching, adaptive thinking decision,
and RAG retrieval gating with ZERO extra LLM calls.
"""

import re
from typing import Tuple, Optional, List, Dict
from backend.config import (
    logger,
    EQUIPMENT_TAG_REGEX,
    RAG_DOMAIN_KEYWORDS,
    THINK_ON_COMPLEX_CHAT,
)

# Multi-signal Intent Keywords, Weights & Exclusion Guards for High-Accuracy Routing
INTENT_DEFINITIONS = [
    {
        "mode": "code",
        "actions": [
            "execute", "run", "calculate", "plot", "debug", "compile", "iterate", "loop", "solve",
            "benchmark", "chalao", "solve karo", "simulate", "scrape", "parse", "automate", "compute", "implement"
        ],
        "nouns": [
            "code", "python", "script", "function", "bug", "error", "sql", "regex", "program", "debug",
            "algorithm", "dataframe", "array", "syntax", "variable", "recursion", "class", "module", "api endpoint"
        ],
        "patterns": [
            re.compile(r"```\w*", re.I),
            re.compile(r"\bdef\s+\w+\s*\(", re.I),
            re.compile(r"\bimport\s+\w+\b", re.I),
            re.compile(r"\b(print|return|traceback|syntaxerror|nameerror|zerodivisionerror)\b", re.I),
            re.compile(r"\b(for\s+\w+\s+in\s+|while\s+|if\s+__name__)\b", re.I),
            re.compile(r"\b(matplotlib|numpy|pandas|scipy|sympy)\b", re.I),
        ],
        "negative_patterns": [
            re.compile(r"\b(in word|in docx|in excel|in spreadsheet|in presentation|in ppt)\b", re.I)
        ],
        "weight": 1.0,
    },
    {
        "mode": "excel",
        "actions": [
            "sum", "average", "vlookup", "xlookup", "aggregate", "tabulate", "pivot", "tally",
            "formula", "table banao", "hisab", "ledger"
        ],
        "nouns": [
            "excel", "xlsx", "xls", "sheet", "spreadsheet", "csv", "pivot table", "table data",
            "tabular", "worksheet", "cells", "rows and columns", "column chart", "data sheet"
        ],
        "patterns": [
            re.compile(r"\b(rows?|columns?)\b.*\b(data|table|sheet|values?)\b", re.I),
            re.compile(r"\b(vlookup|xlookup|hlookup|index match|sumif|countif)\b", re.I),
            re.compile(r"\b(tabular format|spreadsheet format|tabular data)\b", re.I),
        ],
        "negative_patterns": [],
        "weight": 1.0,
    },
    {
        "mode": "ppt",
        "actions": [
            "present", "pitch", "deck", "keynote", "slides banao", "presentation banao"
        ],
        "nouns": [
            "ppt", "pptx", "presentation", "slides", "deck", "slide deck", "powerpoint",
            "agenda slide", "slide show", "title slide", "pitch deck"
        ],
        "patterns": [
            re.compile(r"\b\d+\s*slides?\b", re.I),
            re.compile(r"\b(slide\s*\d+|title\s*slide|conclusion\s*slide)\b", re.I),
            re.compile(r"\b(presentation on|slides for|deck for)\b", re.I),
        ],
        "negative_patterns": [],
        "weight": 1.0,
    },
    {
        "mode": "docs",
        "actions": [
            "draft", "compose", "formalize", "memo", "sop", "document likho", "circular nikalo"
        ],
        "nouns": [
            "word", "doc", "docx", "report", "note", "letter", "approval", "draft", "memo",
            "minutes of meeting", "mom", "circular", "handbook", "whitepaper", "formal notice",
            "contract", "agreement", "nda", "proposal"
        ],
        "patterns": [
            re.compile(r"\b(official\s+memo|formal\s+report|minutes\s+of\s+meeting|official\s+notice)\b", re.I),
            re.compile(r"\b(word document|docx document|printable report)\b", re.I),
        ],
        "negative_patterns": [
            re.compile(r"\b(email|mail)\b", re.I)
        ],
        "weight": 1.0,
    },
    {
        "mode": "ocr",
        "actions": [
            "extract text", "read text", "transcribe", "ocr", "scan", "extract table", "read table",
            "digitize", "parse receipt", "read invoice", "extract data from image"
        ],
        "nouns": [
            "ocr", "text extraction", "scanned document", "receipt", "invoice", "scanned pdf",
            "nameplate", "gauge reading", "table extraction", "handwritten text", "form text"
        ],
        "patterns": [
            re.compile(r"\b(ocr\s+this|extract\s+text|transcribe\s+(this|the|image)|read\s+the\s+text)\b", re.I),
            re.compile(r"\b(scanned\s+(pdf|image|doc|receipt|invoice)|text\s+from\s+(image|photo|drawing))\b", re.I),
        ],
        "negative_patterns": [],
        "weight": 1.2,
    },
    {
        "mode": "vision",
        "actions": [
            "inspect", "analyze diagram", "check drawing", "visualize", "explain drawing", "interpret schematic",
            "detect corrosion", "check gauge", "find defect", "see image", "describe picture"
        ],
        "nouns": [
            "p&id", "pid", "cad drawing", "blueprint", "schematic", "engineering drawing",
            "visual inspection", "flow diagram", "plant photo", "corrosion", "mechanical drawing"
        ],
        "patterns": [
            re.compile(r"\b(p&id|pid|cad\s+blueprint|engineering\s+drawing|schematic\s+diagram)\b", re.I),
            re.compile(r"\b(inspect\s+the\s+(image|diagram|drawing|equipment)|what\s+is\s+in\s+this\s+image)\b", re.I),
        ],
        "negative_patterns": [],
        "weight": 1.2,
    },
]

# File extension mappings to direct execution modes
ATTACHMENT_EXTENSION_MAP = {
    ".py": "code",
    ".ipynb": "code",
    ".sql": "code",
    ".sh": "code",
    ".csv": "excel",
    ".xlsx": "excel",
    ".xls": "excel",
    ".docx": "docs",
    ".doc": "docs",
    ".pptx": "ppt",
    ".ppt": "ppt",
    ".png": "ocr",
    ".jpg": "ocr",
    ".jpeg": "ocr",
    ".bmp": "ocr",
    ".tiff": "ocr",
    ".tif": "ocr",
    ".webp": "ocr",
    ".pdf": "docs",
}

# Regex patterns for backward compatibility fast check
ROUTING_PATTERNS = [
    ("code", re.compile(r"\b(code|python|script|function|bug|error|sql|regex|program|debug|algorithm)\b", re.IGNORECASE)),
    ("docs", re.compile(r"\b(word|doc|docx|report|note|letter|approval|draft|memo)\b", re.IGNORECASE)),
    ("excel", re.compile(r"\b(excel|xlsx|sheet|spreadsheet|csv|pivot|table data)\b", re.IGNORECASE)),
    ("ppt", re.compile(r"\b(ppt|presentation|slides|deck)\b", re.IGNORECASE)),
]

# Patterns for complex analytical thinking in chat
COMPLEX_THINKING_KEYWORDS = re.compile(
    r"\b(why|how|explain|compare|calculate|derive|kyun|kaise|farak|difference)\b",
    re.IGNORECASE
)

MULTI_ASK_PATTERNS = re.compile(
    r"\b(and also|aur bhi|as well as|aur sath me)\b",
    re.IGNORECASE
)

PREV_RESULT_PATTERNS = re.compile(
    r"\b(why did it fail|ye error kyun|reason for failure|why error|fail kyun|error explain)\b",
    re.IGNORECASE
)

# Creation verbs — these should NOT trigger thinking (the model is generating, not analyzing)
CREATION_VERBS = re.compile(
    r"\b(write|draft|likho|likh|banao|bana|prepare|compose|generate|email|mail|send)\b",
    re.IGNORECASE
)

# Follow-up patterns for RAG cache reuse
FOLLOW_UP_PATTERNS = re.compile(
    r"^(aur batao|wahi|uska detail|explain more|details|bataiye|more info|detail me|aur kya|and then|continue|go on)[\s\!\.\?]*$",
    re.IGNORECASE
)

EQUIPMENT_REGEX_COMPILED = re.compile(EQUIPMENT_TAG_REGEX, re.IGNORECASE)


def route_message(
    user_message: str,
    mode_override: Optional[str] = "auto",
    attachments: Optional[List[str]] = None,
    last_route: Optional[str] = None,
    allow_multi: bool = False
) -> Tuple[str, Optional[str]]:
    """
    Determines execution route for incoming message using:
    1. Manual override check.
    2. File attachment inspection (Phase 1).
    3. Technical Equipment tag & Safety SOP context override.
    4. Multi-signal Intent & Keyword Scoring.
    Returns (route_name, trigger_keyword).
    """
    clean_override = (mode_override or "").strip().lower()

    # 1. Handle explicit mode overrides
    if clean_override and clean_override not in ("auto", "", "orchestrator"):
        valid_modes = {"chat", "code", "docs", "excel", "ppt", "vision", "ocr"}
        if clean_override in valid_modes:
            logger.info(f"[ROUTER] Route decision: '{clean_override}' via manual mode override")
            return clean_override, "manual_override"

    message_text = user_message.strip()

    # 2. Phase 1: Attachment-aware routing
    if attachments:
        for att in attachments:
            clean_att = str(att).lower().strip()
            # If attachment is direct base64 image data or data URI
            if clean_att.startswith("data:image") or len(clean_att) > 100:
                logger.info("[ROUTER] Route decision: 'vision' via base64 image payload in attachments")
                return "vision", "attachment_base64_image"
            # Extract extension
            for ext, mapped_mode in ATTACHMENT_EXTENSION_MAP.items():
                if clean_att.endswith(ext):
                    logger.info(f"[ROUTER] Route decision: '{mapped_mode}' via attachment extension '{ext}' in '{att}'")
                    return mapped_mode, f"attachment_{ext}"

    # Check for image filename / attached indicators in user message text
    image_ext_in_text = re.search(r"\b\w+\.(png|jpg|jpeg|webp|bmp|tiff|tif)\b", message_text, re.IGNORECASE)
    if image_ext_in_text:
        logger.info(f"[ROUTER] Route decision: 'vision' via image filename '{image_ext_in_text.group(0)}' in user message")
        return "vision", f"text_attachment_{image_ext_in_text.group(1).lower()}"

    # 3. Conversation-aware follow-up re-routing
    if last_route:
        # If last route was vision or ocr and query is asking about the image/content, keep in vision mode to use cache
        if last_route in ("vision", "ocr"):
            if not any(re.search(rf"\b{k}\b", message_text, re.IGNORECASE) for k in ["python", "script", "excel", "sheet", "ppt", "slide", "word", "docx"]):
                logger.info(f"[ROUTER] Route decision: 'vision' via conversation follow-up from last_route='{last_route}'")
                return "vision", "follow_up_vision_cache"

        # Check follow-up conversion/export patterns
        if re.search(r"\b(export|convert|save|put|tabulate|format)\b.*\b(excel|spreadsheet|sheet|csv|table|xlsx)\b", message_text, re.IGNORECASE) or \
           re.search(r"^(now\s+)?(export\s+to\s+excel|put\s+in\s+spreadsheet|make\s+an?\s+excel\s+sheet|save\s+as\s+csv)", message_text, re.IGNORECASE):
            logger.info(f"[ROUTER] Route decision: 'excel' via conversation follow-up from last_route='{last_route}'")
            return "excel", "follow_up_excel"
        if re.search(r"\b(convert|make|create|generate|turn into)\b.*\b(slides?|ppt|pptx|presentation|pitch deck|deck)\b", message_text, re.IGNORECASE) or \
           re.search(r"^(now\s+)?(make\s+a\s+ppt|convert\s+to\s+slides|create\s+presentation)", message_text, re.IGNORECASE):
            logger.info(f"[ROUTER] Route decision: 'ppt' via conversation follow-up from last_route='{last_route}'")
            return "ppt", "follow_up_ppt"
        if re.search(r"\b(save|export|formalize|draft|format)\b.*\b(word|doc|docx|report|memo|official doc)\b", message_text, re.IGNORECASE) or \
           re.search(r"^(now\s+)?(save\s+as\s+docx|draft\s+official\s+memo|put\s+into\s+report)", message_text, re.IGNORECASE):
            logger.info(f"[ROUTER] Route decision: 'docs' via conversation follow-up from last_route='{last_route}'")
            return "docs", "follow_up_docs"
        if re.search(r"\b(automate|simulate|write code|code this|calculate in python|script this)\b", message_text, re.IGNORECASE):
            logger.info(f"[ROUTER] Route decision: 'code' via conversation follow-up from last_route='{last_route}'")
            return "code", "follow_up_code"

    # 4. Check if message has equipment tag + technical context -> force chat (RAG)
    has_tag = bool(EQUIPMENT_REGEX_COMPILED.search(message_text))
    has_tech_context = bool(re.search(
        r"\b(inspection|utm|thickness|corrosion|vibration|temperature|pressure|calibration|"
        r"reading|measurement|incident|spill|leak|failure|breakdown|sop|procedure|"
        r"maintenance|repair|safety|report)\b",
        message_text, re.IGNORECASE
    ))
    if has_tag and has_tech_context:
        # Check if user specifically requested a code/excel/ppt export of equipment data
        has_explicit_export = bool(re.search(
            r"\b(python|script|code|spreadsheet|excel|xlsx|slides|pptx|matplotlib|plot|chart|graph|simulate|dataframe)\b",
            message_text,
            re.IGNORECASE
        ))
        if not has_explicit_export:
            logger.info("[ROUTER] Route decision: 'chat' (equipment tag + technical context override)")
            return "chat", "tag_tech_override"

    # 5. Multi-signal Weighted Intent Scoring
    # Email and mail specifically routed to chat
    is_email = bool(re.search(r"\b(email|mail)\b", message_text, re.IGNORECASE))
    if is_email and not any(k in message_text.lower() for k in ["python", "script", "code", "excel", "sheet"]):
        logger.info("[ROUTER] Route decision: 'chat' triggered by email/mail communication")
        return "chat", "email_stay_in_chat"

    scores: Dict[str, float] = {}
    trigger_terms: Dict[str, str] = {}

    for intent in INTENT_DEFINITIONS:
        m = intent["mode"]
        score = 0.0
        best_trigger = None

        # Check action words (weight 1.5)
        for act in intent["actions"]:
            if re.search(rf"\b{re.escape(act)}\b", message_text, re.IGNORECASE):
                score += 1.5
                if not best_trigger:
                    best_trigger = act

        # Check noun words (weight 2.0)
        for noun in intent["nouns"]:
            if re.search(rf"\b{re.escape(noun)}\b", message_text, re.IGNORECASE):
                score += 2.0
                best_trigger = noun

        # Check regex patterns (weight 2.5)
        for pat in intent["patterns"]:
            if pat.search(message_text):
                score += 2.5
                if not best_trigger:
                    best_trigger = "pattern_match"

        # Apply negative exclusions/penalties
        for neg_pat in intent.get("negative_patterns", []):
            if neg_pat.search(message_text):
                score -= 3.0

        if score >= 1.5:
            scores[m] = score
            trigger_terms[m] = best_trigger or m

    # Check for Multi-Intent if allow_multi is requested or multi-intent detected
    if allow_multi and scores:
        high_scores = {m: s for m, s in scores.items() if s >= 3.0}
        if len(high_scores) >= 2:
            ordered = sorted(high_scores, key=high_scores.get, reverse=True)
            combo = "+".join(ordered)
            logger.info(f"[ROUTER] Multi-intent detected: {ordered} ({combo})")
            return "multi", combo

    if scores:
        # Pick highest scoring mode
        best_mode = max(scores, key=scores.get)
        trigger_kw = trigger_terms[best_mode]
        logger.info(f"[ROUTER] Route decision: '{best_mode}' (score={scores[best_mode]}) triggered by: '{trigger_kw}'")
        return best_mode, trigger_kw

    # 6. Default fallback
    logger.info("[ROUTER] Route decision: 'chat' (no specific keyword match)")
    return "chat", "default_chat"


async def classify_intent_model(
    user_message: str,
    attachments: Optional[List[str]] = None,
    last_route: Optional[str] = None
) -> Tuple[str, str, float]:
    """
    Intelligent LLM Intent Classifier for Auto Mode.
    Uses the local sovereign model (deepseek-v4-pro:4b) with json_mode=True and think=False.
    Accurately classifies across English, Hindi, Hinglish, and technical jargon into one of:
    - 'code': Programming, scripts, Python/SQL, mathematical/numerical derivations, simulations, plotting charts
    - 'excel': Spreadsheets, tabular datasets, formulas (SUM, AVERAGE, VLOOKUP), ledgers, tables, rows/columns
    - 'ppt': Presentation slides, pitch decks, slide overviews, .pptx deliverables
    - 'docs': Formal Word reports, memos, official notices, letters, incident SOPs, meeting minutes, .docx deliverables
    - 'ocr': Extracting or reading raw text/numbers/tables from images or scanned documents/receipts
    - 'vision': Visual inspection, engineering diagrams, P&ID schematics, physical plant defect detection from images
    - 'chat': General conversation, answering technical plant questions, explaining concepts, troubleshooting, SOP consultation
    Returns (mode, reason, confidence).
    """
    import json
    from backend.ollama_client import call_ollama, filter_thinking

    # Build context notes
    context_notes = []
    if last_route and last_route not in ("auto", "orchestrator"):
        context_notes.append(f"Previous interaction mode was '{last_route}'. If this is a follow-up or modification, keep continuity.")

    if attachments:
        att_kinds = []
        for a in attachments:
            a_str = str(a).lower().strip()
            if a_str.startswith("data:image") or len(a_str) > 100 or any(a_str.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"]):
                att_kinds.append("image")
            elif any(a_str.endswith(ext) for ext in [".xlsx", ".xls", ".csv"]):
                att_kinds.append("spreadsheet")
            elif any(a_str.endswith(ext) for ext in [".docx", ".doc", ".pdf"]):
                att_kinds.append("document")
            elif any(a_str.endswith(ext) for ext in [".py", ".sql", ".sh"]):
                att_kinds.append("code file")
            else:
                att_kinds.append("file")
        context_notes.append(f"User provided {len(attachments)} attachment(s): {', '.join(att_kinds)}.")

    context_str = f" Context: {' '.join(context_notes)}" if context_notes else ""

    system_prompt = (
        "You are the sovereign AI task intent classifier and orchestrator for an industrial engineering workstation.\n"
        "Analyze the user's input (in English, Hindi, Hinglish, or technical jargon) and identify their execution intent.\n"
        "Available modes:\n"
        "- 'code': Writing, running, debugging Python/SQL code, mathematical calculations, scientific simulations, or plotting charts with matplotlib/numpy/pandas.\n"
        "- 'excel': Creating, formatting, or updating spreadsheets, tabular data, formulas (SUM, AVERAGE, VLOOKUP), ledgers, or .xlsx/.csv files.\n"
        "- 'ppt': Generating presentation slides, slide decks, pitch decks, or .pptx presentations.\n"
        "- 'docs': Generating downloadable Word (.docx) files for formal multi-page enterprise documents, technical reports, engineering SOPs, formal circulars, or investigation reports. DO NOT route emails, leave requests, letters, or short text drafts to 'docs' unless a .docx file is explicitly requested.\n"
        "- 'ocr': Extracting or reading raw text/numbers/tables from scanned documents, receipts, invoices, or images.\n"
        "- 'vision': Visual inspection, analyzing diagrams/P&ID schematics/blueprints, or detecting physical plant defects in photos.\n"
        "- 'chat': General conversation, drafting emails, leave requests, letters, message drafts, answering technical plant questions, explaining concepts, troubleshooting, or SOP consultation.\n\n"
        "Return ONLY a valid JSON object in this format:\n"
        '{"mode": "code"|"excel"|"ppt"|"docs"|"ocr"|"vision"|"chat", "confidence": 0.95, "reason": "<short explanation in 1 sentence>"}'
    )

    user_content = user_message.strip()
    if not user_content and attachments:
        user_content = "Analyze the provided attachment."
    if context_str:
        user_content = f"{user_content}\n[SYSTEM_CONTEXT]{context_str}"

    prompt = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content[:600]},
    ]

    try:
        raw_res = await call_ollama(
            prompt,
            stream=False,
            json_mode=True,
            temperature=0.0,
            max_tokens=80,
            think=False
        )
        cleaned = filter_thinking(str(raw_res)).strip()
        data = json.loads(cleaned)
        mode = str(data.get("mode", "")).strip().lower()
        reason = str(data.get("reason", "Model detected intent")).strip()
        confidence = float(data.get("confidence", 0.95))

        valid_modes = {"code", "excel", "ppt", "docs", "ocr", "vision", "chat"}
        if mode in valid_modes:
            logger.info(f"[MODEL_ORCHESTRATOR] Query '{user_message[:50]}' -> Mode: '{mode}' ({confidence}) Reason: {reason}")
            return mode, reason, confidence

    except Exception as e:
        logger.warning(f"[MODEL_ORCHESTRATOR] Model classification failed: {e}")

    # Fallback to fast regex heuristic if model call fails or returns unparseable JSON
    fb_mode, fb_trigger = route_message(
        user_message,
        mode_override="auto",
        attachments=attachments,
        last_route=last_route
    )
    return fb_mode, f"fallback_heuristic_{fb_trigger}", 0.70


async def classify_intent_fast(user_message: str) -> Optional[str]:
    """Alias to classify_intent_model for backward compatibility."""
    mode, _, _ = await classify_intent_model(user_message)
    return mode


async def route_message_async(
    user_message: str,
    mode_override: Optional[str] = "auto",
    attachments: Optional[List[str]] = None,
    last_route: Optional[str] = None,
    allow_multi: bool = False
) -> Tuple[str, Optional[str]]:
    """
    Intelligent Asynchronous Route Dispatcher for Auto Mode.
    1. Honors explicit manual overrides (code, excel, ppt, docs, vision, ocr, chat).
    2. Fast-paths trivial 1-word greetings (0ms latency).
    3. Fast-paths email/letter/leave requests directly to chat (unless .docx explicitly asked).
    4. Uses the local sovereign LLM (deepseek-v4-pro:4b) as the primary intelligent orchestrator
       to understand intent across Hindi, Hinglish, English, and nuanced tasks WITHOUT keywords.
    5. Falls back gracefully to deterministic heuristics if the model is unreachable.
    """
    clean_override = (mode_override or "").strip().lower()
    clean_msg = user_message.strip().lower()

    # 1. Manual user override explicitly selected from UI buttons
    valid_manual_modes = {"chat", "code", "docs", "excel", "ppt", "vision", "ocr"}
    if clean_override in valid_manual_modes:
        logger.info(f"[ROUTER] Route decision: '{clean_override}' via manual mode override")
        return clean_override, "manual_override"

    # 2. Fast-path attachment routing: Images must be processed by multimodal vision model
    if attachments:
        has_image = any(
            str(a).startswith("data:image")
            or len(str(a)) > 50
            or str(a).startswith("iVBORw0")
            or str(a).startswith("/9j/")
            or str(a).startswith("R0lGOD")
            or str(a).startswith("UklGR")
            or any(str(a).lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"])
            for a in attachments
        )
        if has_image:
            # Check if user specifically requested OCR text extraction
            if re.search(r"\b(ocr|extract text|read text|transcribe|get text|text nikal|extract table)\b", clean_msg, re.IGNORECASE):
                logger.info("[ROUTER] Route decision: 'ocr' via image attachment + OCR extraction request")
                return "ocr", "attachment_image_ocr"
            logger.info("[ROUTER] Route decision: 'vision' via image attachment")
            return "vision", "attachment_image_vision"

        has_spreadsheet = any(any(str(a).lower().endswith(ext) for ext in [".xlsx", ".xls", ".csv"]) for a in attachments)
        if has_spreadsheet:
            logger.info("[ROUTER] Route decision: 'excel' via spreadsheet attachment")
            return "excel", "attachment_spreadsheet"

        has_doc = any(any(str(a).lower().endswith(ext) for ext in [".docx", ".doc", ".pdf"]) for a in attachments)
        if has_doc:
            logger.info("[ROUTER] Route decision: 'docs' via document attachment")
            return "docs", "attachment_doc"

    # 3. Fast greeting shortcut for common 1-2 word pleasantries (0ms latency)
    if not attachments and clean_msg in ("hi", "hello", "hey", "namaste", "halo", "hola", "good morning", "good afternoon", "good evening"):
        return "chat", "greeting_fast_path"

    # 4. Fast-path for emails, leave requests, and messages (must render as readable chat text, NOT Word .docx)
    is_email = bool(re.search(r"\b(email|mail|e-mail|leave application|leave request|resignation)\b", clean_msg, re.IGNORECASE))
    explicit_word_doc = bool(re.search(r"\b(word document|docx|\.docx|word file|downloadable doc)\b", clean_msg, re.IGNORECASE))
    if is_email and not explicit_word_doc and not attachments:
        logger.info("[ROUTER] Route decision: 'chat' for email/correspondence communication draft")
        return "chat", "email_draft_chat"

    # 5. Model-Driven Intent Orchestration (Zero Keywords)
    mode, reason, confidence = await classify_intent_model(
        user_message,
        attachments=attachments,
        last_route=last_route
    )
    return mode, f"model_orchestrator: {reason}"


def get_thinking_decision_with_reason(message: str, mode: str) -> Tuple[bool, str]:
    """
    Determines whether deep reasoning/thinking is required for the request.
    Returns (should_think: bool, reason: str).

    Spec rules:
    - mode code -> True (always)
    - mode docs/excel/ppt -> False (JSON planning must not think)
    - creation verbs (write/draft/likho/banao/prepare/email/mail) -> False
    - short simple chat (<25 words, no analytical keywords) -> False
    - analysis asks (why/how/explain/compare/calculate/kyun/kaise) -> True
    """
    clean_mode = (mode or "chat").lower()
    if clean_mode in ("code",):
        return True, "code_mode_deep_reasoning"
    if clean_mode in ("docs", "excel", "ppt"):
        return False, "structured_json_mode"

    # Chat / Auto mode analysis
    if not THINK_ON_COMPLEX_CHAT:
        return False, "think_on_complex_chat_disabled"

    text = message.strip()
    words = text.split()

    # Creation verbs -> False (generating, not analyzing)
    if CREATION_VERBS.search(text):
        return False, "creation_verb_detected"

    # Short simple chat -> False
    if len(words) < 25:
        # Check for analytical keywords that override
        kw_match = COMPLEX_THINKING_KEYWORDS.search(text)
        if not kw_match and text.count("?") < 2 and not MULTI_ASK_PATTERNS.search(text) and not PREV_RESULT_PATTERNS.search(text):
            return False, f"short_simple_chat_{len(words)}_words"

    # Word count > 40 -> True
    if len(words) > 40:
        return True, f"word_count_{len(words)}_gt_40"

    # Analytical keywords -> True
    kw_match = COMPLEX_THINKING_KEYWORDS.search(text)
    if kw_match:
        return True, f"analytical_keyword_{kw_match.group(0).lower()}"

    # Multi-question -> True
    if text.count("?") >= 2 or MULTI_ASK_PATTERNS.search(text):
        return True, "multi_question_or_multi_ask"

    # Previous error analysis -> True
    if PREV_RESULT_PATTERNS.search(text):
        return True, "previous_error_analysis"

    return False, "simple_factual_query"


def decide_thinking(message: str, mode: str) -> bool:
    """Convenience helper returning bool for thinking decision."""
    decision, _ = get_thinking_decision_with_reason(message, mode)
    return decision


def get_rag_decision_with_reason(message: str, has_upload: bool = False) -> Tuple[bool, str]:
    """
    Determines whether knowledge base retrieval should be triggered.
    Returns (should_retrieve: bool, reason: str).
    """
    if has_upload:
        return True, "file_upload_present"

    text = message.strip()

    # 1. Equipment Tag Match (e.g. F-101, HEX-201, TK-1002, P-101A, MOV-104)
    tag_match = EQUIPMENT_REGEX_COMPILED.search(text)
    if tag_match:
        return True, f"equipment_tag_{tag_match.group(0).upper()}"

    # 2. Domain Technical Keywords Match
    text_lower = text.lower()
    for kw in RAG_DOMAIN_KEYWORDS:
        if kw in text_lower:
            return True, f"domain_keyword_{kw}"

    return False, "no_sop_or_tag_trigger"


def should_retrieve(message: str, has_upload: bool = False) -> bool:
    """Convenience helper returning bool for RAG gating."""
    decision, _ = get_rag_decision_with_reason(message, has_upload)
    return decision


def is_follow_up_query(message: str) -> bool:
    """Checks if query is a short conversational follow-up request."""
    return bool(FOLLOW_UP_PATTERNS.search(message.strip()))
