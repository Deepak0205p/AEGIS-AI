"""
Chat Mode Handler for Air-Gapped Local AI Backend.
Implements Two-Tier Knowledge Policy, Chemical DB context injection,
Adaptive Thinking gating, and zero-leak thinking token streaming.
"""

from typing import AsyncGenerator, Dict, Any, List, Optional
from backend.config import logger, DETERMINISTIC_FALLBACK_TEXT
from backend.ollama_client import call_ollama, filter_thinking
from backend.db import build_context_messages, save_message
from backend.knowledge_base import format_rag_context_block
from backend.chemical_kb import detect_chemicals, format_chemical_context_block

CHAT_SYSTEM_PROMPT = """You are AEGIS AI, an authoritative Industrial Operations & Plant Safety Assistant for ONGC & MRPL refineries.

TWO-TIER KNOWLEDGE POLICY:
1. TIER 1 (INTERNAL REFINERY PROCEDURES & EQUIPMENT PARAMETERS):
   - When the user asks about refinery-specific procedures, operating parameters, equipment tags (e.g. F-101, P-101A, CDU, VDU), maintenance schedules, or internal standards:
   - Answer strictly and exclusively from the verified RETRIEVED CONTEXT provided below.
   - If internal parameters or equipment specifics are missing from the retrieved context, respond strictly with:
     "Operational parameters for this query are not indexed in active Master SOPs (OISD/API/MRPL). Manual entry or Shift In-Charge sign-off required."
   - NEVER invent or guess temperature limits, vibration thresholds, clause numbers, or refinery operating values.

2. TIER 2 (GENERAL KNOWLEDGE, DEFINITIONS & SCIENCE):
   - When the user asks general science questions, definitions, concepts (e.g. "what is benzene", "what is photosynthesis", general chemistry/physics/safety principles):
   - Answer normally and clearly from model knowledge in 2 to 6 concise sentences.
   - CRITICAL RESTRICTION ON CAS NUMBERS & EXPOSURE LIMITS:
     * NEVER recite CAS numbers, TLV/TWA exposure limits, flash points, exact clause numbers, or legal compliance thresholds from unverified memory.
     * State exact CAS numbers, chemical formulas, and exposure limits ONLY when present in the VERIFIED CHEMICAL DATABASE CONTEXT provided in the prompt.
     * If specific numerical regulatory limits or CAS numbers are requested for a substance not in the local database context, state: "Chemical data not available in local verified database."
   - Never invent organization-specific policies or refinery plant data.

NATURAL CONVERSATION:
- Reply in the user's language/style (Hinglish/English).
- Keep factual responses concise, direct, and authoritative."""


async def handle_chat_mode(
    chat_id: str,
    user_message: str,
    think: bool = False,
    rag_chunks: Optional[List[Dict[str, Any]]] = None,
    rag_status: str = "skipped",
    agent_id: Optional[str] = None,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Executes grounded generation with Two-Tier policy, Chemical DB injection, and Custom Agent personas:
    - think: bool (whether to emit thinking frames)
    - rag_chunks: list of retrieved SOP chunks or None
    - rag_status: 'hit' | 'miss' | 'skipped'
    - agent_id: Optional custom agent id
    """
    # Detect chemical mentions
    detected_chemicals = detect_chemicals(user_message)
    chem_names = [c["name"] for c in detected_chemicals]

    logger.info(
        f"[CHAT_MODE] chat_id={chat_id} agent_id={agent_id} think={think} rag_status={rag_status} "
        f"chunks_count={len(rag_chunks or [])} chemicals_detected={chem_names}"
    )

    # Save user message to database
    save_message(chat_id, "user", user_message, mode="chat")

    # Construct effective system prompt with Custom Agent persona, Chemical DB & RAG grounding
    effective_system = CHAT_SYSTEM_PROMPT

    if agent_id:
        try:
            from backend.custom_agents import get_agent_by_id
            custom_agent = get_agent_by_id(agent_id)
            if custom_agent:
                effective_system = (
                    f"=== ACTIVE CUSTOM AGENT: {custom_agent.name} ({custom_agent.role}) ===\n"
                    f"{custom_agent.system_prompt}\n"
                    f"Workflow Mode: {custom_agent.workflow_mode}\n"
                    f"Enabled Tools: {', '.join(custom_agent.tools)}\n"
                    "=========================================================\n\n"
                    f"{CHAT_SYSTEM_PROMPT}"
                )
                logger.info(f"[CHAT_MODE] Injected custom agent persona '{custom_agent.name}' into system prompt")
        except Exception as ag_err:
            logger.warning(f"[CHAT_MODE] Custom agent injection warning: {ag_err}")

    # 1. Chemical DB Context Injection
    if detected_chemicals:
        chem_block = format_chemical_context_block(detected_chemicals)
        effective_system += (
            f"\n\n{chem_block}\n\n"
            "MANDATORY RULE FOR CHEMICALS: State the exact CAS number, chemical formula, ACGIH TLV-TWA, "
            "hazards, PPE, and refinery context directly from the VERIFIED CHEMICAL DATABASE above. "
            "Do NOT invent or guess any values."
        )

    # 2. Internal SOP / RAG Context Injection
    if rag_chunks:
        rag_block = format_rag_context_block(rag_chunks)
        effective_system += (
            f"\n\n{rag_block}\n\n"
            "MANDATORY RULE: Answer strictly from the RETRIEVED CONTEXT for internal procedures/equipment. "
            "If the context does not contain the answer, respond with the deterministic fallback notice."
        )
    elif rag_status == "miss":
        effective_system += (
            f"\n\nNOTE: No matching internal SOP documentation was found for this specific query in the local repository. "
            f"If internal operating parameters or equipment thresholds are requested, output: '{DETERMINISTIC_FALLBACK_TEXT}'"
        )

    # Build context messages with history
    messages = await build_context_messages(chat_id, effective_system, user_message)

    # Stream from Ollama (num_predict=2048)
    full_content_tokens: List[str] = []
    full_thinking_tokens: List[str] = []
    token_generator = await call_ollama(
        messages,
        stream=True,
        temperature=0.3 if (rag_chunks or detected_chemicals) else 0.5,
        max_tokens=2048,
        think=think,
    )

    async for chunk in token_generator:
        chunk_type = chunk.get("type", "content")
        token_text = chunk.get("token", "")

        if chunk_type == "thinking":
            full_thinking_tokens.append(token_text)
            if think:
                yield {"thinking": token_text, "event": "step", "step_type": "thought", "content": token_text}
        else:
            full_content_tokens.append(token_text)
            yield {"token": token_text, "event": "step", "step_type": "token", "content": token_text}

    raw_response = "".join(full_content_tokens)
    clean_response = filter_thinking(raw_response)

    # Fallback: if model put everything in thinking and content is empty,
    # extract usable text from the thinking stream
    if not clean_response.strip() and full_thinking_tokens:
        thinking_text = "".join(full_thinking_tokens)
        clean_thinking = filter_thinking(thinking_text)
        if clean_thinking.strip():
            clean_response = clean_thinking
            yield {"token": clean_response, "event": "step", "step_type": "token", "content": clean_response}

    # Fallback guardrail check: if output is empty and RAG missed
    if not clean_response.strip():
        if rag_status == "miss" or (rag_chunks and not full_content_tokens):
            clean_response = DETERMINISTIC_FALLBACK_TEXT
            yield {"token": clean_response, "event": "step", "step_type": "token", "content": clean_response}

    # Persist assistant response (cleaned, zero thinking leak)
    save_message(chat_id, "assistant", clean_response, mode="chat")

    # Final event
    yield {
        "done": True,
        "generated_file": None,
        "run_output": None,
        "content": clean_response,
        "chemicals_detected": chem_names,
        "citations": [
            {
                "doc_id": c["doc_id"],
                "clause": c["clause"],
                "page": c["page"],
                "similarity_score": c["similarity_score"],
            }
            for c in (rag_chunks or [])
        ],
    }
