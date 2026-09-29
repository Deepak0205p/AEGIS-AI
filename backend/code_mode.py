"""
Code Mode Handler.
Enforces the sandbox as the ONLY source of truth.
Generates code, runs in sandbox, retries on failure (up to 2 times), and displays verbatim sandbox output.
"""

import re
from typing import AsyncGenerator, Dict, Any, List, Optional
from backend.config import logger, GENERATED_DIR
from backend.ollama_client import call_ollama, filter_thinking
from backend.db import build_context_messages, save_message, save_file_record
from backend.sandbox import execute_python_sandbox

CODE_SYSTEM_PROMPT = """ANTI-HALLUCINATION RULES:
- Answer ONLY from: (a) the user's messages, (b) conversation history, (c) actual tool/sandbox output. Nothing else.
- NEVER invent: numbers, dates, names, standards/clause numbers, quotes, file contents, or "results" of anything we did not actually run.

PYTHON CODE GENERATION DIRECTIVE:
You are an expert Python engineer. Return ONE complete, runnable, fast-executing Python 3 script in a single ```python ... ``` code block tailored directly to the user's request.
CRITICAL EXECUTION RULES:
1. All scripts must execute and finish in less than 1 second.
2. For iteration, prefer `for` loops (e.g. `for n in range(...)`). If using a `while` loop, always ensure proper termination to prevent infinite loops.
3. Print final results clearly using print().
4. Use only Python standard library or pandas/numpy/matplotlib/openpyxl as required.
5. Return ONLY the executable Python script in ```python ... ``` block without conversational filler.
NON-INTERACTIVE EXECUTION RULE (MANDATORY):
- The script is executed as `python main.py` with NO command-line arguments and NO
  interactive stdin. Therefore:
    * NEVER call `input()` or read from stdin (raises EOFError).
    * NEVER require command-line arguments - `sys.argv` is empty, so argparse
      and `sys.argv[1]` will fail.
- The script MUST run to completion and PRINT A RESULT every time.
- If the user's request omits the numbers needed, define clearly named example
  values at the top of the script, print which values were used, and print the
  final computed answer. Never print only a usage/help/prompt message.
- The printed output is the only thing the user sees, so the concrete computed
  numbers MUST appear in the print statements."""


def extract_python_code(response_text: str) -> Optional[str]:
    """Extracts code from ```python ... ``` or ``` ... ``` block."""
    # Match ```python <code> ```
    pattern = re.compile(r"```(?:python)?\s*([\s\S]*?)```", re.IGNORECASE)
    matches = pattern.findall(response_text)
    if matches:
        # Return the longest code block
        return max(matches, key=len).strip()
    return None


def _run_produced_result(result: Optional[Dict[str, Any]]) -> bool:
    """
    True when a successful run actually produced a usable result.

    Exit code 0 is not enough: a script that only prints "Please provide the
    radius..." has not answered the question. Treating that as success made the
    pipeline report a "verified finding" with no computed value in it.
    """
    if not result or not result.get("success"):
        return False
    stdout = (result.get("stdout") or "").strip()
    if not stdout:
        return False

    # Output that only asks the user for more information is not a result.
    only_a_prompt = re.sub(
        r"[\s`*_#.:,-]", " ", stdout.lower()
    )
    asks_for_more = re.search(
        r"\b(please\s+(provide|enter|supply|give)|enter\s+the|provide\s+the|"
        r"usage|arguments?\s+required|not\s+enough\s+information)\b",
        only_a_prompt,
    )
    if asks_for_more and not re.search(r"\d", stdout):
        return False

    # Require some concrete content: a number, or a reasonably long answer.
    if re.search(r"\d", stdout):
        return True
    return len(stdout) >= 40


async def handle_code_mode(
    chat_id: str,
    user_message: str,
    think: bool = False,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Executes the Code generation and execution pipeline:
    1. Explicit Planning Step: Outputs 2-4 concrete steps and logs them.
    2. Code Generation (temp 0.15) & Extraction.
    3. Sandbox execution with hard iteration/retry limits.
    4. Size-capped sandbox stdout/stderr.
    5. Clean Final Answer Synthesis: Separate model call reporting verified numerical/code results without plan restatements.
    """
    from backend.config import TOOL_RETURN_MAX_CHARS
    from backend.structured_logger import log_agent_plan, log_stage_event, get_current_request_id

    req_id = get_current_request_id()
    logger.info(f"[CODE_MODE] chat_id={chat_id} think={think} temperature=0.15")
    
    save_message(chat_id, "user", user_message, mode="code")
    messages = await build_context_messages(chat_id, CODE_SYSTEM_PROMPT, user_message)

    # ── Phase 1: Explicit Plan Step ──
    code_plan_steps = [
        "1. Formulate executable Python 3 script matching requirements",
        "2. Execute script in isolated sandbox and verify execution exit code",
        "3. Synthesize verified final numerical / deliverable results"
    ]
    log_agent_plan(code_plan_steps, request_id=req_id)
    plan_banner = "**Execution Plan:**\n" + "\n".join([f"  {s}" for s in code_plan_steps]) + "\n\n---\n"
    yield {"token": plan_banner}
    yield {"token": "Generating executable code in isolated sandbox...\n\n"}
    
    # Config-driven code model resolution
    from backend.models_registry import models_registry
    code_model_def = models_registry.get_best_model_for_capability("code")
    code_model = code_model_def.model_id if code_model_def else None

    # Step 1: Generate initial code
    gen_tokens = []
    token_gen = await call_ollama(messages, stream=True, temperature=0.15, think=False, model=code_model)
    async for chunk in token_gen:
        chunk_type = chunk.get("type", "content")
        token_text = chunk.get("token", "")
        if chunk_type == "thinking":
            if think:
                yield {"thinking": token_text, "event": "step", "step_type": "thought", "content": token_text}
        else:
            gen_tokens.append(token_text)
            yield {"token": token_text, "event": "step", "step_type": "token", "content": token_text}
        
    model_output = filter_thinking("".join(gen_tokens))
    extracted_code = extract_python_code(model_output)
    
    # Retry once if no code block was returned
    if not extracted_code:
        yield {"token": "\n\n[Refining code formatting...]\n"}
        retry_prompt = messages + [
            {"role": "assistant", "content": model_output},
            {"role": "user", "content": "Return only the code block inside ```python ... ```."}
        ]
        retry_raw = await call_ollama(retry_prompt, stream=False, temperature=0.15, think=False, model=code_model)
        extracted_code = extract_python_code(str(retry_raw))
        if extracted_code:
            yield {"token": f"\n```python\n{extracted_code}\n```\n"}
            model_output = str(retry_raw)

    if not extracted_code:
        # If still no code, honest reporting
        save_message(chat_id, "assistant", model_output, mode="code")
        yield {
            "done": True,
            "generated_file": None,
            "run_output": "Error: Model did not produce an executable Python script.",
            "code": "",
            "status": "error"
        }
        return

    # Step 3: Sandbox execution with bounded self-correction retries on error.
    # The loop below is bounded by this value; the previously imported
    # AGENT_MAX_ITERATIONS / AGENT_MAX_TOOL_CALLS were never applied.
    max_retries = 2
    current_retry = 0
    sandbox_result = None
    
    yield {"token": "\n\n[Executing code in sandbox...]\n"}
    
    while current_retry <= max_retries:
        sandbox_result = execute_python_sandbox(extracted_code)
        
        if sandbox_result["success"] and not _run_produced_result(sandbox_result):
            # Exit 0 but nothing useful was computed (e.g. the script only asked
            # for input). Treat it as a failed attempt so the model retries.
            logger.warning(
                f"[CODE_MODE] Sandbox exited 0 but produced no usable result on attempt "
                f"{current_retry + 1}: stdout={sandbox_result['stdout'][:120]!r}"
            )
            if current_retry < max_retries:
                current_retry += 1
                yield {"token": f"\n\n[Script ran but printed no result. Retrying {current_retry}/{max_retries}...]\n"}
                fix_messages = messages + [
                    {"role": "assistant", "content": f"```python\n{extracted_code}\n```"},
                    {
                        "role": "user",
                        "content": (
                            "Your script exited successfully but did not produce an answer. It printed:\n"
                            f"{sandbox_result['stdout'][:500]}\n\n"
                            "There is NO interactive input and NO command-line arguments: never call input(), "
                            "never read stdin, and never use sys.argv/argparse. "
                            "Use the values given in the request, or sensible named example values if none were "
                            "provided, and PRINT the final computed numeric result. "
                            "Return only the corrected full script in a ```python ... ``` block."
                        ),
                    },
                ]
                fixed_raw = await call_ollama(fix_messages, stream=False, temperature=0.15, think=False, model=code_model)
                fixed_code = extract_python_code(str(fixed_raw))
                if fixed_code:
                    extracted_code = fixed_code
                    yield {"token": f"\n```python\n{extracted_code}\n```\n"}
            else:
                break
            continue

        if sandbox_result["success"]:
            logger.info(f"[CODE_MODE] Sandbox run SUCCEEDED on attempt {current_retry + 1}")
            break
        else:
            logger.warning(
                f"[CODE_MODE] Sandbox run FAILED on attempt {current_retry + 1} with exit_code={sandbox_result['exit_code']}"
            )
            if current_retry < max_retries:
                current_retry += 1
                yield {"token": f"\n\n[Execution error encountered. Attempting self-correction retry {current_retry}/{max_retries}...]\n"}
                
                error_diagnostic = f"Execution of your script failed with exit code {sandbox_result['exit_code']}.\n"
                if sandbox_result['exit_code'] == 124:
                    error_diagnostic += "CAUSE: Infinite loop or execution timed out (>20s). Ensure loop counter increments unconditionally at the end of the loop, and 2 is recognized as prime.\n"
                
                # Extract specific error type for targeted diagnosis
                stderr_text = sandbox_result['stderr']
                error_type_match = re.search(r'(\w+Error):', stderr_text)
                if error_type_match:
                    error_diagnostic += f"Error Type: {error_type_match.group(1)}\n"
                
                error_diagnostic += f"Stderr Output:\n{stderr_text}\n\nStdout Output:\n{sandbox_result['stdout']}\n\n"
                error_diagnostic += (
                    "The sandbox runs `python main.py` with NO command-line arguments and NO stdin. "
                    "Do not use input(), do not read stdin, and do not require sys.argv/argparse. "
                    "If the request omits required numbers, define clearly named example values, print them, "
                    "and print the final computed result.\n\n"
                    "Fix this error. Return only the corrected full script in a ```python ... ``` block."
                )
                
                fix_messages = messages + [
                    {"role": "assistant", "content": f"```python\n{extracted_code}\n```"},
                    {
                        "role": "user",
                        "content": error_diagnostic
                    }
                ]
                
                fixed_raw = await call_ollama(fix_messages, stream=False, temperature=0.15, think=False, model=code_model)
                fixed_code = extract_python_code(str(fixed_raw))
                if fixed_code:
                    extracted_code = fixed_code
                    yield {"token": f"\n```python\n{extracted_code}\n```\n"}
            else:
                break

    # Build final response text.
    #
    # A run only counts as verified when it exited 0 AND actually produced a
    # result. On the final attempt the loop above breaks while
    # sandbox_result["success"] is still True, so the old check labelled output
    # that the guard had just declared worthless as "Sandbox Output (Verified)"
    # and "Final Verified Findings".
    produced_result = bool(sandbox_result) and sandbox_result["success"] and _run_produced_result(sandbox_result)
    status_str = "success" if produced_result else "error"
    stdout_text = sandbox_result["stdout"] if sandbox_result else ""
    stderr_text = sandbox_result["stderr"] if sandbox_result else ""
    
    run_output_formatted = stdout_text.strip()
    if stderr_text.strip():
        if run_output_formatted:
            run_output_formatted += f"\n\n[Stderr / Errors]:\n{stderr_text.strip()}"
        else:
            run_output_formatted = f"[Stderr / Errors]:\n{stderr_text.strip()}"
            
    # ── Handle Output Size Capping ──
    from backend.agent_loop import cap_tool_result_size
    run_output_formatted, was_capped = cap_tool_result_size(run_output_formatted, max_chars=TOOL_RETURN_MAX_CHARS)
    if was_capped:
        yield {"token": "\n\n⚠️ *(Sandbox stdout capped to prevent context overflow)*\n"}

    # Stream sandbox output verbatim. A failed run is never labelled "verified".
    if status_str == "success":
        yield {"token": f"\n\n**Sandbox Output (Verified):**\n```\n{run_output_formatted}\n```\n"}
    else:
        yield {
            "token": (
                f"\n\n**Sandbox Output (run FAILED - not verified):**\n```\n{run_output_formatted}\n```\n"
            )
        }
    
    # ── Handle Generated Files ──
    generated_files = sandbox_result.get("generated_files", []) if sandbox_result else []
    generated_file_url = None
    if generated_files:
        import shutil
        chat_gen_dir = GENERATED_DIR / chat_id
        chat_gen_dir.mkdir(parents=True, exist_ok=True)
        
        file_links = []
        for gf in generated_files:
            try:
                src_path = gf["path"]
                import uuid as _uuid
                file_id = _uuid.uuid4().hex[:12]
                dest_path = chat_gen_dir / f"{file_id}_{gf['name']}"
                shutil.copy2(src_path, str(dest_path))
                save_file_record(file_id, chat_id, gf["name"], gf["extension"].lstrip("."), str(dest_path))
                download_url = f"/api/files/{file_id}"
                if not generated_file_url:
                    generated_file_url = download_url
                size_kb = round(gf["size_bytes"] / 1024, 1)
                file_links.append(f"📁 [{gf['name']}]({download_url}) ({size_kb} KB)")
            except Exception as e:
                logger.warning(f"[CODE_MODE] Failed to register generated file {gf['name']}: {e}")
        
        if file_links:
            files_msg = "\n\n**Generated Files:**\n" + "\n".join(file_links)
            yield {"token": files_msg}
            run_output_formatted += files_msg

    # ── Phase 3: Separate Final Answer Synthesis ──
    if status_str != "success":
        # The run did not produce a verified result, so there is nothing to
        # synthesise a "verified finding" from. Say what actually happened
        # instead of letting the model dress a failure up as a result.
        failure_note = (
            "**Execution did not complete successfully.**\n\n"
            f"- Exit code: {sandbox_result.get('exit_code') if sandbox_result else 'n/a'}\n"
            f"- Error output is shown above.\n\n"
            "The script needs to run unattended. Re-send the request with the "
            "specific values you want used (for example the shape/geometry and the "
            "dimensions or volume), or adjust the code in the editor and run it again."
        )
        log_stage_event(
            stage="FINAL_ANSWER_SYNTHESIS",
            status="SKIPPED",
            request_id=req_id,
            output_summary="run failed - no verified finding synthesised",
        )
        save_message(
            chat_id,
            "assistant",
            f"```python\n{extracted_code}\n```\n\n**Sandbox Output (run FAILED - not verified):**\n"
            f"```\n{run_output_formatted}\n```\n\n{failure_note}",
            mode="code",
        )
        yield {"token": f"\n\n---\n{failure_note}\n"}
        yield {
            "done": True,
            "generated_file": generated_file_url,
            "run_output": run_output_formatted,
            "code": extracted_code,
            "status": "error",
        }
        return

    yield {"token": "\n\n---\n### 🎯 Final Verified Findings\n"}
    final_messages = [
        {
            "role": "system",
            "content": (
                "You are the Technical Verification Officer. Deliver the final answer to the user based EXCLUSIVELY "
                "on the verified sandbox execution output. DIRECTIVES:\n"
                "1. State ONLY what was computed or printed in the sandbox.\n"
                "2. Do NOT restate the execution plan, code blocks, or internal loops.\n"
                "3. Do NOT add disclaimers or padding. Keep it concise, authoritative, and direct."
            )
        },
        {
            "role": "user",
            "content": f"USER QUERY: {user_message}\n\nVERIFIED SANDBOX OUTPUT:\n{run_output_formatted}\n\nDeliver the final verified finding."
        }
    ]
    log_stage_event(stage="FINAL_ANSWER_SYNTHESIS", status="STARTED", request_id=req_id)
    final_tokens = []
    final_gen = await call_ollama(final_messages, stream=True, temperature=0.15, think=False, model=code_model)
    async for chunk in final_gen:
        token = chunk.get("token", "")
        if token:
            final_tokens.append(token)
            yield {"token": token, "event": "step", "step_type": "token", "content": token}
    
    final_finding = "".join(final_tokens).strip()
    log_stage_event(stage="FINAL_ANSWER_SYNTHESIS", status="SUCCESS", request_id=req_id, output_summary=f"finding_chars={len(final_finding)}")

    full_stored_content = f"```python\n{extracted_code}\n```\n\n**Sandbox Output:**\n```\n{run_output_formatted}\n```\n\n**Final Verified Finding:**\n{final_finding}"
    save_message(chat_id, "assistant", full_stored_content, mode="code")
    
    yield {
        "done": True,
        "generated_file": generated_file_url,
        "run_output": run_output_formatted,
        "code": extracted_code,
        "status": status_str,
    }
