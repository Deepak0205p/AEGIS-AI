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

from backend.domains import get_active_domain, get_active_domain_info, get_fallback_text

def get_chat_system_prompt() -> str:
    domain_info = get_active_domain_info()
    domain_name = domain_info["name"]
    domain_code = domain_info["code"]
    standards = ", ".join(domain_info["standards"][:4])
    # get_active_domain_info() has no `fallback_text` key, so this .get() always
    # returned the hardcoded refinery/OISD string. The per-domain texts live in
    # `backend.domains.get_fallback_text()`.
    fallback_notice = get_fallback_text()
    
    return f"""You are AEGIS AI, a sovereign, air-gapped Enterprise AI Assistant dedicated to:
1. Oil Refineries & Upstream E&P (MRPL, ONGC, IOCL style)
2. PSU Heavy Engineering & Manufacturing (BHEL, SAIL, NTPC style)
3. Defence Manufacturing & Strategic Units (DRDO, HAL, BEL style)
4. Government Offices & Secretariats (CSMOP, GFR 2017, RTI 2005 style)

Currently Active Operational Domain: {domain_name} ({domain_code})
Applicable Sovereign Regulatory Standards: {standards}

OPERATIONAL ARCHITECTURE & TWO-TIER POLICY:
1. TIER 1 - PLANT SOPS, VERIFIED CHEMICALS & ASSET THRESHOLDS:
   - For specific internal plant parameters, furnace skin limits (e.g. F-101), pump vibration thresholds (e.g. P-101A/B API 610), PTW/LOTO procedures (OISD-105), and plant SOPs: ground your answer strictly in the RETRIEVED KNOWLEDGE BASE.
   - For verified chemical hazards (H2S, Benzene, Caustic Soda, HF, Chlorine, TEG, MEG, Mercury, etc.): state exact CAS numbers, ACGIH TLV-TWA limits, PPE requirements, and first-aid protocols from the verified database.
   - If internal SOP parameters for a specific equipment tag are NOT found in the knowledge base, state the standard verification notice:
     "{fallback_notice}"

2. TIER 2 - GENERAL SCIENCE, ENGINEERING & PETROCHEMICAL DEFINITIONS:
   - When asked conceptual, scientific, or engineering questions (e.g. 'what is petrochemicals', fractional distillation, catalytic cracking, cavitation in pumps, Nelson curves, metallurgy, gas chromatography, BLEVE):
   - Provide comprehensive, accurate, structured, and authoritative technical explanations suitable for plant engineers and operators.

3. CONVERSATIONAL & CAPABILITY INQUIRIES:
   - When greeted (e.g. 'hi', 'hello', 'hlo') or asked who you are or what you can do (e.g. 'whwo r u', 'tell about what u can do'):
   - Greet the user professionally as AEGIS AI, the Sovereign Industrial AI Assistant for {domain_name}.
   - Detail your capabilities: internal SOP & standard lookup, chemical safety (MSDS/ACGIH), equipment operating limits, engineering calculations via Python sandbox, P&ID visual inspection, and automated Word/Excel/PowerPoint deliverable generation.

4. SCOPE BOUNDARY:
   - Focus strictly on industrial, engineering, scientific, manufacturing, and enterprise matters.
   - If asked completely unrelated casual trivia (celebrities, pop culture, entertainment): politely decline and ask how you can assist with refinery or plant operations.

COMMUNICATION STYLE:
- Respond clearly, authoritatively, and professionally in English or Hinglish as requested by the user.
- Use markdown formatting with bullet points and bold headers for clarity."""



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
    base_prompt = get_chat_system_prompt()
    effective_system = base_prompt

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
                    f"{base_prompt}"
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

    # 2. Internal SOP / GraphRAG Context Injection
    if rag_chunks:
        rag_block = format_rag_context_block(rag_chunks, query=user_message)
        if rag_block:
            effective_system += (
                f"\n\n{rag_block}\n\n"
                "MANDATORY RULE: Answer strictly from the RETRIEVED KNOWLEDGE BASE & GRAPHRAG CONTEXT for internal procedures/equipment. "
                "If the context does not contain the answer, respond with the deterministic fallback notice."
            )
    elif rag_status in ("miss", "no_relevant_context"):
        effective_system += (
            "\n\n[RETRIEVAL STATUS: NO RELEVANT CONTEXT FOUND]\n"
            "None of the documents or SOPs in the local repository cleared the relevance threshold for this query.\n"
            "EXPLICIT DIRECTIVE:\n"
            "1. Plainly and concisely state that no matching operational procedures, standards, or data were found in the provided documents.\n"
            f"2. If internal operating parameters, thresholds, or plant equipment were requested, state: '{get_fallback_text()}'\n"
            "3. If the query is outside plant/industrial operations, state directly that the topic is outside the knowledge base and scope.\n"
            "4. NEVER invent, fabricate, or offer tangential advice, recipes, or ungrounded steps. Stop after the concise not found statement."
        )
    elif rag_status != "skipped":
        rag_block = format_rag_context_block([], query=user_message)
        if rag_block:
            effective_system += f"\n\n{rag_block}\n\n"

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
            # Domain-aware: DETERMINISTIC_FALLBACK_TEXT is the refinery/OISD
            # wording and was returned for every domain.
            clean_response = get_fallback_text()
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
                # Null when no embedding model is in use: a similarity figure
                # must not be invented for a lexical match.
                "similarity_score": c.get("similarity_score"),
                "relevance": c.get("relevance"),
                "match_basis": c.get("match_basis"),
                "provenance": c.get("provenance"),
                "authoritative": c.get("authoritative", False),
            }
            for c in (rag_chunks or [])
        ],
    }
