"""
Heuristic Router & Execution Policy for Air-Gapped Local AI Backend.
Performs fast, deterministic keyword/regex matching, adaptive thinking decision,
and RAG retrieval gating with ZERO extra LLM calls.
"""

import re
from typing import Tuple, Optional, List
from backend.config import (
    logger,
    EQUIPMENT_TAG_REGEX,
    RAG_DOMAIN_KEYWORDS,
    THINK_ON_COMPLEX_CHAT,
)

# Regex patterns for mode routing
# NOTE: "email" and "mail" deliberately EXCLUDED — those stay in chat (copy-paste text)
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


def route_message(user_message: str, mode_override: Optional[str] = "auto") -> Tuple[str, Optional[str]]:
    """
    Determines execution route for incoming message.
    Returns (route_name, trigger_keyword).
    """
    clean_override = (mode_override or "").strip().lower()

    # Handle explicit mode overrides
    if clean_override and clean_override not in ("auto", "", "orchestrator"):
        valid_modes = {"chat", "code", "docs", "excel", "ppt"}
        if clean_override in valid_modes:
            logger.info(f"[ROUTER] Route decision: '{clean_override}' via manual mode override")
            return clean_override, "manual_override"
        elif clean_override in ("vision", "ocr"):
            logger.info(f"[ROUTER] Route '{clean_override}' unsupported, fallback to 'chat'")
            return "chat", f"fallback_{clean_override}"

    # Heuristic Regex Matching
    message_text = user_message.strip()

    # Check if message has equipment tag + technical context -> force chat (RAG)
    has_tag = bool(EQUIPMENT_REGEX_COMPILED.search(message_text))
    has_tech_context = bool(re.search(
        r"\b(inspection|utm|thickness|corrosion|vibration|temperature|pressure|calibration|"
        r"reading|measurement|incident|spill|leak|failure|breakdown|sop|procedure|"
        r"maintenance|repair|safety|report)\b",
        message_text, re.IGNORECASE
    ))
    if has_tag and has_tech_context:
        logger.info("[ROUTER] Route decision: 'chat' (equipment tag + technical context override)")
        return "chat", "tag_tech_override"

    for route_name, pattern in ROUTING_PATTERNS:
        match = pattern.search(message_text)
        if match:
            trigger_keyword = match.group(0).lower()
            logger.info(f"[ROUTER] Route decision: '{route_name}' triggered by keyword: '{trigger_keyword}'")
            return route_name, trigger_keyword

    # Default fallback
    logger.info("[ROUTER] Route decision: 'chat' (no specific keyword match)")
    return "chat", "default_chat"


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
