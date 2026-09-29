"""
Agentic Multi-Step Task Orchestrator & Tool Execution Loop.
Enforces:
1. Explicit planning step (2-6 numbered steps) generated and logged before tool calls begin.
2. Step-by-step execution with progress check-off.
3. Hard max-iteration and max-tool-call limits with loud failure logs.
4. Input schema validation for all tools (file ops, sandbox, spreadsheets, doc search).
5. Output size-capping of tool returns before reinjection into context.
6. Structured error surfacing (no infinite loops or swallowed errors).
7. Explicit final answer synthesis in a SEPARATE model call isolated from tool-use scratchpads.
"""

import json
import re
import time
from typing import AsyncGenerator, Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field, ValidationError

from backend.config import (
    logger,
    AGENT_MAX_ITERATIONS,
    AGENT_MAX_TOOL_CALLS,
    TOOL_RETURN_MAX_CHARS,
    MIN_RAG_SCORE,
    MAX_RAG_CHUNKS,
    FINAL_SYNTHESIS_TEMPERATURE,
    TASK_MAX_WORDS,
)
from backend.structured_logger import (
    get_current_request_id,
    log_stage_event,
    log_tool_call,
    log_agent_plan,
    log_agent_limit_hit,
    log_raw_model_prompt,
    log_post_generation_audit,
)
from backend.ollama_client import call_ollama, filter_thinking
from backend.db import build_context_messages, save_message


# ══════════════════════════════════════════════════════════════════════════
# TOOL INPUT VALIDATION SCHEMAS
# ══════════════════════════════════════════════════════════════════════════

class SearchToolInput(BaseModel):
    query: str = Field(min_length=2, max_length=500)
    top_k: int = Field(default=3, ge=1, le=5)

class CodeExecToolInput(BaseModel):
    code: str = Field(min_length=5, max_length=50000)
    stdin_input: Optional[str] = Field(default=None, max_length=2000)

class DeliverableToolInput(BaseModel):
    mode: str = Field(pattern="^(docs|excel|ppt)$")
    title: str = Field(min_length=2, max_length=200)
    blocks: List[Dict[str, Any]] = Field(default_factory=list)


def cap_tool_result_size(result_str: str, max_chars: int = TOOL_RETURN_MAX_CHARS) -> Tuple[str, bool]:
    """Cuts off oversized tool returns with an explicit truncation indicator."""
    if len(result_str) <= max_chars:
        return result_str, False
    excess = len(result_str) - max_chars
    truncated = result_str[:max_chars] + f"\n\n[... TRUNCATED {excess} CHARS TO PREVENT CONTEXT OVERFLOW ...]"
    return truncated, True


# ══════════════════════════════════════════════════════════════════════════
# AGENT TOOL RUNNERS WITH SCHEMA VALIDATION & OUTPUT CAPPING
# ══════════════════════════════════════════════════════════════════════════

def execute_tool_call(tool_name: str, args: Dict[str, Any], chat_id: str) -> Dict[str, Any]:
    """
    Validates input schema, executes the tool, size-caps return text,
    and returns a structured result or structured error.
    """
    t0 = time.perf_counter()
    req_id = get_current_request_id()

    try:
        if tool_name == "doc_search":
            validated = SearchToolInput(**args)
            from backend.knowledge_base import search_sops
            chunks = search_sops(validated.query, min_score=MIN_RAG_SCORE, top_k=min(validated.top_k, MAX_RAG_CHUNKS))
            if not chunks:
                ret_text = "No matching internal SOP documents found clearing the relevance threshold."
            else:
                def _cite(c):
                    # A similarity figure only exists when real embeddings are in
                    # use; otherwise report the lexical score actually computed.
                    sim = c.get("similarity_score")
                    score = f"cosine {sim:.3f}" if isinstance(sim, (int, float)) else f"bm25 {c.get('bm25_score', 0.0):.2f}"
                    prov = c.get("provenance", "unknown")
                    return f"[{c['doc_id']} | {score} | {prov}]: {c['content']}"
                ret_text = "\n\n".join([_cite(c) for c in chunks])
            
            capped_text, was_capped = cap_tool_result_size(ret_text)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            log_tool_call("doc_search", validated.dict(), {"chars": len(capped_text), "was_capped": was_capped}, elapsed_ms=elapsed_ms, success=True, request_id=req_id)
            return {"success": True, "output": capped_text, "truncated": was_capped}

        elif tool_name == "code_sandbox":
            validated = CodeExecToolInput(**args)
            from backend.sandbox import execute_python_sandbox
            res = execute_python_sandbox(validated.code, stdin_input=validated.stdin_input)
            
            out_parts = []
            if res.get("stdout"):
                out_parts.append(f"STDOUT:\n{res['stdout'].strip()}")
            if res.get("stderr"):
                out_parts.append(f"STDERR:\n{res['stderr'].strip()}")
            if not out_parts:
                out_parts.append("(Script produced no output)")
            out_parts.append(f"EXIT_CODE: {res.get('exit_code', -1)}")

            raw_out = "\n\n".join(out_parts)
            capped_text, was_capped = cap_tool_result_size(raw_out)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            is_success = (res.get("exit_code") == 0)
            log_tool_call("code_sandbox", {"code_len": len(validated.code)}, {"exit_code": res.get("exit_code"), "out_len": len(capped_text)}, elapsed_ms=elapsed_ms, success=is_success, request_id=req_id)
            return {"success": is_success, "output": capped_text, "truncated": was_capped, "generated_files": res.get("generated_files", [])}

        elif tool_name == "deliverable_builder":
            validated = DeliverableToolInput(**args)
            from backend.deliverables import create_deliverable_file
            res = create_deliverable_file({"title": validated.title, "blocks": validated.blocks}, validated.mode, chat_id)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            log_tool_call("deliverable_builder", {"mode": validated.mode, "title": validated.title}, res, elapsed_ms=elapsed_ms, success=True, request_id=req_id)
            return {"success": True, "output": f"Created {validated.mode.upper()} deliverable: {res.get('filename')} (url: {res.get('download_url')})", "file": res}

        else:
            err_msg = f"Unknown tool requested: '{tool_name}'. Available tools: ['doc_search', 'code_sandbox', 'deliverable_builder']"
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            log_tool_call(tool_name, args, None, elapsed_ms=elapsed_ms, success=False, error=err_msg, request_id=req_id)
            return {"success": False, "error": err_msg}

    except ValidationError as val_err:
        err_msg = f"Schema validation failed for tool '{tool_name}': {str(val_err)}"
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        log_tool_call(tool_name, args, None, elapsed_ms=elapsed_ms, success=False, error=err_msg, request_id=req_id)
        return {"success": False, "error": err_msg}
    except Exception as exc:
        err_msg = f"Execution error in tool '{tool_name}': {str(exc)}"
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        log_tool_call(tool_name, args, None, elapsed_ms=elapsed_ms, success=False, error=err_msg, request_id=req_id)
        return {"success": False, "error": err_msg}


# ══════════════════════════════════════════════════════════════════════════
# MULTI-STEP AGENT LOOP
# ══════════════════════════════════════════════════════════════════════════

PLANNING_SYSTEM_PROMPT = """You are the Lead Planning Agent for an industrial workstation.
Analyze the user's request and formulate an explicit, concise numbered plan (2 to 5 steps max).
Keep steps concrete, action-oriented, and focused.
Return ONLY a valid JSON object matching this schema:
{
  "plan": [
    "Step 1: <action>",
    "Step 2: <action>",
    "Step 3: <action>"
  ]
}
Do NOT return prose or explanation outside the JSON."""

FINAL_ANSWER_SYSTEM_PROMPT = """You are the Senior Technical Reporting Officer.
Your objective: Deliver the final deliverable to the user based EXCLUSIVELY on verified tool execution results and factual context provided.

STRICT DELIVERABLE OUTPUT CONTRACTS BY TASK TYPE:
1. For Approval Note / Inspection Tasks:
   - Output ONLY the following 4 sections:
     # [Title of Note]
     ## 1. Verified Findings
     (Bulleted, containing only facts verified from report & tools)
     ## 2. Technical Evaluation & Calculations
     (Exact numerical parameters, remaining life, or compliance threshold)
     ## 3. Engineering Recommendation
     (Direct actionable decision: approve / derate / repair / re-inspect)
     ## 4. Sign-Off Block
     (Authority, Date, Review Status)
   - Do NOT include any disclaimers, caveats, "As an AI", or restatements of instructions.
   - Do NOT include conversational filler, meta-commentary, or unrequested background.
2. For Code / Engineering Calculation Tasks:
   - Output ONLY: (a) Verified numerical findings and metrics, (b) Exact status or generated artifacts.
3. For General Deliverable Tasks:
   - Deliver only factual verified operational sections."""

# Common generic filler phrases that trigger post-generation stripping / regeneration
GENERIC_FILLER_PATTERNS = [
    r"(?i)as an ai(?:\s+language model|\s+assistant)?",
    r"(?i)it is important to note that(?:\s+this)?",
    r"(?i)please note that(?:\s+this)?",
    r"(?i)disclaimer[:\s].*",
    r"(?i)note:\s*this recommendation is based on.*?(?:\n|$)",
    r"(?i)note:\s*this audit is based on.*?(?:\n|$)",
    r"(?i)always consult with a certified.*?(?:\n|$)",
    r"(?i)this is not financial or engineering advice",
    r"(?i)in conclusion,?\s*",
    r"(?i)hope this helps",
]


def audit_and_clean_final_output(
    text: str,
    task_type: str = "approval_note",
    max_words: Optional[int] = None,
) -> Tuple[str, bool, List[str]]:
    """
    Post-generation check:
    1. Scans for generic filler, boilerplate disclaimers, and conversational padding.
    2. Strips flagged filler sections cleanly.
    3. Enforces hard max-word bounds per task type.
    Returns (cleaned_text, passed_clean, list_of_flagged_phrases).
    """
    flagged = []
    cleaned = text.strip()

    for pattern in GENERIC_FILLER_PATTERNS:
        matches = re.findall(pattern, cleaned)
        if matches:
            flagged.extend([m.strip() if isinstance(m, str) else str(m) for m in matches])
            cleaned = re.sub(pattern, "", cleaned).strip()

    # Clean double blank lines left after stripping
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    # Enforce word limit
    limit = max_words or TASK_MAX_WORDS.get(task_type, 400)
    words = cleaned.split()
    word_count = len(words)

    if word_count > limit:
        flagged.append(f"Exceeded max words: {word_count} > {limit}")
        # Truncate at nearest sentence boundary before the limit
        truncated_words = words[:limit]
        candidate = " ".join(truncated_words)
        last_period = max(candidate.rfind("."), candidate.rfind("\n"))
        if last_period > len(candidate) // 2:
            cleaned = candidate[:last_period + 1]
        else:
            cleaned = candidate + "..."

    passed = (len(flagged) == 0)
    return cleaned, passed, flagged


async def run_multistep_agent_loop(
    chat_id: str,
    user_query: str,
    tools_enabled: Optional[List[str]] = None,
    max_iterations: int = AGENT_MAX_ITERATIONS,
    max_tool_calls: int = AGENT_MAX_TOOL_CALLS,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Executes a structured, bounded agent loop:
    Phase 1: Explicit Plan Generation & Logging
    Phase 2: Step-by-Step Tool Execution with hard caps and size-capped results
    Phase 3: Separate Final Answer Synthesis (clean deliverable, zero scratchpad leakage)
    """
    req_id = get_current_request_id()
    yield {"event": "agent_start", "token": "📋 Initializing agent workflow & plan...\n\n"}

    # ──────────────────────────────────────────────────────────────────────
    # PHASE 1: EXPLICIT PLAN STEP
    # ──────────────────────────────────────────────────────────────────────
    plan_messages = [
        {"role": "system", "content": PLANNING_SYSTEM_PROMPT},
        {"role": "user", "content": f"Task: {user_query}"}
    ]

    try:
        raw_plan_resp = await call_ollama(
            plan_messages,
            stream=False,
            temperature=0.1,
            json_mode=True,
            max_tokens=512,
            think=False,
        )
        plan_data = json.loads(str(raw_plan_resp))
        plan_steps = plan_data.get("plan", [])
        if not isinstance(plan_steps, list) or len(plan_steps) < 2:
            plan_steps = [
                f"Step 1: Retrieve context and data for '{user_query[:50]}'",
                "Step 2: Execute required computation or verification in sandbox",
                "Step 3: Synthesize verified final findings"
            ]
    except Exception as plan_err:
        logger.warning(f"[AGENT] Planning error ({plan_err}). Using default plan.")
        plan_steps = [
            f"Step 1: Analyze requirements for '{user_query[:50]}'",
            "Step 2: Execute required verification tools",
            "Step 3: Compile verified report"
        ]

    # Log and emit plan
    log_agent_plan(plan_steps, request_id=req_id)
    plan_display = "\n".join([f"  {step}" for step in plan_steps])
    yield {
        "event": "agent_plan",
        "plan": plan_steps,
        "token": f"**Execution Plan:**\n{plan_display}\n\n---\n"
    }

    # ──────────────────────────────────────────────────────────────────────
    # PHASE 2: STEP-BY-STEP TOOL EXECUTION LOOP
    # ──────────────────────────────────────────────────────────────────────
    completed_steps = []
    tool_results_memory = []
    iteration_count = 0
    total_tool_calls_executed = 0
    active_step_idx = 0

    while active_step_idx < len(plan_steps):
        iteration_count += 1

        # Check hard max-iteration limit
        if iteration_count > max_iterations:
            log_agent_limit_hit("MAX_ITERATIONS", iteration_count, max_iterations, request_id=req_id)
            yield {
                "event": "agent_error",
                "token": f"\n\n⚠️ **Hard Limit Reached:** Exceeded maximum task iterations ({max_iterations}). Halting loop to prevent infinite cycling.\n"
            }
            break

        current_step_text = plan_steps[active_step_idx]
        yield {
            "event": "agent_step_start",
            "step_index": active_step_idx + 1,
            "step_text": current_step_text,
            "token": f"\n▶️ **Executing Step {active_step_idx + 1}/{len(plan_steps)}:** {current_step_text}\n"
        }

        # Determine appropriate tool based on step content
        step_lower = current_step_text.lower()
        tool_to_call = None
        tool_args = {}

        if any(w in step_lower for w in ["search", "retrieve", "lookup", "sop", "standard", "standards", "rules", "threshold", "limits", "compliance", "requirements", "review asme", "review api"]):
            tool_to_call = "doc_search"
            tool_args = {"query": user_query, "top_k": 3}
        elif any(w in step_lower for w in ["calculate", "math", "python", "code", "run", "simulation", "compute", "evaluation", "verify thickness", "corrosion", "life"]):
            tool_to_call = "code_sandbox"
            # Prompt model for quick code block for this specific step
            code_prompt = [
                {"role": "system", "content": "You are a code execution worker. Write ONE self-contained Python script to solve the requested step. Print the answer. Return ONLY ```python ... ``` without conversational text."},
                {"role": "user", "content": f"Task: {user_query}\nPlan Step: {current_step_text}"}
            ]
            code_resp = await call_ollama(code_prompt, stream=False, temperature=0.1, think=False)
            from backend.code_mode import extract_python_code
            extracted = extract_python_code(str(code_resp))
            if extracted:
                tool_args = {"code": extracted}
            else:
                # No code block came back. Do NOT fabricate a placeholder script:
                # a fixed `print()` exits 0, was streamed to the user as
                # "Tool code_sandbox returned ...", and was rendered in the final
                # synthesis under "Verified Outcome". Report the real failure
                # instead so the step surfaces as incomplete.
                tool_to_call = None
                logger.warning(
                    f"[AGENT LOOP] Model produced no ```python block for step "
                    f"{active_step_idx + 1}; skipping the code_sandbox tool "
                    f"rather than executing a placeholder."
                )
                yield {
                    "event": "agent_error",
                    "token": (
                        f"\n\n⚠️ Step {active_step_idx + 1} ('{current_step_text[:80]}') "
                        f"required a calculation, but the planner returned no "
                        f"executable code. This step is reported as incomplete.\n"
                    ),
                }
        elif any(w in step_lower for w in ["generate deliverable", "create note", "approval note", "create document", "build document", "deliverable"]):
            tool_to_call = "deliverable_builder"
            tool_args = {
                "mode": "docs",
                "title": "Approval Note - Inspection Assessment",
                "blocks": [
                    {"type": "heading", "text": "Approval Note: Inspection Evaluation", "level": 1},
                    {"type": "paragraph", "text": f"Generated based on verified multi-step inspection evaluation for: {user_query}"}
                ]
            }

        if tool_to_call:
            # Check hard max-tool-call limit
            if total_tool_calls_executed >= max_tool_calls:
                log_agent_limit_hit("MAX_TOOL_CALLS", total_tool_calls_executed, max_tool_calls, request_id=req_id)
                yield {
                    "event": "agent_error",
                    "token": f"\n\n⚠️ **Hard Limit Reached:** Exceeded maximum allowed tool calls ({max_tool_calls}). Stopping tool execution.\n"
                }
                break

            total_tool_calls_executed += 1
            tool_res = execute_tool_call(tool_to_call, tool_args, chat_id)
            tool_success = tool_res.get("success", False)
            out_preview = tool_res.get("output", "")[:250].replace("\n", " ")

            if tool_success:
                yield {
                    "event": "tool_result",
                    "tool": tool_to_call,
                    "token": f"  ✓ Tool `{tool_to_call}` returned: {out_preview}...\n"
                }
                tool_results_memory.append({
                    "step": current_step_text,
                    "tool": tool_to_call,
                    "result": tool_res.get("output", "")
                })
            else:
                err_text = tool_res.get("error", "Unknown error")
                yield {
                    "event": "tool_error",
                    "tool": tool_to_call,
                    "token": f"  ✗ Tool `{tool_to_call}` error: {err_text}\n"
                }
                tool_results_memory.append({
                    "step": current_step_text,
                    "tool": tool_to_call,
                    "error": err_text
                })
        else:
            yield {
                "event": "step_info",
                "token": f"  ℹ️ Step processed analytically.\n"
            }

        # Check off completed step
        completed_steps.append(current_step_text)
        yield {
            "event": "agent_step_done",
            "step_index": active_step_idx + 1,
            "token": f"  ✅ Completed Step {active_step_idx + 1}.\n"
        }
        active_step_idx += 1

    # ──────────────────────────────────────────────────────────────────────
    # PHASE 3: SEPARATE FINAL ANSWER SYNTHESIS STEP
    # ──────────────────────────────────────────────────────────────────────
    yield {
        "event": "final_answer_start",
        "token": "\n---\n### 🎯 Final Verified Report\n"
    }

    # Format verified evidence memory (clean & bounded)
    evidence_lines = []
    for item in tool_results_memory:
        st = item.get("step", "")
        if "result" in item:
            evidence_lines.append(f"- Verified Outcome for '{st}':\n  {item['result']}")
        elif "error" in item:
            evidence_lines.append(f"- Tool Note for '{st}': Failed with {item['error']}")

    evidence_context = "\n\n".join(evidence_lines) if evidence_lines else "No external tools were executed; report direct factual operational findings."

    # Determine task type and word limit.
    # Matched on word boundaries: the previous `k in query_lower` test meant
    # "ean" matched clean/meaning/linear/ocean and "note" matched notes/denote,
    # so "write python code to clean the CSV" was classified approval_note and
    # the code_findings branch was unreachable for it.
    query_lower = user_query.lower()

    def _has_word(*words: str) -> bool:
        return any(re.search(r"(?<!\w)" + re.escape(w) + r"(?!\w)", query_lower) for w in words)

    if _has_word("approval", "ean", "note", "notes", "recommendation"):
        task_type = "approval_note"
    elif _has_word("inspection", "vessel", "thickness"):
        task_type = "inspection_report"
    elif _has_word("code", "python", "script", "compute", "calculation", "calculate"):
        task_type = "code_findings"
    else:
        task_type = "general_deliverable"

    max_word_limit = TASK_MAX_WORDS.get(task_type, 400)
    contract_directive = (
        f"\nHARD CONSTRAINT: This deliverable must NOT exceed {max_word_limit} words. "
        "Strictly adhere to the section structure. Do NOT include disclaimers, restated instructions, "
        "or conversational padding."
    )

    final_messages = [
        {"role": "system", "content": FINAL_ANSWER_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"TASK TYPE: {task_type.upper()}\n"
                f"USER QUERY: {user_query}\n\n"
                f"VERIFIED TOOL RESULTS & EVIDENCE:\n{evidence_context}\n\n"
                f"{contract_directive}\n"
                "Synthesize the authoritative final answer now strictly following the directives above."
            )
        }
    ]

    log_stage_event(
        stage="FINAL_ANSWER_SYNTHESIS",
        status="STARTED",
        request_id=req_id,
        input_summary=f"task_type={task_type}, max_words={max_word_limit}, temp={FINAL_SYNTHESIS_TEMPERATURE}",
    )

    final_tokens = []
    # Hard temperature: Low temperature (0.10) specifically avoids rambling
    final_gen = await call_ollama(
        final_messages,
        stream=True,
        temperature=FINAL_SYNTHESIS_TEMPERATURE,
        think=False
    )
    async for chunk in final_gen:
        token = chunk.get("token", "")
        if token:
            final_tokens.append(token)
            yield {
                "event": "step",
                "step_type": "token",
                "token": token,
                "content": token
            }

    raw_output = "".join(final_tokens).strip()

    # Post-generation compliance check & clean
    cleaned_output, passed_audit, flagged_items = audit_and_clean_final_output(
        raw_output,
        task_type=task_type,
        max_words=max_word_limit
    )

    log_post_generation_audit(
        task_type=task_type,
        passed=passed_audit,
        stripped_phrases=flagged_items,
        word_count=len(cleaned_output.split()),
        max_words=max_word_limit,
        regenerated=False,
        request_id=req_id
    )

    log_stage_event(
        stage="FINAL_ANSWER_SYNTHESIS",
        status="SUCCESS",
        request_id=req_id,
        output_summary=f"final_answer_chars={len(cleaned_output)}, word_count={len(cleaned_output.split())}, cleaned={not passed_audit}",
    )

    save_message(chat_id, "assistant", cleaned_output, mode="agentic")
    yield {"event": "done", "done": True}
