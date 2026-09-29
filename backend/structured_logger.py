"""
Structured Pipeline Logger for Air-Gapped Local AI Backend.
Enforces observable stages, timing, tool tracking, prompt logging, and rotating file persistence.
Zero behavioral changes.
"""

import os
import sys
import time
import json
import uuid
import contextvars
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.config import LOGS_DIR

# Context variable to hold the active request_id across async coroutines
current_request_id: contextvars.ContextVar[str] = contextvars.ContextVar("current_request_id", default="")

def get_current_request_id() -> str:
    """Returns the current request ID or generates a fallback if outside request context."""
    req_id = current_request_id.get()
    return req_id if req_id else "req_system"

def set_current_request_id(req_id: Optional[str] = None) -> str:
    """Sets or generates a unique request_id in contextvars."""
    clean_id = req_id if req_id else f"req_{uuid.uuid4().hex[:12]}"
    current_request_id.set(clean_id)
    return clean_id


# Setup dedicated structured logger
STRUCTURED_LOG_PATH = LOGS_DIR / "pipeline_structured.log"
pipeline_logger = logging.getLogger("pipeline_structured")
pipeline_logger.setLevel(logging.INFO)

# Avoid duplicate handlers on server reloads
if not pipeline_logger.handlers:
    # Formatter: JSON lines or clean grep-friendly standard format
    log_format = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [REQ:%(req_id)s] [%(stage)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Rotating file handler: 20MB per file, keep up to 10 backups
    rot_handler = RotatingFileHandler(
        STRUCTURED_LOG_PATH,
        maxBytes=20 * 1024 * 1024,
        backupCount=10,
        encoding="utf-8"
    )
    rot_handler.setLevel(logging.INFO)

    # Custom Filter to inject req_id and stage into every record
    class PipelineLogFilter(logging.Filter):
        def filter(self, record):
            if not hasattr(record, "req_id") or not record.req_id:
                record.req_id = get_current_request_id()
            if not hasattr(record, "stage"):
                record.stage = getattr(record, "stage", "PIPELINE")
            return True

    rot_handler.addFilter(PipelineLogFilter())
    rot_handler.setFormatter(log_format)
    pipeline_logger.addHandler(rot_handler)

    # Also forward to console StreamHandler with safe utf-8/surrogateescape or errors='replace'
    c_handler = logging.StreamHandler(sys.stdout)
    c_handler.setLevel(logging.INFO)
    c_handler.addFilter(PipelineLogFilter())
    c_handler.setFormatter(log_format)
    # Ensure stdout writes don't crash on Windows non-UTF8 terminals
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(errors="replace")
        except Exception:
            pass
    pipeline_logger.addHandler(c_handler)


def log_stage_event(
    stage: str,
    status: str,  # 'STARTED' | 'SUCCESS' | 'FAILED' | 'DECISION'
    request_id: Optional[str] = None,
    input_summary: Optional[Any] = None,
    output_summary: Optional[Any] = None,
    elapsed_ms: Optional[float] = None,
    error: Optional[Any] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    """
    Emits a structured log line for a specific stage with elapsed time and status.
    Format is easily greppable: stage name, request_id, input size/summary, elapsed time, success/failure.
    """
    req_id = request_id or get_current_request_id()
    meta = metadata or {}

    details = []
    if status:
        details.append(f"status={status}")
    if elapsed_ms is not None:
        details.append(f"elapsed={elapsed_ms:.2f}ms")
    if input_summary is not None:
        inp_str = str(input_summary)
        if len(inp_str) > 200:
            inp_str = inp_str[:200] + f"... (len={len(inp_str)})"
        details.append(f"input={inp_str!r}")
    if output_summary is not None:
        out_str = str(output_summary)
        if len(out_str) > 200:
            out_str = out_str[:200] + f"... (len={len(out_str)})"
        details.append(f"output={out_str!r}")
    for k, v in meta.items():
        details.append(f"{k}={v!r}")
    if error:
        details.append(f"error={str(error)!r}")

    msg = " | ".join(details)
    extra = {"req_id": req_id, "stage": stage.upper()}
    if status == "FAILED" or error:
        pipeline_logger.error(msg, extra=extra)
    else:
        pipeline_logger.info(msg, extra=extra)


class StageTimer:
    """Context manager to measure and log stage execution time and success/failure."""

    def __init__(
        self,
        stage: str,
        input_summary: Optional[Any] = None,
        request_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.stage = stage
        self.input_summary = input_summary
        self.request_id = request_id or get_current_request_id()
        self.metadata = metadata or {}
        self.start_time = 0.0

    def __enter__(self):
        self.start_time = time.perf_counter()
        log_stage_event(
            stage=self.stage,
            status="STARTED",
            request_id=self.request_id,
            input_summary=self.input_summary,
            metadata=self.metadata,
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed_ms = (time.perf_counter() - self.start_time) * 1000.0
        if exc_type is not None:
            log_stage_event(
                stage=self.stage,
                status="FAILED",
                request_id=self.request_id,
                input_summary=self.input_summary,
                elapsed_ms=elapsed_ms,
                error=exc_val,
                metadata=self.metadata,
            )
        else:
            log_stage_event(
                stage=self.stage,
                status="SUCCESS",
                request_id=self.request_id,
                input_summary=self.input_summary,
                elapsed_ms=elapsed_ms,
                metadata=self.metadata,
            )
        return False  # Don't swallow exceptions


def log_model_selection(
    selected_model: str,
    routing_decision: str,
    reason: str,
    request_id: Optional[str] = None,
    confidence: Optional[float] = None,
):
    """
    Log which Ollama model was selected and why (the routing decision, not just the choice).
    """
    req_id = request_id or get_current_request_id()
    log_stage_event(
        stage="ROUTER_MODEL_SELECTION",
        status="DECISION",
        request_id=req_id,
        metadata={
            "selected_model": selected_model,
            "routing_decision": routing_decision,
            "reason": reason,
            "confidence": confidence,
        },
    )


def log_tool_call(
    tool_name: str,
    arguments: Any,
    return_value: Any,
    elapsed_ms: Optional[float] = None,
    success: bool = True,
    error: Optional[Any] = None,
    request_id: Optional[str] = None,
):
    """
    Log every tool call: tool name, arguments, return value size, success/failure.
    """
    req_id = request_id or get_current_request_id()
    
    # Calculate return value size
    ret_str = str(return_value) if return_value is not None else ""
    ret_size = len(ret_str)
    
    arg_str = str(arguments)
    if len(arg_str) > 300:
        arg_str = arg_str[:300] + f"... (len={len(arg_str)})"

    log_stage_event(
        stage="TOOL_EXECUTION",
        status="SUCCESS" if success else "FAILED",
        request_id=req_id,
        input_summary=f"{tool_name}({arg_str})",
        output_summary=f"return_size={ret_size} chars",
        elapsed_ms=elapsed_ms,
        error=error,
        metadata={
            "tool_name": tool_name,
            "success": success,
            "return_size_bytes": ret_size,
        },
    )


def log_agent_plan(plan_steps: List[str], request_id: Optional[str] = None):
    """
    Log the explicit initial numbered plan (2-6 steps) before tool execution begins.
    """
    req_id = request_id or get_current_request_id()
    plan_desc = "; ".join([f"Step {i+1}: {step}" for i, step in enumerate(plan_steps)])
    log_stage_event(
        stage="AGENT_PLAN",
        status="DECISION",
        request_id=req_id,
        input_summary=f"plan_step_count={len(plan_steps)}",
        output_summary=f"plan: {plan_desc}",
        metadata={"step_count": len(plan_steps), "steps": plan_steps}
    )
    for i, step in enumerate(plan_steps, 1):
        pipeline_logger.info(
            f"PLAN_STEP #{i}: {step}",
            extra={"req_id": req_id, "stage": "AGENT_PLAN_STEP"}
        )


def log_agent_limit_hit(limit_type: str, current_value: int, limit_max: int, request_id: Optional[str] = None):
    """
    Log a loud failure when hard max-iteration or max-tool-call limit is hit.
    """
    req_id = request_id or get_current_request_id()
    msg = f"HARD LIMIT REACHED: {limit_type} ({current_value} >= {limit_max}). Terminating agent loop immediately."
    pipeline_logger.error(msg, extra={"req_id": req_id, "stage": "AGENT_LIMIT_HIT"})
    log_stage_event(
        stage="AGENT_LIMIT_HIT",
        status="FAILED",
        request_id=req_id,
        input_summary=f"limit_type={limit_type}, max={limit_max}",
        output_summary=f"reached={current_value}",
        error=RuntimeError(msg),
        metadata={"limit_type": limit_type, "current_value": current_value, "limit_max": limit_max}
    )


def log_post_generation_audit(
    task_type: str,
    passed: bool,
    stripped_phrases: List[str],
    word_count: int,
    max_words: int,
    regenerated: bool = False,
    request_id: Optional[str] = None,
):
    """
    Log post-generation compliance checks: generic filler detection, word count enforcement, and stripping/regeneration.
    """
    req_id = request_id or get_current_request_id()
    log_stage_event(
        stage="POST_GEN_AUDIT",
        status="PASSED" if passed else "FLAGGED_AND_CLEANED",
        request_id=req_id,
        input_summary=f"task_type={task_type} word_count={word_count} max_words={max_words}",
        output_summary=f"passed={passed} stripped_count={len(stripped_phrases)} regenerated={regenerated}",
        metadata={
            "task_type": task_type,
            "passed": passed,
            "flagged_phrases": stripped_phrases,
            "word_count": word_count,
            "max_words": max_words,
            "regenerated": regenerated,
        },
    )


def log_image_preprocessing(
    raw_dim: Tuple[int, int],
    processed_dim: Tuple[int, int],
    skew_angle_deg: float,
    contrast_ratio: float,
    upscaled: bool,
    deskewed: bool,
    denoised: bool,
    quality_grade: str,
    request_id: Optional[str] = None,
):
    """
    Log image quality check (resolution, skew, contrast) and preprocessing pass (deskew, denoise, upscale).
    """
    req_id = request_id or get_current_request_id()
    log_stage_event(
        stage="IMAGE_PREPROCESSING",
        status="SUCCESS",
        request_id=req_id,
        input_summary=f"raw_dim={raw_dim} skew={skew_angle_deg:.2f}° contrast={contrast_ratio:.2f}",
        output_summary=f"processed_dim={processed_dim} grade={quality_grade} upscaled={upscaled} deskewed={deskewed} denoised={denoised}",
        metadata={
            "raw_dim": raw_dim,
            "processed_dim": processed_dim,
            "skew_angle_deg": skew_angle_deg,
            "contrast_ratio": contrast_ratio,
            "quality_grade": quality_grade,
            "upscaled": upscaled,
            "deskewed": deskewed,
            "denoised": denoised,
        },
    )


def log_ocr_region_confidence(
    regions: List[Dict[str, Any]],
    uncertain_count: int,
    mean_confidence: float,
    request_id: Optional[str] = None,
):
    """
    Log OCR confidence scores per region/line and report flagged uncertain regions.
    """
    req_id = request_id or get_current_request_id()
    log_stage_event(
        stage="OCR_CONFIDENCE_AUDIT",
        status="UNCERTAIN_REGIONS_FLAGGED" if uncertain_count > 0 else "HIGH_CONFIDENCE",
        request_id=req_id,
        input_summary=f"total_regions={len(regions)} mean_confidence={mean_confidence:.2f}",
        output_summary=f"uncertain_count={uncertain_count}",
        metadata={
            "total_regions": len(regions),
            "uncertain_count": uncertain_count,
            "mean_confidence": mean_confidence,
            "regions": regions[:10],
        },
    )


def log_retrieved_chunks(
    query: str,
    chunks: List[Dict[str, Any]],
    min_score_threshold: float,
    dropped_count: int = 0,
    request_id: Optional[str] = None,
):
    """
    Log raw chunks retrieved for a query alongside their similarity scores and text snippets
    before they are injected into the prompt.
    """
    req_id = request_id or get_current_request_id()
    chunk_summaries = []
    for c in chunks:
        cid = c.get("doc_id", "unknown")
        title = c.get("title", "")
        # `similarity_score` is only present when real embeddings exist; fall back
        # to the lexical relevance so the log never prints a fabricated number.
        sim = c.get("similarity_score")
        if isinstance(sim, (int, float)):
            score_str = f"cosine={sim:.4f}"
        else:
            rel = c.get("relevance")
            score_str = f"bm25={c.get('bm25_score', 0.0):.4f} relevance={rel:.4f}" if isinstance(rel, (int, float)) else "score=n/a"
        chunk_summaries.append(f"[{cid} | {score_str} | {title}]")

    log_stage_event(
        stage="RETRIEVER_CHUNKS",
        status="SUCCESS" if chunks else "NO_MATCH",
        request_id=req_id,
        input_summary=f"query={query!r} threshold={min_score_threshold}",
        output_summary=f"passed={len(chunks)}, dropped_below_threshold={dropped_count}",
        metadata={
            "retrieved_count": len(chunks),
            "dropped_count": dropped_count,
            "threshold": min_score_threshold,
            "chunks": chunk_summaries,
        },
    )

    # Detailed chunk-by-chunk logging
    for i, c in enumerate(chunks, 1):
        content_preview = c.get("content", "").replace("\n", " ").strip()
        if len(content_preview) > 160:
            content_preview = content_preview[:160] + "..."
        pipeline_logger.info(
            f"CHUNK #{i}: doc_id={c.get('doc_id')} score={c.get('similarity_score')} title={c.get('title')!r} text={content_preview!r}",
            extra={"req_id": req_id, "stage": "RETRIEVER_CHUNK_DETAIL"},
        )


def log_raw_model_prompt(
    model: str,
    messages: List[Dict[str, Any]],
    request_id: Optional[str] = None,
    extra_options: Optional[Dict[str, Any]] = None,
):
    """
    Log the final prompt actually sent to the model (system + retrieved context + user turn),
    token/char count included, right before the API call — not a reconstructed approximation.
    """
    req_id = request_id or get_current_request_id()

    # Reconstruct the exact structured text or serialize the message payload
    full_prompt_text = ""
    for msg in messages:
        role = msg.get("role", "unknown").upper()
        content = msg.get("content", "")
        full_prompt_text += f"\n--- [{role}] ---\n{content}\n"

    char_count = len(full_prompt_text)
    # Estimate token count (~4 chars per token)
    est_token_count = max(1, char_count // 4)
    msg_count = len(messages)

    # First log a high-level summary line
    log_stage_event(
        stage="MODEL_PROMPT_DISPATCH",
        status="DISPATCHING",
        request_id=req_id,
        metadata={
            "target_model": model,
            "message_turns": msg_count,
            "char_count": char_count,
            "estimated_tokens": est_token_count,
        }
    )

    # Second log the exact verbatim prompt payload
    preview_or_full = full_prompt_text.strip()
    pipeline_logger.info(
        f"VERBATIM PROMPT SENT TO MODEL '{model}' (chars={char_count}, est_tokens={est_token_count}):\n{preview_or_full}",
        extra={"req_id": req_id, "stage": "RAW_PROMPT"}
    )
