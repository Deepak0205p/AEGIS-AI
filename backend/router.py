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


async def classify_intent_fast(user_message: str) -> Optional[str]:
    """
    Phase 3: Ultra-fast single-token LLM intent classifier for zero-match ambiguous queries.
    Uses temperature=0.0 and max_tokens=10 with think=False to classify in ~50-100ms.
    """
    from backend.ollama_client import call_ollama, filter_thinking

    prompt = [
        {
            "role": "system",
            "content": (
                "You are an intent routing classifier for an industrial sovereign AI. "
                "Classify the user's primary request into EXACTLY ONE word from: "
                "[code, docs, excel, ppt, chat]. "
                "Rules:\n"
                "- code: programming, scripts, debugging, algorithms, math computation\n"
                "- docs: formal Word reports, memos, official notices, letters\n"
                "- excel: spreadsheets, tabular datasets, accounting, tables with formulas\n"
                "- ppt: presentation slides, pitch decks\n"
                "- chat: general conversation, questions about plant equipment, SOPs, explanations\n"
                "Respond with ONLY the lowercase classification word."
            ),
        },
        {"role": "user", "content": user_message.strip()[:300]},
    ]
    try:
        raw_res = await call_ollama(prompt, stream=False, temperature=0.0, max_tokens=8, think=False)
        cleaned = filter_thinking(str(raw_res)).strip().lower()
        for candidate in ["code", "excel", "ppt", "docs", "chat"]:
            if candidate in cleaned:
                logger.info(f"[FAST_CLASSIFIER] Ambiguous query '{user_message[:40]}' classified as '{candidate}'")
                return candidate
    except Exception as e:
        logger.warning(f"[FAST_CLASSIFIER] Fast classification failed: {e}")
    return None


async def route_message_async(
    user_message: str,
    mode_override: Optional[str] = "auto",
    attachments: Optional[List[str]] = None,
    last_route: Optional[str] = None,
    allow_multi: bool = False
) -> Tuple[str, Optional[str]]:
    """
    Asynchronous version of route_message that executes deterministic heuristic checks first,
    and falls back to fast micro-LLM intent classification if heuristics yield 'default_chat'
    on multi-word ambiguous prompts.
    """
    route, trigger = route_message(
        user_message,
        mode_override=mode_override,
        attachments=attachments,
        last_route=last_route,
        allow_multi=allow_multi
    )
    
    # If heuristic was decisive or manually overridden, return immediately (0ms overhead)
    if trigger != "default_chat" or (mode_override and mode_override != "auto"):
        return route, trigger

    # Only run fast micro-classifier if query is substantive (> 3 words) and lacks SOP tag context
    words = user_message.strip().split()
    if len(words) >= 4 and not EQUIPMENT_REGEX_COMPILED.search(user_message):
        classified_mode = await classify_intent_fast(user_message)
        if classified_mode and classified_mode in ("code", "docs", "excel", "ppt"):
            return classified_mode, "fast_llm_classifier"

    return route, trigger


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
