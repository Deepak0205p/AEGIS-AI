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
5. Return ONLY the executable Python script in ```python ... ``` block without conversational filler."""


def extract_python_code(response_text: str) -> Optional[str]:
    """Extracts code from ```python ... ``` or ``` ... ``` block."""
    # Match ```python <code> ```
    pattern = re.compile(r"```(?:python)?\s*([\s\S]*?)```", re.IGNORECASE)
    matches = pattern.findall(response_text)
    if matches:
        # Return the longest code block
        return max(matches, key=len).strip()
    return None


async def handle_code_mode(
    chat_id: str,
    user_message: str,
    think: bool = False,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Executes the Code generation and execution pipeline:
    1. Generate script (temp 0.15)
    2. Extract code (retry once if missing)
    3. Run in sandbox
    4. Auto-fix errors with up to 2 retries
    5. Stream tokens & emit final verbatim stdout.
    """
    logger.info(f"[CODE_MODE] chat_id={chat_id} think={think} temperature=0.15")
    
    save_message(chat_id, "user", user_message, mode="code")
    messages = await build_context_messages(chat_id, CODE_SYSTEM_PROMPT, user_message)
    
    yield {"token": "Generating executable code in isolated sandbox...\n\n"}
    
    # Step 1: Generate initial code
    gen_tokens = []
    token_gen = await call_ollama(messages, stream=True, temperature=0.15, think=False)
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
        retry_raw = await call_ollama(retry_prompt, stream=False, temperature=0.15, think=False)
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

    # Step 3: Sandbox execution with up to 2 retries on error
    max_retries = 2
    current_retry = 0
    sandbox_result = None
    
    yield {"token": "\n\n[Executing code in sandbox...]\n"}
    
    while current_retry <= max_retries:
        sandbox_result = execute_python_sandbox(extracted_code)
        
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
                
                error_diagnostic += f"Stderr Output:\n{stderr_text}\n\nStdout Output:\n{sandbox_result['stdout']}\n\nFix this error. Return only the corrected full script in a ```python ... ``` block."
                
                fix_messages = messages + [
                    {"role": "assistant", "content": f"```python\n{extracted_code}\n```"},
                    {
                        "role": "user",
                        "content": error_diagnostic
                    }
                ]
                
                fixed_raw = await call_ollama(fix_messages, stream=False, temperature=0.15, think=False)
                fixed_code = extract_python_code(str(fixed_raw))
                if fixed_code:
                    extracted_code = fixed_code
                    yield {"token": f"\n```python\n{extracted_code}\n```\n"}
            else:
                break

    # Build final response text
    status_str = "success" if sandbox_result and sandbox_result["success"] else "error"
    stdout_text = sandbox_result["stdout"] if sandbox_result else ""
    stderr_text = sandbox_result["stderr"] if sandbox_result else ""
    
    run_output_formatted = stdout_text.strip()
    if stderr_text.strip():
        if run_output_formatted:
            run_output_formatted += f"\n\n[Stderr / Errors]:\n{stderr_text.strip()}"
        else:
            run_output_formatted = f"[Stderr / Errors]:\n{stderr_text.strip()}"
            
    if not run_output_formatted:
        run_output_formatted = "(Script finished with no stdout output)"

    # Stream sandbox output verbatim
    yield {"token": f"\n\n**Sandbox Output (Verified):**\n```\n{run_output_formatted}\n```\n"}
    
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
    
    full_stored_content = f"```python\n{extracted_code}\n```\n\n**Sandbox Output:**\n```\n{run_output_formatted}\n```"
    save_message(chat_id, "assistant", full_stored_content, mode="code")
    
    yield {
        "done": True,
        "generated_file": generated_file_url,
        "run_output": run_output_formatted,
        "code": extracted_code,
        "status": status_str,
    }
