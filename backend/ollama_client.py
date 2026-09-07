"""
Ollama Client for Air-Gapped Local Inference.
Strictly offline: connects only to local Ollama instance on http://localhost:11434.
Supports streaming token chunks with distinct thinking vs content categorization.
"""

import re
import json
import httpx
from typing import List, Dict, Any, Optional, AsyncGenerator, Union

from backend.config import (
    MODEL_NAME,
    VISION_MODEL_NAME,
    OLLAMA_HOST,
    NUM_CTX,
    OLLAMA_TIMEOUT,
    DEFAULT_TOP_P,
    DEFAULT_TOP_K,
    DEFAULT_REPEAT_PENALTY,
    logger,
)


class OllamaConnectionError(Exception):
    """Raised when Ollama is unreachable or model is missing."""
    pass


class ModelNotFoundError(Exception):
    """Raised when the specified MODEL_NAME is not present on Ollama server."""
    pass


def filter_thinking(text: str) -> str:
    """
    Strips internal thinking/reasoning tags and prefixes from the final response.
    Handles tags split across token boundaries (e.g. ["<thi","nk>..."]
    Ensures zero thinking leak in the stored database records and clean final output.
    """
    if not text:
        return ""
    cleaned = text

    # Multi-pass: keep stripping until no more <think> tags found
    # (handles splits across token boundaries like "<thi" + "nk>...")
    for _ in range(5):
        prev = cleaned
        # Strip complete <think>...</think> XML blocks
        cleaned = re.sub(r"<think>[\s\S]*?</think>", "", cleaned, flags=re.IGNORECASE)
        # Strip partial/fragmented think tags that may span tokens
        # e.g. "<thi" at end, "nk>" at start, or partial "</thi"
        cleaned = re.sub(r"<think[\s\S]{0,50}?->", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"</?think[\s\S]{0,20}?>", "", cleaned, flags=re.IGNORECASE)
        # Also handle split closing tags like "</thi" + "nk>"
        cleaned = re.sub(r"</thi$", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"^nk>", "", cleaned, flags=re.IGNORECASE)
        if cleaned == prev:
            break

    # Strip "Thinking Process:\n\n..." prefixes if present
    if "Thinking Process:" in cleaned:
        match = re.search(
            r"Thinking Process:[\s\S]*?\n\n(?=[A-Z0-9\*\#\-\"\'\`]|Got |Sure |Hello |The |In |According |For |Note |Based |Operational |Maximum |1\.)",
            cleaned
        )
        if match:
            cleaned = cleaned[match.end():]
        else:
            lines = cleaned.split("\n")
            non_thinking = [
                l for l in lines
                if not (l.strip().startswith(("Thinking Process:", "*", "1.", "2.", "3.", "4.", "5.", "6.")) or "Analyze" in l or "Constraint" in l)
            ]
            if non_thinking and "".join(non_thinking).strip():
                cleaned = "\n".join(non_thinking)

    # Post-processing: detect model analysis patterns leaked into content
    # Pattern: numbered or asterisk lines with analysis headers
    thinking_header = re.match(
        r"^\s*[\*\d\.]+\s*\*{0,2}\s*(Analyze|Identify|Evaluate|Consider|Self-Correction|Determine|Check|Review|Assess)",
        cleaned, re.IGNORECASE
    )
    if thinking_header:
        # Find the first line that doesn't look like internal analysis
        lines = cleaned.split("\n")
        first_real = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue
            is_thinking_line = (
                re.match(r"^\s*\d+\.\s*\*{0,2}\s*(Analyze|Identify|Evaluate|Consider|Self-Correction|Determine|Check|Review|Assess)", stripped, re.IGNORECASE) is not None
                or re.match(r"^\s*\d+\.\s*\*{0,2}(User input|Context|System prompt|Task|The user|I need|REVEAL|MANDATORY|Reply|Since|The task|Constraints|Response|Final|Action)", stripped, re.IGNORECASE) is not None
                or stripped.startswith("*Self-Correction")
                or stripped.startswith("- Self-Correction")
                or re.match(r"^[\*\-]\s+(User input|Context|System prompt|Task|The user|I need|REVEAL|Since|Reply|The task|Constraints)", stripped, re.IGNORECASE) is not None
            )
            if is_thinking_line:
                first_real = i + 1
            elif first_real > 0:
                break
            else:
                break
        if first_real > 0 and first_real < len(lines):
            cleaned = "\n".join(lines[first_real:]).strip()

    # Also catch standalone "Thinking Process:" prefix without full block
    cleaned = re.sub(r"^Thinking Process:\s*\n*", "", cleaned, flags=re.IGNORECASE).strip()

    return cleaned.strip()


async def check_ollama_health() -> Dict[str, Any]:
    """
    Startup health check: GET /api/tags must contain MODEL_NAME.
    """
    url = f"{OLLAMA_HOST}/api/tags"
    exact_fix = f"run: ollama serve && ollama pull {MODEL_NAME}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            if response.status_code != 200:
                raise OllamaConnectionError(
                    f"Ollama returned HTTP {response.status_code}. Fix: {exact_fix}"
                )
            data = response.json()
            models = [m.get("name", "") for m in data.get("models", [])]
            
            # Check for exact tag match or base model match
            model_found = any(
                MODEL_NAME == m or MODEL_NAME in m or m.startswith(MODEL_NAME)
                for m in models
            )
            if not model_found:
                logger.error(
                    f"CRITICAL ERROR: Required model '{MODEL_NAME}' is not loaded in Ollama. "
                    f"Available models: {models}. Fix: {exact_fix}"
                )
                raise ModelNotFoundError(
                    f"Model '{MODEL_NAME}' is missing from Ollama. Available: {models}. Fix: {exact_fix}"
                )
                
            logger.info(f"Ollama health check PASSED. Active text model: {MODEL_NAME}, vision model: {VISION_MODEL_NAME}")
            return {
                "status": "ok",
                "model": MODEL_NAME,
                "vision_model": VISION_MODEL_NAME,
                "available_models": models,
                "ollama_host": OLLAMA_HOST,
            }
            
    except httpx.RequestError as exc:
        msg = f"CRITICAL ERROR: Cannot connect to Ollama at {OLLAMA_HOST} ({exc}). Fix: {exact_fix}"
        logger.critical(msg)
        raise OllamaConnectionError(msg) from exc


async def call_ollama(
    messages: List[Dict[str, Any]],
    stream: bool = True,
    temperature: float = 0.5,
    json_mode: bool = False,
    max_tokens: Optional[int] = None,
    think: Optional[bool] = None,
    images: Optional[List[str]] = None,
    model: Optional[str] = None,
) -> Union[AsyncGenerator[Dict[str, str], None], str]:
    """
    Single inference gateway for all modes.
    Supports multimodal inputs with base64 image strings.
    Yields Dict[str, str] with keys:
      - "type": "thinking" | "content"
      - "token": str
    """
    target_model = model or (VISION_MODEL_NAME if images else MODEL_NAME)
    url = f"{OLLAMA_HOST}/api/chat"
    
    eff_num_predict = max_tokens if (max_tokens is not None and max_tokens > 0) else 2048
    options: Dict[str, Any] = {
        "temperature": float(temperature),
        "top_p": DEFAULT_TOP_P,
        "top_k": DEFAULT_TOP_K,
        "repeat_penalty": DEFAULT_REPEAT_PENALTY,
        "num_ctx": NUM_CTX,
        "num_predict": eff_num_predict,
    }
    
    # Inject images into the last user message if provided
    formatted_messages = list(messages)
    if images and formatted_messages:
        for idx in range(len(formatted_messages) - 1, -1, -1):
            if formatted_messages[idx].get("role") == "user":
                msg_copy = dict(formatted_messages[idx])
                msg_copy["images"] = images
                formatted_messages[idx] = msg_copy
                break

    payload: Dict[str, Any] = {
        "model": target_model,
        "messages": formatted_messages,
        "stream": stream,
        "options": options,
    }
    
    if think is not None:
        payload["think"] = think
    
    if json_mode:
        payload["format"] = "json"

    logger.info(
        f"Ollama inference request -> model={target_model}, temp={temperature}, "
        f"num_predict={eff_num_predict}, think={think}, "
        f"json_mode={json_mode}, stream={stream}, messages_count={len(messages)}"
    )

    if stream:
        return _stream_ollama(url, payload)
    else:
        return await _non_stream_ollama(url, payload)


async def _stream_ollama(url: str, payload: Dict[str, Any]) -> AsyncGenerator[Dict[str, str], None]:
    """
    Streams structured chunks:
    - {"type": "thinking", "token": "..."}
    - {"type": "content", "token": "..."}
    """
    exact_fix = f"run: ollama serve && ollama pull {MODEL_NAME}"
    try:
        timeout = httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("POST", url, json=payload) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    error_msg = f"Ollama error {response.status_code}: {error_text.decode('utf-8', errors='ignore')}"
                    logger.error(error_msg)
                    yield {"type": "content", "token": f"Error from Ollama backend: {error_msg}. ({exact_fix})"}
                    return

                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        msg = chunk.get("message", {})
                        thinking = msg.get("thinking", "")
                        content = msg.get("content", "")
                        
                        if thinking:
                            yield {"type": "thinking", "token": thinking}
                        if content:
                            yield {"type": "content", "token": content}
                        if chunk.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue

    except (httpx.ConnectError, httpx.NetworkError) as e:
        err = f"Failed to connect to Ollama at {OLLAMA_HOST}. Ensure Ollama is running ({exact_fix}). Error: {e}"
        logger.error(err)
        yield {"type": "content", "token": f"\n[Ollama Connection Error: {err}]"}
    except httpx.TimeoutException as e:
        err = f"Ollama inference timed out after {OLLAMA_TIMEOUT}s. Error: {e}"
        logger.error(err)
        yield {"type": "content", "token": f"\n[Ollama Timeout Error: {err}]"}
    except Exception as e:
        err = f"Unexpected error communicating with Ollama: {e}"
        logger.error(err)
        yield {"type": "content", "token": f"\n[Ollama Error: {err}]"}


async def _non_stream_ollama(url: str, payload: Dict[str, Any]) -> str:
    """Non-streaming request to Ollama returning full string response."""
    exact_fix = f"run: ollama serve && ollama pull {MODEL_NAME}"
    try:
        timeout = httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, json=payload)
            if response.status_code != 200:
                raise OllamaConnectionError(
                    f"Ollama returned HTTP {response.status_code}: {response.text}. Fix: {exact_fix}"
                )
            data = response.json()
            msg = data.get("message", {})
            raw_text = msg.get("content") or msg.get("thinking") or ""
            return filter_thinking(raw_text)
    except httpx.RequestError as e:
        raise OllamaConnectionError(f"Cannot reach Ollama at {OLLAMA_HOST}: {e}. Fix: {exact_fix}") from e


async def unload_model(model_name: str) -> bool:
    """
    Explicitly unloads a model from Ollama VRAM by setting keep_alive=0.
    This frees GPU memory before loading a different model.
    Returns True if successful, False otherwise.
    """
    url = f"{OLLAMA_HOST}/api/generate"
    payload = {
        "model": model_name,
        "prompt": "",
        "keep_alive": 0,
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                logger.info(f"[MODEL_SWAP] Successfully unloaded model '{model_name}' from VRAM")
                return True
            else:
                logger.warning(f"[MODEL_SWAP] Unload request for '{model_name}' returned status {response.status_code}")
                return False
    except Exception as e:
        logger.warning(f"[MODEL_SWAP] Failed to unload model '{model_name}': {e}")
        return False


async def preload_model(model_name: str, keep_alive: int = 300) -> bool:
    """
    Preloads a model into Ollama VRAM with a specified keep_alive duration (seconds).
    This ensures the model is warm and ready for inference.
    Returns True if successful, False otherwise.
    """
    url = f"{OLLAMA_HOST}/api/generate"
    payload = {
        "model": model_name,
        "prompt": "",
        "keep_alive": keep_alive,
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                logger.info(f"[MODEL_SWAP] Successfully preloaded model '{model_name}' (keep_alive={keep_alive}s)")
                return True
            else:
                logger.warning(f"[MODEL_SWAP] Preload request for '{model_name}' returned status {response.status_code}")
                return False
    except Exception as e:
        logger.warning(f"[MODEL_SWAP] Failed to preload model '{model_name}': {e}")
        return False


async def swap_to_model(
    target_model: str,
    unload_model_name: str,
    chat_id: Optional[str] = None,
    context_to_transfer: Optional[Any] = None
) -> bool:
    """
    Performs a full model swap:
    1. Saves context_to_transfer in temporary backend memory (context_handoff).
    2. Unloads current model from VRAM (keep_alive=0).
    3. Preloads target model into VRAM.
    Used for seamless vision↔text model transitions without losing working memory.
    """
    if chat_id and context_to_transfer is not None:
        try:
            from backend.context_handoff import context_handoff
            context_handoff.save_handoff_context(
                chat_id=chat_id,
                from_model=unload_model_name,
                to_model=target_model,
                context_payload=context_to_transfer
            )
        except Exception as err:
            logger.warning(f"[MODEL_SWAP] Could not store handoff context: {err}")

    logger.info(f"[MODEL_SWAP] Swapping: unload '{unload_model_name}' -> load '{target_model}'")
    await unload_model(unload_model_name)
    return await preload_model(target_model)

