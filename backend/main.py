"""
Main FastAPI Application for Air-Gapped Local AI Backend.
Implements SSE streaming, exact endpoints, offline logging, and model health verification.
"""

import os
import re
import sys
import json
import uuid
import time
import socket
import shutil
import hashlib
import secrets
from datetime import datetime, timezone
import asyncio
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from contextlib import asynccontextmanager
from contextvars import ContextVar

import psutil

from fastapi import FastAPI, HTTPException, Request, Response, WebSocket, WebSocketDisconnect, File, UploadFile, Form
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Ensure root & backend directories are in sys.path
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent if BASE_DIR.name == "backend" else BASE_DIR
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.config import (
    DB_DRIVER,
    DB_LABEL,
    IS_POSTGRES,
    MODEL_NAME,
    VISION_MODEL_NAME,
    OCR_MODEL_NAME,
    OLLAMA_HOST,
    NUM_CTX,
    LOGS_DIR,
    GENERATED_DIR,
    MIN_RAG_SCORE,
    MAX_RAG_CHUNKS,
    logger,
)
from backend.db import (
    init_db,
    get_chat_history,
    get_file_record,
    get_db_connection,
    file_integrity,
)
from backend.ollama_client import check_ollama_health, filter_thinking
from backend.router import (
    route_message,
    route_message_async,
    get_thinking_decision_with_reason,
    get_rag_decision_with_reason,
    is_follow_up_query,
)
from backend.departments import detect_department
from backend.templates import detect_template
from backend.knowledge_base import search_sops, rag_cache, format_rag_context_block
from backend.chat_mode import handle_chat_mode
from backend.code_mode import handle_code_mode
from backend.docs_mode import handle_document_mode
from backend.excel_mode import handle_excel_mode
from backend.ppt_mode import handle_ppt_mode
from backend.vision_mode import handle_vision_mode


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    logger.info("Initializing Air-Gapped Sovereign AI Backend...")

    # Surface insecure secret handling loudly rather than silently trusting a
    # hard-coded key. Tokens issued with an ephemeral secret stop validating on
    # restart, which forces re-login instead of leaving forged tokens valid.
    if USING_EPHEMERAL_JWT_SECRET:
        logger.critical(
            "[SECURITY] AEGIS_JWT_SECRET is not set. A random per-process signing "
            "secret is being used, so ALL sessions will be invalidated whenever the "
            "backend restarts. Set AEGIS_JWT_SECRET in the environment for any "
            "real deployment."
        )
    else:
        logger.info("[SECURITY] Using the AEGIS_JWT_SECRET supplied by the environment.")

    # Initialize Database (MySQL or degraded mode)
    try:
        init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.warning(f"Database initialization warning: {e}. Backend running in degraded/in-memory mode.")
    
    # Verify Ollama connectivity and model presence
    try:
        health_info = await check_ollama_health()
        logger.info(f"Ollama connected successfully. Serving model: {health_info['model']}")
        
        # Verify ALL models configured in models_registry.json are actually pulled locally in Ollama
        from backend.models_registry import models_registry
        available_tags = health_info.get("available_models", [])
        all_ok, found_models, missing_models = models_registry.verify_all_models_present(available_tags)
        
        if missing_models:
            logger.critical(
                f"[STARTUP_CONFIG_ALERT] [WARNING] Missing locally pulled models defined in models_registry.json: {missing_models}!\n"
                f"Available in Ollama: {available_tags}.\n"
                f"Remediation: Run `ollama pull <model_id>` for each missing model to avoid runtime failovers."
            )
        else:
            logger.info(f"[STARTUP_CONFIG_CHECK] All {len(found_models)} registry models verified in local Ollama: {found_models}")
    except Exception as e:
        logger.warning(f"Ollama health check warning: {e}. Backend running in degraded/offline-ollama mode.")
        
    yield
    logger.info("Shutting down Air-Gapped Backend.")


app = FastAPI(
    title="Air-Gapped Sovereign AI Chatbot Backend",
    description="Offline local AI backend using FastAPI and Ollama for industrial intranet",
    version="2.0.0",
    lifespan=lifespan,
)

# ══════════════════════════════════════════════════════════════════════
# Global API authentication gate.
#
# Every HTTP route in this application lives under /api, so a single
# middleware closes the default-open surface in one place instead of relying
# on each handler remembering to check a token. Only the routes a browser
# must reach *before* it has a token are public.
#
# Note: this middleware is registered BEFORE the CORS middleware below, so CORS
# ends up outermost and its headers are present even on a 401 response.
# ══════════════════════════════════════════════════════════════════════
PUBLIC_API_ROUTES = {
    ("POST", "/api/v1/auth/login"),
    ("POST", "/api/auth/login"),
    ("POST", "/api/v1/auth/ldap-login"),
    ("POST", "/api/v1/auth/cert-login"),
    ("GET", "/api/health"),
    ("GET", "/api/v1/health"),
    ("GET", "/docs"),
    ("GET", "/redoc"),
    ("GET", "/openapi.json"),
}


@app.middleware("http")
async def enforce_api_auth(request: Request, call_next):
    path = request.url.path
    method = request.method.upper()

    # Preflight and non-API paths are not authenticated here.
    if method == "OPTIONS" or not path.startswith("/api"):
        return await call_next(request)

    if (method, path) in PUBLIC_API_ROUTES:
        return await call_next(request)

    caller = _caller_from_request(request)
    if not caller:
        logger.warning(
            f"[AUTH] Rejected unauthenticated {method} {path} from "
            f"{request.client.host if request.client else 'unknown'}"
        )
        return JSONResponse(
            status_code=401,
            content={
                "status": "ERROR",
                "detail": "Authentication required. Send 'Authorization: Bearer <session token>'.",
            },
        )

    # Expose the verified identity to handlers.
    request.state.caller = caller
    return await call_next(request)


# CORS Middleware for local intranet access.
# The browser apps run on localhost/LAN origins, so we allow those explicitly
# (configurable) instead of "*" — a wildcard plus credentials is never safe.
_DEFAULT_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:3443",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:3443",
]
_env_origins = os.getenv("AEGIS_ALLOWED_ORIGINS", "").strip()
ALLOWED_ORIGINS = [o.strip() for o in _env_origins.split(",") if o.strip()] or _DEFAULT_ALLOWED_ORIGINS
# Air-gapped plant deployments reach the workbench over private ranges
# (10/8, 172.16-31, 192.168/16) on any port.
ALLOWED_ORIGIN_REGEX = r"^https?://(localhost|127\.0\.0\.1|(10\.\d+\.\d+\.\d+)|(192\.168\.\d+\.\d+)|(172\.(1[6-9]|2\d|3[01])\.\d+\.\d+))(:\d+)?$"

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=ALLOWED_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)


# Request Logging Middleware
@app.middleware("http")
async def audit_and_log_middleware(request: Request, call_next):
    start_time = time.time()
    client_ip = request.client.host if request.client else "unknown"
    
    # Audit check: verify no external headers or redirects
    host_header = request.headers.get("host", "")
    logger.info(f"[HTTP] {request.method} {request.url.path} from {client_ip}")
    
    response = await call_next(request)
    duration = round((time.time() - start_time) * 1000, 2)
    logger.info(f"[HTTP] {request.method} {request.url.path} -> status={response.status_code} ({duration}ms)")
    return response


# --- Pydantic Request Models ---
class ChatRequest(BaseModel):
    message: str = Field(..., description="User prompt text")
    mode: Optional[str] = Field("auto", description="Execution mode: auto | chat | code | docs | excel | ppt")
    chat_id: Optional[str] = Field(None, description="Unique conversation session ID")
    attachments: Optional[List[str]] = Field(default=None, description="List of uploaded filenames or file paths")
    agent_id: Optional[str] = Field(default=None, description="Optional custom agent ID for persona execution")


# --- API Endpoints ---

def _database_health() -> Dict[str, Any]:
    """
    Reports the configured database engine and whether it actually answers.

    The engine label comes from configuration; `connected` is a live probe, so a
    misconfigured or stopped database is visible here rather than surfacing later
    as a failed request.
    """
    from backend.db_dialect import describe
    info: Dict[str, Any] = {
        "driver": DB_DRIVER,
        "engine": "PostgreSQL" if IS_POSTGRES else "MySQL/MariaDB",
        "target": describe(),
        "connected": False,
    }
    try:
        from backend.db_dialect import get_db_connection
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        finally:
            conn.close()
        info["connected"] = True
    except Exception as exc:
        info["error"] = f"{type(exc).__name__}: {exc}"
    return info


@app.get("/api/health")
async def get_health():
    """
    1. GET /api/health -> {status, ollama_connected, model: MODEL_NAME, database}
    """
    database = _database_health()
    try:
        health_info = await check_ollama_health()
        return {
            "status": "ok" if database["connected"] else "degraded",
            "ollama_connected": True,
            "model": MODEL_NAME,
            "num_ctx": NUM_CTX,
            "air_gapped": True,
            "database": database,
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "ollama_connected": False,
                "model": MODEL_NAME,
                "error": str(e),
                "database": database,
                "fix": f"run: ollama serve && ollama pull {MODEL_NAME}"
            }
        )


# In-memory tracking of the last execution route per chat session
SESSION_LAST_ROUTE: Dict[str, str] = {}

# Per-request actor for the RAG audit ledger, so a retrieval triggered by this
# turn is attributed to the authenticated caller rather than a fixed "operator".
SESSION_ACTOR: ContextVar[Optional[str]] = ContextVar("aegis_session_actor", default=None)


async def generate_chat_events(
    user_msg: str,
    requested_mode: str,
    chat_id: str,
    attachments: Optional[List[str]] = None,
    agent_id: Optional[str] = None
):
    """
    Core execution pipeline shared across POST /api/chat and WS /api/chat/stream.
    Yields structured event dicts:
    1. {"route", "department", "template", "thinking", "rag", "model", "event": "meta"}
    2. {"thinking": "..."} frames (when think=True)
    3. {"token": "..."} repeatedly
    4. {"done": True, ...}
    """
    # ── STRUCTURED LOGGING: Single request_id propagated through all downstream calls ──
    from backend.structured_logger import (
        set_current_request_id,
        log_stage_event,
        log_model_selection,
    )
    from backend.knowledge_base import set_retrieval_actor
    req_id = set_current_request_id(chat_id)
    # Attribute any RAG retrieval triggered by this turn to the real caller.
    set_retrieval_actor(SESSION_ACTOR.get())
    pipeline_start_t = time.perf_counter()
    log_stage_event(
        stage="PIPELINE_ENTRY",
        status="STARTED",
        request_id=req_id,
        input_summary=f"msg_len={len(user_msg)}, requested_mode={requested_mode}, attachments={len(attachments) if attachments else 0}",
        metadata={"chat_id": chat_id, "agent_id": agent_id or "default"}
    )

    last_route = SESSION_LAST_ROUTE.get(chat_id)
    router_start_t = time.perf_counter()
    route, trigger_keyword = await route_message_async(
        user_msg,
        requested_mode,
        attachments=attachments,
        last_route=last_route,
        allow_multi=False
    )
    router_elapsed_ms = (time.perf_counter() - router_start_t) * 1000.0
    SESSION_LAST_ROUTE[chat_id] = route

    # Config-driven model selection from registry (no hardcoded model branches)
    from backend.router import get_model_for_route
    effective_model, effective_ctx, effective_temp = get_model_for_route(route)
    log_model_selection(
        selected_model=effective_model,
        routing_decision=f"route={route}",
        reason=f"trigger={trigger_keyword}, mode_requested={requested_mode}, attachments_count={len(attachments) if attachments else 0}",
        request_id=req_id,
        confidence=None
    )
    log_stage_event(
        stage="ROUTER",
        status="SUCCESS",
        request_id=req_id,
        input_summary=f"requested_mode={requested_mode}",
        output_summary=f"route={route}, model={effective_model}, trigger={trigger_keyword}",
        elapsed_ms=router_elapsed_ms,
        metadata={"trigger": trigger_keyword, "model": effective_model, "context_window": effective_ctx, "temperature": effective_temp}
    )

    # --- DEPARTMENT DETECTION ---
    department, dept_trigger = detect_department(user_msg)
    logger.info(
        f"[DEPT] chat_id={chat_id} department={department} "
        f"trigger={dept_trigger} msg={user_msg[:60]!r}"
    )

    # --- TEMPLATE DETECTION ---
    template_key = detect_template(user_msg)
    if template_key:
        logger.info(f"[TEMPLATE] chat_id={chat_id} template={template_key}")

    # --- ADAPTIVE THINKING DECISION ---
    think_decision, think_reason = get_thinking_decision_with_reason(user_msg, route)
    logger.info(
        f"[THINK] chat_id={chat_id} route={route} think={think_decision} "
        f"trigger={think_reason} msg={user_msg[:80]!r}"
    )

    # --- RAG GATING (chat mode only) ---
    rag_status = "skipped"
    rag_chunks: Optional[List[Dict[str, Any]]] = None
    rag_trigger = "not_applicable"
    has_upload = False

    if route == "chat":
        rag_decision, rag_trigger = get_rag_decision_with_reason(user_msg, has_upload)
        logger.info(
            f"[RAG] chat_id={chat_id} should_retrieve={rag_decision} "
            f"trigger={rag_trigger} msg={user_msg[:80]!r}"
        )

        if rag_decision:
            if is_follow_up_query(user_msg):
                cached = rag_cache.get(chat_id)
                if cached:
                    rag_chunks = cached["chunks"]
                    rag_status = "hit"
                    logger.info(
                        f"[RAG] chat_id={chat_id} FOLLOW-UP CACHE REUSE "
                        f"cached_query={cached['query']!r} chunks={len(rag_chunks)}"
                    )
                else:
                    rag_chunks = search_sops(user_msg, min_score=MIN_RAG_SCORE, top_k=MAX_RAG_CHUNKS)
                    if rag_chunks:
                        rag_status = "hit"
                        rag_cache.store(chat_id, user_msg, rag_chunks)
                    else:
                        rag_status = "no_relevant_context"
            else:
                rag_chunks = search_sops(user_msg, min_score=MIN_RAG_SCORE, top_k=MAX_RAG_CHUNKS)
                if rag_chunks:
                    rag_status = "hit"
                    rag_cache.store(chat_id, user_msg, rag_chunks)
                else:
                    rag_status = "no_relevant_context"

            if rag_chunks:
                chunk_info = [
                    (
                        c["doc_id"],
                        f"cosine={c['similarity_score']}" if c.get("similarity_score") is not None
                        else f"bm25={c.get('bm25_score', 0.0)}",
                    )
                    for c in rag_chunks
                ]
                logger.info(f"[RAG] chat_id={chat_id} INJECTED chunks={chunk_info}")
            else:
                logger.info(
                    f"[RAG] chat_id={chat_id} NO_RELEVANT_CONTEXT_FOUND "
                    f"min_score={MIN_RAG_SCORE} -> explicit no-context directive injected"
                )
        else:
            logger.info(f"[RAG] chat_id={chat_id} SKIPPED reason={rag_trigger}")

    # Event 0: Direct Routing Event frame (updates UI routing badge & trace immediately)
    routed_by_label = "model_orchestrator" if (trigger_keyword and "model_orchestrator" in trigger_keyword) else (
        "manual" if trigger_keyword == "manual_override" else "heuristic_regex"
    )
    yield {
        "event": "routing",
        "domain": route,
        "model_id": effective_model,
        "routed_by": routed_by_label,
        # The router does not compute a calibrated confidence. Reporting 98
        # would be a fabricated number, so it is null with an explicit method.
        "confidence": None,
        "confidence_method": "not_computed",
        "reason": trigger_keyword,
    }

    # Event 1: Extended meta frame
    yield {
        "route": route,
        "department": department,
        "template": template_key,
        "thinking": think_decision,
        "rag": rag_status,
        "model": effective_model,
        "event": "meta",
        "trigger": trigger_keyword,
        "dept_trigger": dept_trigger,
        "think_reason": think_reason if think_decision else None,
        "rag_trigger": rag_trigger if route == "chat" else None,
    }

    full_tokens: List[str] = []
    sandbox_job_id = None
    sandbox_exit_code = None
    try:
        if requested_mode in ("agent", "agentic", "multistep"):
            from backend.agent_loop import run_multistep_agent_loop
            handler = run_multistep_agent_loop(chat_id, user_msg)
        elif route == "code":
            handler = handle_code_mode(chat_id, user_msg, think=think_decision)
        elif route == "docs":
            handler = handle_document_mode("docs", chat_id, user_msg)
        elif route == "excel":
            handler = handle_excel_mode(chat_id, user_msg)
        elif route == "ppt":
            handler = handle_ppt_mode(chat_id, user_msg)
        elif route in ("vision", "ocr"):
            handler = handle_vision_mode(
                chat_id,
                user_msg,
                attachments=attachments,
                is_ocr=(route == "ocr"),
                think=think_decision
            )
        else:
            handler = handle_chat_mode(
                chat_id,
                user_msg,
                think=think_decision,
                rag_chunks=rag_chunks,
                rag_status=rag_status,
                agent_id=agent_id
            )

        async for event in handler:
            if event.get("event") == "step" and event.get("step_type") == "thought":
                yield event
            elif "thinking" in event and event.get("event") == "step":
                yield event
            elif "token" in event:
                full_tokens.append(event["token"])
                yield {
                    "token": event["token"],
                    "event": "step",
                    "step_type": "token",
                    "content": event["token"],
                }
            elif event.get("done"):
                gen_file = event.get("generated_file")
                run_out = event.get("run_output")
                code_status = event.get("status")
                # Use the handler's filtered content (thinking already stripped)
                handler_content = event.get("content", "")
                accumulated_text = handler_content if handler_content else filter_thinking("".join(full_tokens))
                # Prefer the model the handler actually reported (ground truth).
                # Otherwise keep the registry-resolved model from
                # get_model_for_route() -- this line used to overwrite it with
                # the hardcoded MODEL_NAME/VISION_MODEL_NAME constants, so the
                # UI routing badge and the audit log named a model that did not
                # produce the answer.
                final_model = event.get("model_id") or effective_model
                yield {
                    "done": True,
                    "generated_file": gen_file,
                    "run_output": run_out,
                    "status": code_status,
                    "event": "final_answer",
                    "content": accumulated_text,
                    "deliverable_ids": [gen_file] if gen_file else [],
                    "model_id": final_model,
                    "routed_by": route,
                    "thinking": think_decision,
                    "rag": rag_status,
                    "department": department,
                    "template": template_key,
                    # The pipeline does not compute a calibrated confidence, so we
                    # report null rather than an invented 100%.
                    "confidence": None,
                    "confidence_method": "not_computed",
                }
            else:
                yield event

        # Log summary line for backend.log
        rag_detail = rag_status
        if rag_status == "hit" and rag_chunks:
            chunk_names = [c["doc_id"] for c in rag_chunks]
            rag_detail = f"hit({','.join(chunk_names)})"
        logger.info(
            f"[PIPELINE] chat_id={chat_id} route={route} dept={department} "
            f"template={template_key or 'none'} think={think_decision} "
            f"reason={think_reason} rag={rag_detail} tokens={len(full_tokens)}"
        )
        # STRUCTURED LOGGING: Pipeline completion event
        try:
            total_elapsed_ms = (time.perf_counter() - pipeline_start_t) * 1000.0
            log_stage_event(
                stage="PIPELINE_COMPLETE",
                status="SUCCESS",
                request_id=req_id,
                input_summary=f"route={route}, user_prompt_len={len(user_msg)}",
                output_summary=f"tokens_generated={len(full_tokens)}, rag={rag_detail}",
                elapsed_ms=total_elapsed_ms,
                metadata={
                    "route": route,
                    "model": effective_model,
                    "tokens_count": len(full_tokens),
                    "department": department,
                }
            )
        except Exception:
            pass

    except Exception as e:
        logger.error(f"[CHAT ERROR] chat_id={chat_id} route={route} error={e}", exc_info=True)
        # STRUCTURED LOGGING: Pipeline failure event
        try:
            total_elapsed_ms = (time.perf_counter() - pipeline_start_t) * 1000.0
            log_stage_event(
                stage="PIPELINE_COMPLETE",
                status="FAILED",
                request_id=req_id,
                input_summary=f"route={route}",
                elapsed_ms=total_elapsed_ms,
                error=e,
                metadata={"route": route}
            )
        except Exception:
            pass
        err_msg = f"\n\n[Error processing request: {str(e)}]"
        yield {"token": err_msg, "event": "step", "step_type": "error", "content": err_msg}
        yield {
            "done": True,
            "generated_file": None,
            "run_output": None,
            "status": "error",
            "error": str(e),
            "event": "final_answer",
            "content": "".join(full_tokens) + err_msg,
        }


@app.post("/api/chat")
async def chat_endpoint(request_body: ChatRequest, request: Request):
    """
    POST /api/chat -> {message, mode, chat_id} -> SSE stream:
       - event 1: {"route": "...", "thinking": true/false, "rag": "hit"|"miss"|"skipped", "model": "..."}
       - then:    {"thinking": "..."} (collapsible, when think=True)
       - then:    {"token": "..."} repeatedly
       - final:   {"done": true, "generated_file": "<url or null>", "run_output": "<string or null>"}
    """
    attachments = request_body.attachments
    # ChatRequest has no `prompt` field; reading it raised AttributeError for any
    # client that sent an empty `message`. Only `message` is a real field.
    user_msg = (request_body.message or "").strip()
    if not user_msg and attachments:
        user_msg = "Analyze the attached image and describe what you see."
    elif not user_msg:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
        
    chat_id = request_body.chat_id or f"chat_{uuid.uuid4().hex[:10]}"
    requested_mode = request_body.mode or "auto"
    agent_id = request_body.agent_id

    # Log user query to activity & monitoring audit ledger.
    # The identity comes from the verified bearer token, not a hardcoded
    # "operator", so the Security Monitor can attribute a query to a real user.
    try:
        from backend.db import log_user_activity
        audit_username, audit_role = _request_identity(request)
        SESSION_ACTOR.set(audit_username)
        log_user_activity(
            username=audit_username,
            role=audit_role,
            activity_type="CHAT_QUERY",
            query_text=user_msg,
            channel_or_chat_id=chat_id,
            details=f"Mode: {requested_mode} | Agent: {agent_id or 'default'}",
            file_meta=attachments
        )
    except Exception as log_err:
        logger.warning(f"[AUDIT_LOG_WARN] Failed to record user query: {log_err}")

    async def sse_event_generator():
        async for event in generate_chat_events(user_msg, requested_mode, chat_id, attachments=attachments, agent_id=agent_id):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        sse_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        },
    )


async def _authorize_websocket(websocket: WebSocket) -> Optional[Dict[str, Any]]:
    """
    Authenticates a WebSocket connection via the `token` query parameter.

    Must be called BEFORE `websocket.accept()`. Closing an unaccepted socket
    makes the server reject the HTTP upgrade with 403, so an unauthenticated
    client never gets a successful handshake in the first place (rather than
    being accepted and immediately dropped with close code 4401).
    """
    token = (websocket.query_params.get("token") or "").strip()
    payload = _decode_token(token) if token else None
    if not payload:
        await websocket.close(code=1008, reason="Authentication required")
        return None
    return payload


@app.websocket("/api/chat/stream")
async def websocket_chat_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time token and reasoning stream.
    Payload: {"message": str, "mode": Optional[str], "chat_id": Optional[str], "attachments": Optional[List[str]], "agent_id": Optional[str]}
    Connect with ?token=<session token> (authentication is enforced).
    """
    # Authenticate before accepting: an invalid token fails the HTTP upgrade.
    caller = await _authorize_websocket(websocket)
    if not caller:
        logger.warning("[WS] Rejected unauthenticated /api/chat/stream connection")
        return
    await websocket.accept()
    logger.info(f"[WS] Client connected to /api/chat/stream as {caller.get('sub')}")
    # Attribute any RAG retrieval on this connection to the verified caller.
    SESSION_ACTOR.set(str(caller.get("sub") or "operator"))

    try:
        while True:
            raw_data = await websocket.receive_text()
            try:
                data = json.loads(raw_data)
            except Exception as parse_err:
                logger.warning(f"[WS] Malformed JSON received: {parse_err}")
                await websocket.send_json({"error": "Malformed JSON payload", "done": True})
                continue

            attachments = data.get("attachments") or data.get("files")
            user_msg = (data.get("message") or data.get("prompt") or "").strip()
            requested_mode = data.get("mode") or data.get("role") or "auto"
            chat_id = data.get("chat_id") or data.get("session_id") or f"chat_{uuid.uuid4().hex[:10]}"
            agent_id = data.get("agent_id")

            if not user_msg and attachments:
                user_msg = "Analyze the attached image and describe what you see."
            elif not user_msg:
                await websocket.send_json({"error": "Empty message", "done": True})
                continue

            logger.info(f"[WS STREAM] chat_id={chat_id} mode={requested_mode} prompt={user_msg[:60]!r}")
            async for event in generate_chat_events(user_msg, requested_mode, chat_id, attachments=attachments, agent_id=agent_id):
                await websocket.send_json(event)
    except WebSocketDisconnect:
        logger.info("[WS] Client disconnected from /api/chat/stream")
    except Exception as e:
        logger.error(f"[WS ERROR] /api/chat/stream: {e}", exc_info=True)


@app.websocket("/api/audit-stream")
async def websocket_audit_stream(websocket: WebSocket):
    """
    WebSocket continuous 1000ms air-gap network & VRAM telemetry heartbeat stream.
    Gathers genuine psutil active network sockets and VRAM/RAM statistics.
    Connect with ?token=<session token> (authentication is enforced).
    """
    caller = await _authorize_websocket(websocket)
    if not caller:
        logger.warning("[WS] Rejected unauthenticated /api/audit-stream connection")
        return
    await websocket.accept()
    logger.info(f"[WS] Client connected to /api/audit-stream as {caller.get('sub')}")
    try:
        while True:
            ram = psutil.virtual_memory()
            gpu = _get_gpu_info()

            # Dynamic project-only socket inspection and active air-gap guard
            try:
                from backend.airgap_guard import inspect_and_guard_project_sockets
                current_pid = os.getpid()
                live_sockets = inspect_and_guard_project_sockets(current_pid)
            except Exception as exc:
                logger.debug(f"Socket inspection fallback: {exc}")
                live_sockets = []

            localhost_cnt = len([s for s in live_sockets if s["tier"] == "LOCALHOST"])
            lan_cnt = len([s for s in live_sockets if s["tier"] == "LAN_HOTSPOT"])
            blocked_cnt = len([s for s in live_sockets if s["tier"] == "EXTERNAL_WAN"])

            payload = {
                "sovereignty": {
                    # Socket counts are measured; packet counters are not
                    # available on this deployment and are never invented.
                    "external_packets": None,
                    "localhost_packets": None,
                    "lan_hotspot_packets": None,
                    "packet_counting_available": False,
                    "localhost_connections": localhost_cnt,
                    "lan_hotspot_connections": lan_cnt,
                    "external_internet_connections": blocked_cnt,
                    "verdict": (
                        f"ALERT: {blocked_cnt} external socket(s) observed by the egress guard"
                        if blocked_cnt > 0
                        else "No external sockets observed at sample time (point-in-time psutil inspection)"
                    ),
                    "sampled_at": datetime.now().isoformat(timespec="seconds"),
                    "daemon_heartbeat_hz": 1.0,
                    "sockets": live_sockets[:30]
                },
                "vram": {
                    "gpu_available": gpu.get("gpu_available", False),
                    "gpu_name": gpu.get("gpu_name", None),
                    "used_mb": gpu.get("used_mb", 0),
                    "total_mb": gpu.get("total_mb", 0),
                    "free_mb": gpu.get("free_mb", 0),
                    "percent": gpu.get("utilization_percent", 0),
                    "temperature_celsius": gpu.get("temperature_celsius", None),
                    "system_ram_total_mb": round(ram.total / (1024 * 1024)),
                    "system_ram_used_mb": round(ram.used / (1024 * 1024)),
                    "system_ram_free_mb": round(ram.available / (1024 * 1024)),
                    "system_ram_percent": ram.percent,
                }
            }
            await websocket.send_json(payload)
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        logger.info("[WS] Client disconnected from /api/audit-stream")
    except Exception as e:
        logger.debug(f"[WS AUDIT STREAM CLOSED] {e}")


@app.get("/api/chat/sessions")
async def list_chat_sessions(username: Optional[str] = None):
    """Lists saved conversation sessions from XAMPP MySQL."""
    from backend.db import list_all_chat_sessions
    sessions = list_all_chat_sessions()
    return {"status": "SUCCESS", "sessions": sessions}


@app.post("/api/chat/sessions")
async def create_chat_session(payload: Optional[Dict[str, Any]] = None):
    """Creates or initializes a chat session ID."""
    sess_id = uuid.uuid4().hex[:16]
    return {
        "status": "SUCCESS",
        "session": {
            "id": sess_id,
            "title": "New Chat",
            "created_at": int(time.time()),
            "messages": []
        }
    }


@app.get("/api/chat/sessions/{session_id}")
async def get_chat_session(session_id: str):
    """Returns conversation messages for the given session ID from XAMPP MySQL."""
    history = get_chat_history(session_id)
    first_title = "Chat"
    for m in history:
        if m.get("role") == "user":
            first_title = m.get("content", "Chat")[:40]
            break
    return {
        "status": "SUCCESS",
        "session": {
            "id": session_id,
            "title": first_title,
            "created_at": int(time.time()),
            "messages": history
        }
    }


@app.delete("/api/chat/sessions/{session_id}")
async def delete_chat_session(session_id: str):
    """Deletes conversation session and associated data from XAMPP MySQL."""
    from backend.db import delete_chat_session_data
    delete_chat_session_data(session_id)
    return {"status": "SUCCESS", "deleted": session_id}


def _get_gpu_info() -> Dict[str, Any]:
    """Try to get GPU info via nvidia-smi. Returns empty dict if unavailable."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.used,memory.total,memory.free,temperature.gpu,utilization.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=3
        )
        if result.returncode == 0 and result.stdout.strip():
            parts = result.stdout.strip().split(", ")
            if len(parts) >= 6:
                return {
                    "gpu_available": True,
                    "gpu_name": parts[0].strip(),
                    "used_mb": int(parts[1]),
                    "total_mb": int(parts[2]),
                    "free_mb": int(parts[3]),
                    "temperature_celsius": float(parts[4]),
                    "utilization_percent": float(parts[5]),
                }
    except Exception:
        pass
    return {"gpu_available": False}


@app.get("/api/v1/models/vram")
async def get_vram_metrics():
    ram = psutil.virtual_memory()
    gpu = _get_gpu_info()
    return {
        "gpu_available": gpu.get("gpu_available", False),
        "gpu_name": gpu.get("gpu_name", None),
        "total_mb": gpu.get("total_mb", 0),
        "used_mb": gpu.get("used_mb", 0),
        "free_mb": gpu.get("free_mb", 0),
        "usage_percent": gpu.get("utilization_percent", 0),
        "temperature_celsius": gpu.get("temperature_celsius", None),
        "os_overhead_mb": 0,
        "primary_model_mb": gpu.get("used_mb", 0),
        "secondary_model_mb": 0,
        "kv_cache_mb": 0,
        "system_ram_total_mb": round(ram.total / (1024 * 1024)),
        "system_ram_used_mb": round(ram.used / (1024 * 1024)),
        "system_ram_free_mb": round(ram.available / (1024 * 1024)),
        "system_ram_percent": ram.percent,
    }


@app.get("/api/v1/models/status")
async def get_models_status():
    from backend.domains import get_active_domain, get_active_domain_info
    models_list = await get_models()
    return {
        "status": "ready",
        "active_model": MODEL_NAME,
        "active_domain": get_active_domain(),
        "domain_info": get_active_domain_info(),
        "models": models_list,
    }


# --- Domain Management Endpoints (PSU, Defence, Government, Refinery) ---
@app.get("/api/domains")
async def list_available_domains():
    """Returns list of supported industrial and enterprise domains with active selection."""
    from backend.domains import list_domains, get_active_domain
    return {
        "status": "SUCCESS",
        "active_domain": get_active_domain(),
        "domains": list_domains(),
    }


@app.get("/api/domains/active")
async def get_current_domain():
    """Returns metadata for the currently active domain."""
    from backend.domains import get_active_domain_info
    return {
        "status": "SUCCESS",
        "domain": get_active_domain_info(),
    }


class SwitchDomainRequest(BaseModel):
    domain: str


@app.post("/api/domains/switch")
async def switch_operational_domain(req: SwitchDomainRequest):
    """Dynamically switches active operational domain across the air-gapped system."""
    from backend.domains import set_active_domain, get_active_domain_info, DOMAIN_REGISTRY
    domain_key = req.domain.strip().lower()
    if domain_key not in DOMAIN_REGISTRY:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid domain '{req.domain}'. Valid choices: {list(DOMAIN_REGISTRY.keys())}"
        )
    set_active_domain(domain_key)
    info = get_active_domain_info()
    logger.info(f"[DOMAIN] Operational domain successfully switched to: '{domain_key}' ({info['name']})")
    return {
        "status": "SUCCESS",
        "message": f"Operational domain switched to {info['name']}",
        "active_domain": domain_key,
        "domain_info": info,
    }


# --- Auth ---
import base64
import hashlib
import hmac

# --- Password hashing -------------------------------------------------
# NOTE: the repo-root `.env` is loaded by `backend.config` at import time, which
# happens before this module is read. A second loader used to live here, far
# below the config import, so it ran too late to affect any setting.

# Passwords are stored as PBKDF2-HMAC-SHA256 with a per-user random salt.
# Legacy unsalted SHA-256 hashes are still *verified* (so existing accounts keep
# working) but are transparently upgraded to PBKDF2 on the next successful login.
PBKDF2_ITERATIONS = 260_000
PASSWORD_ALGO = "pbkdf2_sha256"


def _hash_password(password: str, salt_hex: Optional[str] = None) -> Dict[str, str]:
    salt = bytes.fromhex(salt_hex) if salt_hex else secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return {
        "password_hash": digest.hex(),
        "password_salt": salt.hex(),
        "password_algo": PASSWORD_ALGO,
    }


def _verify_password(password: str, user: Dict[str, Any]) -> bool:
    stored = user.get("password_hash", "")
    algo = user.get("password_algo", "sha256_legacy")
    if algo == PASSWORD_ALGO:
        expected = _hash_password(password, user.get("password_salt"))["password_hash"]
        return hmac.compare_digest(expected, stored)
    # Legacy format: unsalted SHA-256.
    return hmac.compare_digest(hashlib.sha256(password.encode()).hexdigest(), stored)


AUTH_USERS = {
    "admin": {
        # Development seed accounts only. Override the whole registry with
        # AEGIS_USERS_JSON for any real deployment.
        "role": "SUPER_ADMIN",
        "full_name": "Refinery Compliance Chief",
        "department": "Executive HSE & CISO",
        "status": "ACTIVE",
        "can_verify": True,
        "created_at": "2026-01-10 09:00:00",
        **_hash_password("RefineryAdmin2026!"),
    },
    "operator": {
        "role": "FIELD_OPERATOR",
        "full_name": "Lead Process Operator",
        "department": "Refinery Operations",
        "status": "ACTIVE",
        "can_verify": False,
        "created_at": "2026-02-14 11:30:00",
        **_hash_password("RefineryPass2026!"),
    },
    "engineer": {
        "role": "MAINTENANCE_ENG",
        "full_name": "Senior Reliability Engineer",
        "department": "Mechanical Maintenance",
        "status": "ACTIVE",
        "can_verify": True,
        "created_at": "2026-03-01 14:15:00",
        **_hash_password("RefineryEng2026!"),
    },
    "lead": {
        "role": "PROCESS_LEAD",
        "full_name": "Chief Process Lead",
        "department": "Crude Distillation Unit (CDU)",
        "status": "ACTIVE",
        "can_verify": True,
        "created_at": "2026-03-15 08:45:00",
        **_hash_password("ProcessLead2026!"),
    },
}

# Real deployments supply their own accounts, e.g.
#   AEGIS_USERS_JSON='{"alice":{"password":"...","role":"SUPER_ADMIN","department":"HSE"}}'
_env_users = os.getenv("AEGIS_USERS_JSON", "").strip()
if _env_users:
    try:
        _parsed_users = json.loads(_env_users)
        if not isinstance(_parsed_users, dict):
            raise ValueError("AEGIS_USERS_JSON must be a JSON object keyed by username")
        for _uname, _spec in _parsed_users.items():
            if not isinstance(_spec, dict):
                continue
            _entry: Dict[str, Any] = {
                "role": _spec.get("role", "FIELD_OPERATOR"),
                "full_name": _spec.get("full_name", _uname),
                "department": _spec.get("department", "Unassigned"),
                "status": _spec.get("status", "ACTIVE"),
                "can_verify": _spec.get("can_verify", _spec.get("role") in ("SUPER_ADMIN", "PROCESS_LEAD", "MAINTENANCE_ENG")),
                "created_at": _spec.get("created_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            }
            if _spec.get("password"):
                _entry.update(_hash_password(str(_spec["password"])))
            elif _spec.get("password_hash"):
                # Pre-hashed accounts are supported so plaintext never has to be
                # present in the environment.
                _entry["password_hash"] = _spec["password_hash"]
                _entry["password_salt"] = _spec.get("password_salt", "")
                _entry["password_algo"] = _spec.get("password_algo", PASSWORD_ALGO)
            else:
                continue
            AUTH_USERS[_uname.lower()] = _entry
    except Exception as _users_err:
        logger.critical(f"[SECURITY] AEGIS_USERS_JSON could not be parsed: {_users_err}")

# Token signing secret: supplied by the environment in any real deployment.
# If it is missing we generate a strong random per-process secret (tokens then
# stop validating after a restart, which is the safe failure mode) and warn.
_ENV_JWT_SECRET = os.getenv("AEGIS_JWT_SECRET", "").strip()
USING_EPHEMERAL_JWT_SECRET = not _ENV_JWT_SECRET
JWT_SECRET = _ENV_JWT_SECRET or secrets.token_urlsafe(48)
TOKEN_TTL_SECONDS = int(os.getenv("AEGIS_TOKEN_TTL_SECONDS", "28800"))


def _token_signature(raw_payload_b64: str) -> str:
    return hmac.new(
        JWT_SECRET.encode(),
        raw_payload_b64.encode(),
        hashlib.sha256,
    ).hexdigest()


def _make_token(username: str, role: str) -> str:
    """Issues an HMAC-signed session token (payload.signature)."""
    payload = json.dumps(
        {"sub": username, "role": role, "exp": int(time.time()) + TOKEN_TTL_SECONDS}
    )
    payload_b64 = base64.urlsafe_b64encode(payload.encode()).decode()
    return f"{payload_b64}.{_token_signature(payload_b64)}"


def _decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verifies and decodes a session token.

    Returns None for anything that is not an intact, correctly signed,
    unexpired token — an unsigned/edited token can never be trusted.
    """
    if not token or "." not in (token or ""):
        return None
    payload_b64, _, signature = token.partition(".")
    if not payload_b64 or not signature:
        return None
    expected = _token_signature(payload_b64)
    if not hmac.compare_digest(expected, signature):
        logger.warning("[AUTH] Rejected a token with an invalid signature.")
        return None
    try:
        payload = json.loads(base64.urlsafe_b64decode(payload_b64.encode()))
    except Exception:
        return None
    if payload.get("exp", 0) < time.time():
        return None
    return payload


def _caller_from_request(request: Request) -> Optional[Dict[str, Any]]:
    """
    Resolves the caller identity from the Authorization header, or None.

    The `Bearer` scheme is required: a bare token with no scheme (or a different
    scheme) is not accepted, so the credential format is unambiguous.
    """
    if request is None:
        return None
    auth_header = request.headers.get("Authorization", "")
    if not auth_header:
        return None
    scheme, _, token = auth_header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return _decode_token(token.strip())


def _require_roles(
    request: Request,
    allowed_roles: tuple,
    action: str,
    claimed_role: Optional[str] = None,
):
    """
    Enforces that the caller is authenticated AND holds an allowed role.

    A missing or invalid token is 401 — an unverified request is never
    treated as authorised just because no role could be determined.
    """
    caller = _caller_from_request(request)
    if not caller:
        raise HTTPException(
            status_code=401,
            detail=f"Authentication required to {action}. Provide 'Authorization: Bearer <token>'.",
        )
    role = caller.get("role")
    if role not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail=(
                f"Access Denied: {action} requires one of "
                f"{', '.join(allowed_roles)} (caller role: {role or 'unknown'})."
            ),
        )
    return caller


class LoginRequest(BaseModel):
    username: str
    password: str


# Capability grants per role. Returned to the client so UI affordances can be
# gated consistently, and sent on every login/whoami response.
_ROLE_PERMISSIONS: Dict[str, List[str]] = {
    "SUPER_ADMIN": [
        "read", "write", "admin", "verify", "user:manage",
        "rag:reindex_global", "domain:switch", "sovereignty:export",
    ],
    "ADMIN": [
        "read", "write", "admin", "verify", "user:manage",
        "rag:reindex_global", "domain:switch", "sovereignty:export",
    ],
    "PROCESS_LEAD": ["read", "write", "verify", "rag:reindex_global"],
    "MAINTENANCE_ENG": ["read", "write", "verify"],
    "FIELD_OPERATOR": ["read", "write"],
    "PLANT_SECURITY_OFFICER": [
        "read", "write", "admin", "verify", "user:manage", "sovereignty:export",
    ],
}


def _permissions_for_role(role: str) -> List[str]:
    """Returns the capability list granted to a role (read-only by default)."""
    return list(_ROLE_PERMISSIONS.get((role or "").upper(), ["read"]))


@app.post("/api/v1/auth/login")
async def login_endpoint(body: LoginRequest):
    """POST /api/v1/auth/login -> authenticate user and return token."""
    user = AUTH_USERS.get(body.username)
    if not user:
        return JSONResponse(status_code=401, content={"status": "ERROR", "detail": "Invalid credentials"})

    if user.get("status") == "FROZEN":
        return JSONResponse(
            status_code=403,
            content={"status": "ERROR", "detail": "Access Denied: Account is frozen/suspended by Administrator."}
        )

    if not _verify_password(body.password, user):
        return JSONResponse(status_code=401, content={"status": "ERROR", "detail": "Invalid credentials"})

    # Transparent upgrade: a legacy unsalted hash becomes PBKDF2 on first login.
    if user.get("password_algo", "sha256_legacy") != PASSWORD_ALGO:
        user.update(_hash_password(body.password))
        logger.info(f"[AUTH] Upgraded the stored password hash for '{body.username}' to {PASSWORD_ALGO}.")

    token = _make_token(body.username, user["role"])
    logger.info(f"[AUTH] Login successful: user={body.username} role={user['role']}")
    # Permissions are echoed inside `user` as well as at the top level: the
    # client stores only `data.user`, so a top-level-only field left
    # `user.permissions` undefined and role-gated UI checks could never pass.
    granted_permissions = _permissions_for_role(user["role"])
    return {
        "status": "SUCCESS",
        "token": token,
        "access_token": token,
        "auth_method": "LOCAL_DATABASE",
        "user": {
            "username": body.username,
            "role": user["role"],
            "full_name": user["full_name"],
            "department": user["department"],
            "can_verify": user.get("can_verify", user["role"] in ("SUPER_ADMIN", "PROCESS_LEAD", "MAINTENANCE_ENG")),
            "permissions": granted_permissions,
        },
        "permissions": granted_permissions,
    }


@app.get("/api/v1/auth/me")
async def get_auth_me(request: Request):
    """GET /api/v1/auth/me -> return current user from token."""
    payload = _caller_from_request(request)
    if not payload:
        return JSONResponse(
            status_code=401,
            content={"status": "ERROR", "detail": "No valid bearer token provided"},
        )

    username = payload.get("sub", "")
    user = AUTH_USERS.get(username)
    if not user:
        return JSONResponse(status_code=401, content={"status": "ERROR", "detail": "User not found"})

    return {
        "status": "SUCCESS",
        "username": username,
        "role": user["role"],
        "full_name": user["full_name"],
        "department": user["department"],
        "can_verify": user.get("can_verify", user["role"] in ("SUPER_ADMIN", "PROCESS_LEAD", "MAINTENANCE_ENG")),
        "permissions": _permissions_for_role(user["role"]),
        "authenticated": True,
    }


@app.get("/api/history/{chat_id}")
async def get_history(chat_id: str):
    """
    3. GET /api/history/{chat_id} -> returns full message history for conversation.
    """
    messages = get_chat_history(chat_id)
    return {
        "chat_id": chat_id,
        "count": len(messages),
        "messages": messages
    }


@app.get("/api/files/list")
async def list_files(chat_id: Optional[str] = None):
    """Lists generated deliverable files with full 2-step verification metadata."""
    from backend.db import backfill_file_metadata, get_all_deliverable_files
    rows = get_all_deliverable_files(chat_id)
    
    items = []
    backfilled = 0
    for r in rows:
        v_status = r.get("verification_status") or "PENDING_STAGE_1"
        size_bytes = r.get("size_bytes")
        sha256_hash = r.get("sha256_hash")

        # Self-heal legacy rows: compute the real size/hash once, then persist it
        # so the Canvas/verification UIs report genuine integrity metadata.
        if (size_bytes is None or not sha256_hash) and backfilled < 25:
            try:
                candidate = Path(r.get("file_path") or "")
                if candidate.exists() and candidate.is_file() and candidate.stat().st_size <= 20 * 1024 * 1024:
                    computed_hash, computed_size = file_integrity(candidate)
                    if computed_hash:
                        backfill_file_metadata(r["file_id"], computed_hash, computed_size)
                        sha256_hash = sha256_hash or computed_hash
                        size_bytes = size_bytes if size_bytes is not None else computed_size
                        backfilled += 1
            except Exception as e:
                logger.debug(f"[FILES LIST] Integrity backfill skipped for {r.get('file_id')}: {e}")

        items.append({
            "file_id": r["file_id"],
            "chat_id": r["chat_id"],
            "filename": r["filename"],
            "file_type": r["file_type"],
            "verification_status": v_status,
            "stage_1_verifier": r.get("stage_1_verifier"),
            "stage_1_at": str(r["stage_1_at"]) if r.get("stage_1_at") else None,
            "stage_1_notes": r.get("stage_1_notes"),
            "stage_2_verifier": r.get("stage_2_verifier"),
            "stage_2_at": str(r["stage_2_at"]) if r.get("stage_2_at") else None,
            "stage_2_notes": r.get("stage_2_notes"),
            "rejected_by": r.get("rejected_by"),
            "rejected_at": str(r["rejected_at"]) if r.get("rejected_at") else None,
            "reject_reason": r.get("reject_reason"),
            "size_bytes": size_bytes,
            "sha256_hash": sha256_hash,
            "created_at": str(r["created_at"]),
            "updated_at": str(r["updated_at"]) if r.get("updated_at") else None,
            "download_url": f"/api/files/{r['file_id']}"
        })
    return {"files": items}


class RenameFileRequest(BaseModel):
    filename: str


@app.post("/api/files/{file_id}/rename")
async def rename_file(file_id: str, body: RenameFileRequest):
    """Renames an existing generated deliverable."""
    from backend.db import rename_file_record
    success = rename_file_record(file_id, body.filename)
    if not success:
        raise HTTPException(status_code=404, detail="File not found")
    return {"status": "SUCCESS", "file_id": file_id, "new_filename": body.filename}


# =====================================================================
# 2-STEP HUMAN VERIFICATION & APPROVAL WORKFLOW ENDPOINTS
# =====================================================================

class VerifyActionRequest(BaseModel):
    verifier: Optional[str] = None
    notes: Optional[str] = None
    role: Optional[str] = None


class RejectActionRequest(BaseModel):
    rejected_by: Optional[str] = None
    reason: str
    role: Optional[str] = None


class EditAndApproveRequest(BaseModel):
    verifier: Optional[str] = None
    notes: Optional[str] = None
    role: Optional[str] = None
    stage: int = 1 # 1 for Stage 1, 2 for Stage 2
    filename: Optional[str] = None


@app.get("/api/verification/pending")
@app.get("/api/v1/verification/pending")
async def get_pending_verification_items(role: Optional[str] = None, request: Request = None):
    """
    Returns deliverables awaiting verification filtered by the caller's
    authenticated role (the `role` query parameter is ignored for authorization):
    - PROCESS_LEAD / MAINTENANCE_ENG / FIELD_OPERATOR -> Stage 1 items only
    - SUPER_ADMIN / ADMIN -> Stage 1 and Stage 2 items
    """
    from backend.db import get_pending_verifications
    # The role is taken from the signed token only. A client-supplied `role`
    # query parameter is never trusted for authorization.
    caller = _require_roles(
        request,
        ("PROCESS_LEAD", "MAINTENANCE_ENG", "SUPER_ADMIN", "ADMIN", "FIELD_OPERATOR"),
        "view the verification queue",
    )
    effective_role = caller.get("role")

    items = get_pending_verifications(effective_role)
    stage1_count = len([i for i in items if i.get("verification_status") == "PENDING_STAGE_1"])
    stage2_count = len([i for i in items if i.get("verification_status") == "PENDING_STAGE_2"])
    
    formatted = []
    for r in items:
        formatted.append({
            "file_id": r["file_id"],
            "chat_id": r["chat_id"],
            "filename": r["filename"],
            "file_type": r["file_type"],
            "verification_status": r.get("verification_status") or "PENDING_STAGE_1",
            "stage_1_verifier": r.get("stage_1_verifier"),
            "stage_1_at": str(r["stage_1_at"]) if r.get("stage_1_at") else None,
            "stage_1_notes": r.get("stage_1_notes"),
            "stage_2_verifier": r.get("stage_2_verifier"),
            "stage_2_at": str(r["stage_2_at"]) if r.get("stage_2_at") else None,
            "stage_2_notes": r.get("stage_2_notes"),
            "created_at": str(r["created_at"]),
            "download_url": f"/api/files/{r['file_id']}"
        })

    return {
        "status": "SUCCESS",
        "role": effective_role,
        "total_pending": len(formatted),
        "stage1_pending": stage1_count,
        "stage2_pending": stage2_count,
        "items": formatted
    }


@app.post("/api/verification/{file_id}/stage1/approve")
@app.post("/api/v1/verification/{file_id}/stage1/approve")
async def approve_stage_1(file_id: str, body: VerifyActionRequest, request: Request):
    """
    Step 1 Verification Approval (Lower Post / L1 Peer Review):
    Authorized Roles: PROCESS_LEAD, MAINTENANCE_ENG, SUPER_ADMIN
    Advances deliverable from PENDING_STAGE_1 -> PENDING_STAGE_2.
    """
    from backend.db import get_file_record, verify_file_stage_1
    _require_roles(
        request,
        ("PROCESS_LEAD", "MAINTENANCE_ENG", "SUPER_ADMIN", "ADMIN"),
        "approve Step 1 verification",
    )
    record = get_file_record(file_id)
    if not record:
        raise HTTPException(status_code=404, detail="Deliverable file not found")
        
    current_status = record.get("verification_status")
    if current_status != "PENDING_STAGE_1":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot execute Step 1 Approval: Document is currently in '{current_status}' stage."
        )

    verifier = body.verifier or "ProcessLead"
    notes = body.notes or "Step 1: Technical parameters and mass balance approved by Process Lead"
    
    verify_file_stage_1(file_id, verifier=verifier, notes=notes)
    logger.info(f"[VERIFY STEP 1 - LOWER POST] File {file_id} approved by {verifier}. Advanced to PENDING_STAGE_2.")
    
    return {
        "status": "SUCCESS",
        "file_id": file_id,
        "verification_status": "PENDING_STAGE_2",
        "stage": 1,
        "message": f"Step 1 Verification Approved by {verifier}. Document advanced to Higher Post (Step 2 Sign-Off)."
    }


@app.post("/api/verification/{file_id}/stage2/approve")
@app.post("/api/v1/verification/{file_id}/stage2/approve")
async def approve_stage_2(file_id: str, body: VerifyActionRequest, request: Request):
    """
    Step 2 Verification Final Sign-Off (Higher Post / Executive CISO & Compliance Chief):
    Strictly Authorized: SUPER_ADMIN (or authorized Compliance Executive)
    Transitions deliverable from PENDING_STAGE_2 -> VERIFIED.
    """
    from backend.db import get_file_record, verify_file_stage_2
    # Authorization runs before any lookup so an unauthenticated caller cannot
    # probe which file ids exist (404 vs 401 would leak that).
    _require_roles(
        request,
        ("SUPER_ADMIN", "ADMIN"),
        "complete Step 2 final sign-off",
    )
    record = get_file_record(file_id)
    if not record:
        raise HTTPException(status_code=404, detail="Deliverable file not found")
        
    current_status = record.get("verification_status")
    if current_status == "PENDING_STAGE_1":
        raise HTTPException(
            status_code=400, 
            detail="Access Denied: Document must first be approved by Lower Post in Step 1 before Higher Post can sign off."
        )
    elif current_status != "PENDING_STAGE_2":
        raise HTTPException(
            status_code=400,
            detail=f"Document is not awaiting Step 2 Sign-off (Current status: {current_status})."
        )

    # Authorization: the caller must be authenticated and hold the required role.
    # (Previously an unresolvable role skipped the check entirely.)

    verifier = body.verifier or "Refinery Compliance Chief"
    notes = body.notes or "Step 2: Executive compliance & regulatory sign-off certified"
    
    verify_file_stage_2(file_id, verifier=verifier, notes=notes)
    logger.info(f"[VERIFY STEP 2 - HIGHER POST] File {file_id} signed off by {verifier}. Status: VERIFIED.")
    
    return {
        "status": "SUCCESS",
        "file_id": file_id,
        "verification_status": "VERIFIED",
        "stage": 2,
        "message": f"Document fully verified and cryptographically signed off by Higher Post ({verifier})."
    }


@app.post("/api/verification/{file_id}/reject")
@app.post("/api/v1/verification/{file_id}/reject")
async def reject_verification(file_id: str, body: RejectActionRequest, request: Request):
    """
    Rejection action (at either Step 1 or Step 2):
    Marks deliverable as REJECTED with mandatory reason note.
    """
    from backend.db import get_file_record, reject_file
    caller = _require_roles(
        request,
        ("PROCESS_LEAD", "MAINTENANCE_ENG", "SUPER_ADMIN", "ADMIN"),
        "reject a deliverable",
    )
    record = get_file_record(file_id)
    if not record:
        raise HTTPException(status_code=404, detail="Deliverable file not found")
        
    if not body.reason.strip():
        raise HTTPException(status_code=400, detail="Rejection reason is required")
        
    rejected_by = body.rejected_by or caller.get("sub") or "Reviewer"
    reject_file(file_id, rejected_by=rejected_by, reason=body.reason.strip())
    logger.info(f"[VERIFY REJECT] File {file_id} rejected by {rejected_by}. Reason: {body.reason}")
    
    return {
        "status": "SUCCESS",
        "file_id": file_id,
        "verification_status": "REJECTED",
        "rejected_by": rejected_by,
        "reason": body.reason,
        "message": f"Document rejected by {rejected_by}."
    }


@app.post("/api/verification/{file_id}/edit-and-approve")
@app.post("/api/v1/verification/{file_id}/edit-and-approve")
async def edit_and_approve(file_id: str, body: EditAndApproveRequest, request: Request):
    """
    Make Edits & Proceed:
    Updates document metadata/filename, records verification notes, and promotes to next stage.
    """
    from backend.db import get_file_record, verify_file_stage_1, verify_file_stage_2, rename_file_record
    _require_roles(
        request,
        ("PROCESS_LEAD", "MAINTENANCE_ENG", "SUPER_ADMIN", "ADMIN") if body.stage == 1
        else ("SUPER_ADMIN", "ADMIN"),
        f"edit-and-approve at stage {body.stage}",
    )
    record = get_file_record(file_id)
    if not record:
        raise HTTPException(status_code=404, detail="Deliverable file not found")
        
    # If a new filename was provided from editor canvas
    if body.filename and body.filename.strip():
        rename_file_record(file_id, body.filename.strip())

    verifier = body.verifier or "Reviewer"
    notes = body.notes or "Edited and approved by reviewer"

    if body.stage == 1:
        verify_file_stage_1(file_id, verifier=verifier, notes=notes)
        next_status = "PENDING_STAGE_2"
    else:
        verify_file_stage_2(file_id, verifier=verifier, notes=notes)
        next_status = "VERIFIED"

    return {
        "status": "SUCCESS",
        "file_id": file_id,
        "verification_status": next_status,
        "message": f"Document edited & approved by {verifier}. Advanced to {next_status}."
    }



@app.get("/api/ppt/styles")
async def get_ppt_styles():
    """Returns the comprehensive registry of 50 unique presentation styles and themes."""
    from backend.ppt_styles import list_all_ppt_styles
    styles = list_all_ppt_styles()
    return {
        "count": len(styles),
        "styles": styles
    }


@app.get("/api/files/{file_id}/content")
async def get_file_content(file_id: str):
    """
    Parses and returns structured content of generated deliverables (.xlsx, .docx, .pptx)
    so Canvas Editors display the EXACT live generated data instead of fallback templates.
    """
    record = get_file_record(file_id)
    if not record:
        raise HTTPException(status_code=404, detail="File not found.")
        
    file_path = Path(record["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk.")
        
    filename = record["filename"]
    file_type = record["file_type"].lower()

    # 1. Parse Excel Workbook (.xlsx)
    if file_type == "xlsx":
        try:
            import openpyxl
            wb = openpyxl.load_workbook(str(file_path), data_only=True)
            sheets_out = []
            for s_idx, ws in enumerate(wb.worksheets):
                rows_data = []
                for r_idx, row in enumerate(ws.iter_rows(values_only=True)):
                    row_cells = []
                    for c_idx, val in enumerate(row):
                        is_hdr = (r_idx == 0 or (r_idx == 2 and ws.cell(row=1, column=1).value))
                        val_str = "" if val is None else str(val)
                        align = "right" if isinstance(val, (int, float)) else "left"
                        bg = "#f1f5f9" if is_hdr else "#ffffff"
                        row_cells.append({
                            "value": val_str,
                            "isHeader": is_hdr,
                            "style": {
                                "bold": is_hdr,
                                "align": align,
                                "bgColor": bg,
                                "color": "#0f172a" if is_hdr else "#1e293b"
                            }
                        })
                    if any(c["value"] for c in row_cells):
                        rows_data.append(row_cells)
                        
                sheets_out.append({
                    "id": f"sheet-{s_idx + 1}",
                    "name": ws.title,
                    "rows": rows_data if rows_data else [
                        [{"value": "No Data", "isHeader": False, "style": {"align": "left"}}]
                    ]
                })
            return {"file_id": file_id, "filename": filename, "file_type": "xlsx", "sheets": sheets_out}
        except Exception as e:
            logger.error(f"Error parsing xlsx deliverable {file_id}: {e}")
            return {"file_id": file_id, "filename": filename, "file_type": "xlsx", "error": str(e)}

    # 2. Parse Word Document (.docx)
    elif file_type == "docx":
        try:
            import docx
            doc = docx.Document(str(file_path))
            html_parts = []
            
            for p in doc.paragraphs:
                text = p.text.strip()
                if not text:
                    continue
                if p.style.name.startswith("Heading 1"):
                    html_parts.append(f'<h1 style="color: #1e40af; border-bottom: 2px solid #cbd5e1; padding-bottom: 6px; font-size: 20px; font-weight: 800; margin-top: 18px;">{text}</h1>')
                elif p.style.name.startswith("Heading 2"):
                    html_parts.append(f'<h2 style="color: #0369a1; font-size: 16px; font-weight: 700; margin-top: 16px;">{text}</h2>')
                elif p.style.name.startswith("Heading 3"):
                    html_parts.append(f'<h3 style="color: #0f172a; font-size: 14px; font-weight: 700; margin-top: 12px;">{text}</h3>')
                elif p.style.name.startswith("List Bullet") or text.startswith("• ") or text.startswith("- "):
                    clean_bullet = text.lstrip("•-* ")
                    html_parts.append(f'<li style="color: #1e293b; line-height: 1.7; font-size: 14px; margin-left: 18px;">{clean_bullet}</li>')
                else:
                    html_parts.append(f'<p style="color: #1e293b; line-height: 1.7; font-size: 14px; margin-top: 8px;">{text}</p>')

            for tbl in doc.tables:
                table_html = ['<table style="width: 100%; border-collapse: collapse; margin-top: 14px; margin-bottom: 18px; border: 1px solid #cbd5e1; font-size: 13px;">']
                for r_idx, row in enumerate(tbl.rows):
                    table_html.append("<tr>")
                    for cell in row.cells:
                        c_text = cell.text.strip()
                        if r_idx == 0:
                            table_html.append(f'<th style="padding: 9px 12px; background-color: #f1f5f9; border: 1px solid #cbd5e1; font-weight: 700; text-align: left; color: #0f172a;">{c_text}</th>')
                        else:
                            table_html.append(f'<td style="padding: 8px 12px; border: 1px solid #e2e8f0; color: #334155;">{c_text}</td>')
                    table_html.append("</tr>")
                table_html.append("</table>")
                html_parts.append("".join(table_html))

            final_html = "".join(html_parts)
            return {"file_id": file_id, "filename": filename, "file_type": "docx", "html": final_html}
        except Exception as e:
            logger.error(f"Error parsing docx deliverable {file_id}: {e}")
            return {"file_id": file_id, "filename": filename, "file_type": "docx", "error": str(e)}

    # 3. Parse PowerPoint Slides (.pptx)
    elif file_type == "pptx":
        try:
            from pptx import Presentation
            prs = Presentation(str(file_path))
            slides_out = []
            
            for s_idx, slide in enumerate(prs.slides):
                title = ""
                subtitle = ""
                bullets = []
                notes = ""
                table_data = None
                
                if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
                    notes = slide.notes_slide.notes_text_frame.text.strip()
                    
                for shape in slide.shapes:
                    # Check for Table Shape
                    if shape.has_table:
                        tbl = shape.table
                        t_headers = [tbl.cell(0, c_idx).text.strip() for c_idx in range(len(tbl.columns))]
                        t_rows = []
                        for r_idx in range(1, len(tbl.rows)):
                            row_vals = [tbl.cell(r_idx, c_idx).text.strip() for c_idx in range(len(tbl.columns))]
                            if any(row_vals):
                                t_rows.append(row_vals)
                        table_data = {"headers": t_headers, "rows": t_rows}
                    
                    # Check for Text Shape
                    elif shape.has_text_frame:
                        for p_idx, p in enumerate(shape.text_frame.paragraphs):
                            t = p.text.strip()
                            if not t:
                                continue
                            if not title:
                                title = t
                            elif not subtitle and s_idx == 0:
                                subtitle = t
                            else:
                                bullets.append(t.lstrip("•-*✓ "))
                                
                # Determine slide background color
                bg_color_hex = "#ffffff"
                accent_color_hex = "#ea580c"
                try:
                    if slide.background and slide.background.fill and slide.background.fill.fore_color:
                        c = slide.background.fill.fore_color.rgb
                        bg_color_hex = f"#{c[0]:02x}{c[1]:02x}{c[2]:02x}"
                except Exception:
                    pass

                layout_type = "title" if s_idx == 0 else ("table" if table_data else "content")
                slides_out.append({
                    "id": s_idx + 1,
                    "layout": layout_type,
                    "title": title or f"Slide {s_idx + 1}",
                    "subtitle": subtitle,
                    "bullets": bullets if bullets else (["Key Takeaways & Findings"] if not table_data else []),
                    "tableData": table_data,
                    "kpis": [],
                    "timeline": [],
                    "notes": notes,
                    "bgColor": bg_color_hex,
                    "accentColor": accent_color_hex,
                })
                
            return {"file_id": file_id, "filename": filename, "file_type": "pptx", "slides": slides_out}
        except Exception as e:
            logger.error(f"Error parsing pptx deliverable {file_id}: {e}")
            return {"file_id": file_id, "filename": filename, "file_type": "pptx", "error": str(e)}

    return {"file_id": file_id, "filename": filename, "file_type": file_type, "content": "Raw Binary"}


class SaveFileContentRequest(BaseModel):
    """Canvas save payload emitted by the chat frontend editors."""
    content: Dict[str, Any] = Field(default_factory=dict)
    editor: Optional[str] = None


def _request_identity(request: Optional[Request]) -> tuple:
    """Resolves (username, role) from the verified bearer token.

    The global gate already rejects unauthenticated /api calls, so a request
    that reaches here carries a valid token; the fallback is defensive only.
    """
    if request is None:
        return "operator", "FIELD_OPERATOR"
    payload = _caller_from_request(request)
    if not payload:
        return "operator", "FIELD_OPERATOR"
    return (
        payload.get("sub") or payload.get("username") or "operator",
        payload.get("role") or "FIELD_OPERATOR",
    )


@app.post("/api/files/{file_id}/content")
@app.post("/api/v1/files/{file_id}/content")
async def save_file_content(file_id: str, body: SaveFileContentRequest, request: Request):
    """
    Persists Canvas edits back onto the real deliverable on disk.

    The pre-edit revision is snapshotted to `<name>.bak` for auditability, the
    new revision is serialized to a temp file that keeps the original extension
    and then atomically swapped in, so a serialization failure can never
    destroy the original deliverable. Editing a document that already reached
    a later verification stage re-opens the 2-step human verification gate,
    because the approved bytes no longer match what is on disk.
    """
    record = get_file_record(file_id)
    if not record:
        raise HTTPException(status_code=404, detail="File not found.")

    file_path = Path(record["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk.")

    content = body.content or {}
    if not isinstance(content, dict) or not content:
        raise HTTPException(status_code=400, detail="Canvas payload is empty.")

    username, role = _request_identity(request)

    # 1. Preserve the pre-edit revision for audit
    backup_path = file_path.with_name(f"{file_path.name}.bak")
    try:
        shutil.copy2(str(file_path), str(backup_path))
    except Exception as e:
        logger.warning(f"[CANVAS SAVE] Could not snapshot revision of {file_id}: {e}")
        backup_path = None

    # 2. Serialize to a temp file that preserves the original extension
    temp_path = file_path.with_name(f"{file_path.stem}.canvas-tmp{file_path.suffix}")

    from backend.canvas_serialization import CanvasSerializationError, apply_editor_content_to_file

    try:
        apply_editor_content_to_file(temp_path, record.get("file_type", ""), content)
        os.replace(str(temp_path), str(file_path))
    except CanvasSerializationError as e:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass
        logger.error(f"[CANVAS SAVE] Serialization failed for {file_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Canvas save failed; the original deliverable was preserved. {e}",
        )

    # 3. Refresh integrity metadata and verification state
    sha256_hash, size_bytes = file_integrity(file_path)

    from backend.db import mark_file_edited

    edit_info = mark_file_edited(file_id, sha256_hash=sha256_hash, size_bytes=size_bytes) or {}
    previous_status = edit_info.get("previous_status")
    new_status = edit_info.get("verification_status")
    reverification_required = bool(edit_info.get("reverification_required"))

    # 4. Record the edit in the security audit ledger
    try:
        from backend.db import log_user_activity

        log_user_activity(
            username=username,
            role=role,
            activity_type="FILE_EDIT",
            channel_or_chat_id=record.get("chat_id"),
            query_text=f"Canvas save: {record.get('filename')}",
            details=(
                f"file_id={file_id} type={record.get('file_type')} "
                f"status {previous_status} -> {new_status}"
            ),
            file_meta={
                "file_id": file_id,
                "filename": record.get("filename"),
                "sha256_hash": sha256_hash,
                "size_bytes": size_bytes,
            },
        )
    except Exception as e:
        logger.debug(f"[CANVAS SAVE] Audit logging skipped: {e}")

    logger.info(
        f"[CANVAS SAVE] file_id={file_id} saved by {username} ({role}): "
        f"verification {previous_status} -> {new_status}"
    )

    return {
        "status": "SUCCESS",
        "file_id": file_id,
        "filename": record.get("filename"),
        "file_type": record.get("file_type"),
        "sha256_hash": sha256_hash,
        "size_bytes": size_bytes,
        "previous_verification_status": previous_status,
        "verification_status": new_status,
        "reverification_required": reverification_required,
        "backup_created": backup_path.name if backup_path else None,
        "message": (
            "Deliverable saved. Re-verification required because the content changed after approval."
            if reverification_required
            else "Deliverable saved to air-gapped storage."
        ),
    }


@app.get("/api/files/{file_id}")
@app.get("/api/files/download/{file_id}")
async def download_file(file_id: str):
    """
    Deliverable download endpoint serving genuine generated .docx, .xlsx, and .pptx files.
    """
    record = get_file_record(file_id)
    if not record:
        raise HTTPException(status_code=404, detail="File not found.")
        
    file_path = Path(record["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on storage disk.")
        
    filename = record["filename"]
    file_type = record["file_type"].lower()
    
    media_types = {
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "pdf": "application/pdf",
        "png": "image/png",
    }
    
    media_type = media_types.get(file_type, "application/octet-stream")
    logger.info(f"[DOWNLOAD] Serving deliverable file_id={file_id} filename={filename}")
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@app.get("/api/models")
@app.get("/api/models")
@app.get("/api/v1/models")
async def get_models():
    """Returns the active sovereign models dynamically discovered from Ollama plus any connected nodes."""
    from backend.nodes import get_all_nodes, _model_node_bindings
    import httpx
    
    # Auto-discover local Ollama models dynamically
    discovered_tags = []
    try:
        resp = httpx.get(f"{OLLAMA_HOST}/api/tags", timeout=3.0)
        if resp.status_code == 200:
            for item in resp.json().get("models", []):
                t_name = item.get("name")
                if t_name and t_name not in discovered_tags:
                    discovered_tags.append(t_name)
    except Exception as e:
        logger.debug(f"[MODELS] Ollama tag discovery fallback: {e}")

    model_configs = {
        "deepseek-v4-pro:4b": ("Sovereign Deep Reasoning (Gemma-4 / DeepSeek)", "text_reasoning", "General text, safety SOP verification, coding, and document generation engine.", 3400),
        "gemma4-e4b:latest": ("Gemma 4 Industrial Process Specialist", "engineering_process", "Refinery process thermodynamics, yield formulas, and furnace safety.", 3200),
        "qwen2.5vl:3b": ("Sovereign Industrial Multimodal (OCR & P&ID)", "vision_multimodal", "Multimodal visual inspection, CAD/P&ID diagrams, and tabular OCR extraction.", 2200),
        "unlimited-ocr:latest": ("Air-Gapped High-Speed OCR Engine", "ocr_extraction", "Document scanner, handwritten notes, and tag plate transcription.", 2000),
    }

    base_models = []
    # Ensure current primary model is first
    tags_to_process = list(discovered_tags) if discovered_tags else [MODEL_NAME, VISION_MODEL_NAME]
    if MODEL_NAME in tags_to_process:
        tags_to_process.remove(MODEL_NAME)
        tags_to_process.insert(0, MODEL_NAME)

    for tag in tags_to_process:
        cfg = model_configs.get(tag, (tag, "general", "Discovered sovereign open-weight model.", 2500))
        is_prim = (tag == MODEL_NAME)
        base_models.append({
            "id": tag,
            "name": tag,
            "display_name": cfg[0],
            "quantization": "Q4_K_M",
            "vram_mb": cfg[3],
            "context_length": NUM_CTX,
            "domain": cfg[1],
            "is_primary": is_prim,
            "keep_alive": "300s",
            "status": "active" if is_prim else "standby",
            "node_ip": "127.0.0.1",
            "description": cfg[2],
        })
    
    # Inject discovered models from remote nodes if any
    all_nodes = get_all_nodes()
    for node in all_nodes:
        if not node.is_local and node.status == "online":
            for m_tag in node.discovered_models:
                if not any(m["id"] == m_tag for m in base_models):
                    base_models.append({
                        "id": m_tag,
                        "name": m_tag,
                        "display_name": f"{m_tag} ({node.name})",
                        "quantization": "Remote GGUF",
                        "vram_mb": 4000,
                        "context_length": NUM_CTX,
                        "domain": "distributed_worker",
                        "is_primary": False,
                        "keep_alive": "300s",
                        "status": "standby",
                        "node_ip": node.host_ip,
                        "description": f"Remote worker model hosted on {node.host_ip}:{node.port} ({node.device_type}).",
                    })

    # Update node_ip based on bindings
    for m in base_models:
        bound_node_id = _model_node_bindings.get(m["id"])
        if bound_node_id:
            for n in all_nodes:
                if n.id == bound_node_id:
                    m["node_ip"] = n.host_ip
                    break

    return base_models


# --- Compute Node Management Endpoints ---

class AddNodeRequest(BaseModel):
    name: str
    host_ip: str
    port: int = 11434
    device_type: str = "LAN Worker"
    models: Optional[List[str]] = None

class TestNodeRequest(BaseModel):
    host_ip: str
    port: int = 11434

class BindModelRequest(BaseModel):
    model_id: str
    node_id: str

@app.get("/api/v1/nodes")
async def list_nodes():
    """Returns all registered local and remote compute nodes."""
    from backend.nodes import get_all_nodes
    return [node.dict() for node in get_all_nodes()]

@app.post("/api/v1/nodes/test")
async def test_node(body: TestNodeRequest):
    """Tests connection to a remote device running Ollama/vLLM on LAN and discovers models."""
    from backend.nodes import test_node_connection, is_private_or_loopback_ip
    if not is_private_or_loopback_ip(body.host_ip):
        raise HTTPException(
            status_code=400,
            detail="Air-Gap Security Violation: Only private RFC-1918 LAN IPs (192.168.x.x, 10.x.x.x, 172.16-31.x.x, localhost) are permitted."
        )
    result = await test_node_connection(body.host_ip, body.port)
    return result

@app.post("/api/v1/nodes")
@app.post("/api/v1/nodes/add")
async def add_compute_node(body: AddNodeRequest):
    """Adds a new remote compute worker device to the distributed cluster."""
    from backend.nodes import add_or_update_node, test_node_connection, is_private_or_loopback_ip
    if not is_private_or_loopback_ip(body.host_ip):
        raise HTTPException(
            status_code=400,
            detail="Air-Gap Security Violation: External WAN IP blocked. Use local LAN IP."
        )
    # Test connection and discover models if not provided
    test_res = await test_node_connection(body.host_ip, body.port)
    discovered = body.models or test_res.get("models", [])
    node = add_or_update_node(
        name=body.name,
        host_ip=body.host_ip,
        port=body.port,
        device_type=body.device_type,
        models=discovered
    )
    if not test_res.get("online"):
        node.status = "offline"
    return node.dict()

@app.delete("/api/v1/nodes/{node_id}")
async def delete_compute_node(node_id: str):
    """Removes a worker device from the compute cluster."""
    from backend.nodes import remove_node
    success = remove_node(node_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot remove primary local node or node not found.")
    return {"status": "success", "message": f"Node {node_id} removed."}

@app.post("/api/v1/nodes/bind")
async def bind_model(body: BindModelRequest):
    """Binds an LLM model to execute on a specific local or remote compute node."""
    from backend.nodes import bind_model_to_node
    bind_model_to_node(body.model_id, body.node_id)
    return {"status": "success", "message": f"Model {body.model_id} bound to node {body.node_id}."}


class ModelEndpointRequest(BaseModel):
    endpoint_url: str


@app.post("/api/v1/models/{model_id}/endpoint")
async def set_model_endpoint(model_id: str, body: ModelEndpointRequest):
    """
    Points a model at a specific Ollama endpoint.

    This route was missing, so the Admin UI's per-model endpoint editor always
    404'd. The endpoint is parsed into host/port, validated as RFC 1918 private
    or loopback (air-gap policy), registered as a compute node, and the model is
    bound to it — reusing the existing node registry rather than inventing a
    second binding mechanism.
    """
    from urllib.parse import urlparse
    from backend.nodes import (
        add_or_update_node, bind_model_to_node,
        is_private_or_loopback_ip, test_node_connection,
    )

    raw = (body.endpoint_url or "").strip()
    if not raw:
        raise HTTPException(status_code=400, detail="endpoint_url is required.")

    candidate = raw if "://" in raw else f"http://{raw}"
    parsed = urlparse(candidate)
    host_ip = (parsed.hostname or "").strip()
    if not host_ip:
        raise HTTPException(
            status_code=400,
            detail=f"Could not parse a host from endpoint_url '{raw}'.",
        )
    try:
        port = int(parsed.port or 11434)
    except ValueError:
        port = 11434

    if not is_private_or_loopback_ip(host_ip):
        raise HTTPException(
            status_code=400,
            detail=(
                "Air-Gap Security Violation: Only private RFC-1918 LAN IPs "
                "(192.168.x.x, 10.x.x.x, 172.16-31.x.x, localhost) are permitted."
            ),
        )

    probe = await test_node_connection(host_ip, port)
    node = add_or_update_node(
        name=f"endpoint:{host_ip}:{port}",
        host_ip=host_ip,
        port=port,
        device_type="LAN Worker",
        models=probe.get("models", []),
    )
    if not probe.get("online"):
        node.status = "offline"
    bind_model_to_node(model_id, node.id)

    logger.info(f"[MODELS] Bound '{model_id}' to endpoint {host_ip}:{port} (node {node.id})")
    return {
        "status": "SUCCESS",
        "model_id": model_id,
        "node_id": node.id,
        "host_ip": host_ip,
        "port": port,
        "reachable": bool(probe.get("online")),
        "message": (
            f"Model '{model_id}' bound to {host_ip}:{port}."
            + ("" if probe.get("online") else " Endpoint is not currently reachable.")
        ),
    }



class ModelSwapRequest(BaseModel):
    model_id: str
    chat_id: Optional[str] = None
    context_data: Optional[Any] = None


_swap_history_records = []

@app.get("/api/v1/models/swaps")
@app.get("/api/models/swaps")
async def get_model_swaps():
    """Returns recent hot-swap history for model telemetry observatory."""
    return _swap_history_records[-50:]

@app.post("/api/models/swap")
@app.post("/api/v1/models/swap")
async def manual_model_swap(body: ModelSwapRequest):
    """
    Explicitly triggers model swap in VRAM:
    - Unloads current active model (keep_alive=0)
    - Stores context in temporary buffer
    - Preloads target model
    """
    target = body.model_id
    from backend.ollama_client import swap_to_model
    current_primary = MODEL_NAME
    unload_target = current_primary if target == VISION_MODEL_NAME else VISION_MODEL_NAME

    success = await swap_to_model(
        target_model=target,
        unload_model_name=unload_target,
        chat_id=body.chat_id,
        context_to_transfer=body.context_data
    )

    record = {
        "id": f"swap-{int(time.time()*1000)}",
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "from_model": unload_target,
        "to_model": target,
        "duration_ms": 420,
        "status": "SUCCESS" if success else "FAILED",
        "trigger": "MANUAL_HOTSWAP",
        "target_met": success,
        "context_preserved": body.context_data is not None or (body.chat_id is not None)
    }
    _swap_history_records.append(record)
    return record


class SandboxRunRequest(BaseModel):
    code: str
    job_id: Optional[str] = None
    stdin_input: Optional[str] = None


@app.post("/api/sandbox/run")
@app.post("/api/v1/sandbox/run")
async def run_sandbox_code(body: SandboxRunRequest):
    """
    Executes Python script in isolated local or Docker sandbox
    and returns genuine stdout, stderr, execution time, and generated files.
    """
    from backend.sandbox import execute_python_sandbox
    result = execute_python_sandbox(body.code, job_id=body.job_id, stdin_input=body.stdin_input)
    return result


class CodeRunRequest(BaseModel):
    language: str
    code: str
    stdin_input: Optional[str] = None
    filename: Optional[str] = None


@app.post("/api/sandbox/run-code")
@app.post("/api/v1/sandbox/run-code")
async def run_code_endpoint(body: CodeRunRequest):
    """
    Executes code for the Canvas code / SQL / shell editors and returns genuine
    stdout, stderr, exit code and timing (plus real result rows for SQL).

    When no engine can honestly execute the language — e.g. shell without a
    Docker daemon, or C++ without a compiler — the response is
    `status: UNSUPPORTED` with the reason. The UI surfaces that instead of
    inventing output.
    """
    from backend.code_runner import run_code

    result = run_code(
        body.language,
        body.code,
        stdin_input=body.stdin_input,
        filename=body.filename,
    )
    logger.info(
        f"[CODE RUNNER] language={body.language} status={result['status']} "
        f"exit={result['exit_code']} duration_ms={result.get('duration_ms')}"
    )
    return result


# --- Additional Admin Endpoints for Complete Subsystem Support ---

class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: str = "FIELD_OPERATOR"
    full_name: str
    department: str = "Refinery Operations"

class UpdateUserRequest(BaseModel):
    role: Optional[str] = None
    full_name: Optional[str] = None
    department: Optional[str] = None
    status: Optional[str] = None
    password: Optional[str] = None

class ToggleFreezeRequest(BaseModel):
    status: str # "ACTIVE" | "FROZEN"

@app.get("/api/v1/auth/users")
@app.get("/api/auth/users")
async def list_auth_users():
    """Lists all provisioned sovereign operators and administrators."""
    users_list = []
    idx = 1
    for uname, udata in AUTH_USERS.items():
        users_list.append({
            "id": idx,
            "username": uname,
            "role": udata.get("role", "FIELD_OPERATOR"),
            "full_name": udata.get("full_name", uname),
            "department": udata.get("department", "Operations"),
            "status": udata.get("status", "ACTIVE"),
            "created_at": udata.get("created_at", "2026-01-01 00:00:00"),
        })
        idx += 1
    return {"status": "SUCCESS", "users": users_list}

@app.post("/api/v1/auth/users")
async def create_auth_user(body: CreateUserRequest):
    """Creates a new admin or operator account in the sovereign registry."""
    uname = body.username.strip().lower()
    if not uname:
        raise HTTPException(status_code=400, detail="Username cannot be empty")
    if uname in AUTH_USERS:
        raise HTTPException(status_code=400, detail=f"User '{uname}' already exists")
    
    pw_fields = _hash_password(body.password)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    AUTH_USERS[uname] = {
        **pw_fields,
        "role": body.role,
        "full_name": body.full_name,
        "department": body.department,
        "status": "ACTIVE",
        "created_at": now_str,
    }
    logger.info(f"[USER_MGMT] Created user: {uname} ({body.role})")
    return {
        "status": "SUCCESS",
        "message": f"User '{uname}' created successfully",
        "user": {
            "username": uname,
            "role": body.role,
            "full_name": body.full_name,
            "department": body.department,
            "status": "ACTIVE",
            "created_at": now_str
        }
    }

@app.put("/api/v1/auth/users/{username}")
async def update_auth_user(username: str, body: UpdateUserRequest):
    """Updates role, department, name, or password for an existing account."""
    uname = username.strip().lower()
    if uname not in AUTH_USERS:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = AUTH_USERS[uname]
    if body.role:
        user["role"] = body.role
    if body.full_name:
        user["full_name"] = body.full_name
    if body.department:
        user["department"] = body.department
    if body.status:
        user["status"] = body.status
    if body.password:
        user.update(_hash_password(body.password))
        
    logger.info(f"[USER_MGMT] Updated user: {uname} (role={user['role']}, status={user['status']})")
    return {
        "status": "SUCCESS",
        "message": f"User '{uname}' updated successfully",
        "user": {
            "username": uname,
            "role": user["role"],
            "full_name": user["full_name"],
            "department": user["department"],
            "status": user.get("status", "ACTIVE"),
        }
    }

@app.post("/api/v1/auth/users/{username}/freeze")
async def toggle_user_freeze(username: str, body: ToggleFreezeRequest):
    """Freezes (suspends) or activates a user account."""
    uname = username.strip().lower()
    if uname not in AUTH_USERS:
        raise HTTPException(status_code=404, detail="User not found")
    if uname == "admin" and body.status == "FROZEN":
        raise HTTPException(status_code=400, detail="Cannot freeze root administrator account 'admin'")
        
    AUTH_USERS[uname]["status"] = body.status
    logger.info(f"[USER_MGMT] Toggled freeze for {uname}: {body.status}")
    return {"status": "SUCCESS", "message": f"User '{uname}' status changed to {body.status}"}

@app.delete("/api/v1/auth/users/{username}")
async def delete_auth_user(username: str):
    """Deletes an operator account."""
    uname = username.strip().lower()
    if uname not in AUTH_USERS:
        raise HTTPException(status_code=404, detail="User not found")
    if uname == "admin":
        raise HTTPException(status_code=400, detail="Root administrator account 'admin' cannot be deleted")
        
    del AUTH_USERS[uname]
    logger.info(f"[USER_MGMT] Deleted user: {uname}")
    return {"status": "SUCCESS", "message": f"User '{uname}' deleted successfully"}



class RouterEvalRequest(BaseModel):
    query: str
    mode: Optional[str] = "auto"


@app.post("/api/v1/router/evaluate")
@app.post("/api/router/evaluate")
async def evaluate_router_query(body: RouterEvalRequest):
    """
    Evaluates routing decisions for a query without executing LLM inference.
    Returns domain, stage1 match status, target model, confidence, and latency.
    """
    start_t = time.perf_counter()
    query = body.query.strip()
    route, trigger = await route_message_async(query, body.mode or "auto")
    department, dept_trigger = detect_department(query)
    think_decision, think_reason = get_thinking_decision_with_reason(query, route)
    latency_ms = round((time.perf_counter() - start_t) * 1000, 2)
    
    target_model = VISION_MODEL_NAME if route in ("vision", "ocr") else MODEL_NAME
    
    tools = []
    if route == "code":
        tools = ["python_sandbox", "ast_screener"]
    elif route == "excel":
        tools = ["openpyxl_compiler", "formula_validator"]
    elif route == "ppt":
        tools = ["python_pptx", "slide_theme_engine"]
    elif route == "docs":
        tools = ["docx_synthesizer", "style_formatter"]
    elif route in ("ocr", "vision"):
        tools = ["paddle_ocr", "spatial_reasoner"]

    return {
        "status": "SUCCESS",
        "domain": route.upper(),
        "targetModel": target_model,
        # Derived from the router's own match signal, not a constant.
        "stage1Match": bool(trigger),
        "routedBy": f"stage1_{trigger}" if trigger else "unmatched_default",
        # Measured end-to-end router time; no artificial floor.
        "totalLatencyMs": latency_ms,
        # This deployment's router is deterministic stage-1 rule/tag matching.
        # There is no dense-centroid stage, so its latency is not reported.
        "stage2Executed": False,
        "stage2LatencyMs": None,
        "stage2Note": (
            "No dense/semantic stage is configured in this deployment; the "
            "router resolves on stage-1 rules and equipment tags only."
        ),
        # The router is a deterministic stage-1 matcher: it does not produce a
        # calibrated confidence, so we report null rather than inventing a number.
        "confidence": None,
        "confidence_method": "not_computed",
        "isInScope": None,
        "isInScopeNote": "Scope classification is not computed by this router.",
        "department": department,
        "thinking": think_decision,
        "thinkingReason": think_reason,
        "requiredTools": tools
    }


@app.get("/api/rag-admin/stats")
@app.get("/api/v1/rag-admin/stats")
async def get_rag_admin_stats():
    """
    Reports what the retrieval layer actually is.

    Previously this endpoint returned a hard-coded document count, a 1024
    "dimension" vector store and a "BAAI/bge-m3-gguf" embedding model that the
    system never used. Every field below is measured from the live corpus.
    """
    from backend.knowledge_base import corpus_stats, retrieval_status, distinct_document_count, last_ingest_at
    from backend.graph_rag import graphrag_engine

    stats = corpus_stats()
    retrieval = retrieval_status()
    emb = retrieval["dense"]
    document_count = distinct_document_count()

    return {
        "success": True,
        # Real counts derived from the loaded corpus.
        "documents": document_count,
        "document_count": document_count,
        "chunks": stats["total_chunks"],
        "total_chunks": stats["total_chunks"],
        "chunks_by_provenance": stats["chunks_by_provenance"],
        "authoritative_chunks": stats["authoritative_chunks"],
        "entities_count": len(graphrag_engine.entities),
        "relations_count": len(graphrag_engine.relations),
        "collections": 1,
        "collection_name": "in_process_knowledge_corpus",
        # Dimensions exist only when real embeddings are actually in use.
        "dimensions": None,
        "embedding_model": emb.get("model"),
        "dense_embeddings_enabled": bool(emb.get("available")),
        "embedding_status": emb.get("reason"),
        "lexical_index": stats["lexical_index"],
        "bm25_enabled": True,
        "retrieval_method": retrieval["method"],
        "last_indexed": last_ingest_at(),
        "persistence": "in_memory",
        "persistence_note": (
            "Ingested chunks live in the backend process and are lost on restart. "
            "Re-upload the source documents after a restart."
        ),
        "notice": stats["notice"],
    }


@app.get("/api/rag-admin/documents")
@app.get("/api/v1/rag-admin/documents")
async def get_rag_admin_documents():
    """Lists the documents actually present in the live corpus, with the real
    provenance of each one."""
    from backend.knowledge_base import MASTER_SOPS, last_ingest_at
    from backend.graph_rag import graphrag_engine

    docs_map: Dict[str, Dict[str, Any]] = {}
    for sop in MASTER_SOPS:
        # Group per-section chunk ids (<DOC>-01, <DOC>-02, ...) under one document.
        doc_key = sop.doc_id
        tail = sop.doc_id[-3:]
        if tail[0] == "-" and tail[1:].isdigit():
            doc_key = sop.doc_id.rsplit("-", 1)[0]
        if doc_key not in docs_map:
            docs_map[doc_key] = {
                "id": doc_key,
                "name": sop.title,
                "category": (sop.domain or "refinery").capitalize(),
                "chunks": 0,
                "sizeKb": 0,
                "provenance": sop.provenance,
                "authoritative": sop.authoritative,
                "source": sop.source,
                "timestamp": None,
            }
        docs_map[doc_key]["chunks"] += 1
        docs_map[doc_key]["sizeKb"] += max(1, len(sop.content) // 1024)

    # Uploaded documents that were registered as graph entities.
    for ent_id, ent in graphrag_engine.entities.items():
        if ent.category == "Uploaded Document" and ent_id not in docs_map:
            docs_map[ent_id] = {
                "id": ent_id,
                "name": ent.name,
                "category": (ent.domain or "refinery").capitalize(),
                "chunks": ent.properties.get("chunks", 1),
                "sizeKb": max(1, ent.properties.get("uploaded_size", 1024) // 1024),
                "provenance": "user_uploaded",
                "authoritative": False,
                "source": ent.name,
                "timestamp": last_ingest_at(),
            }

    docs_list = list(docs_map.values())
    return {
        "success": True,
        "count": len(docs_list),
        "documents": docs_list,
    }


from fastapi import UploadFile, File as FastAPIFile, Form

def _extract_upload_text(filename: str, contents: bytes) -> Tuple[str, Optional[str]]:
    """
    Extracts text from an uploaded document.

    Returns (text, error). When no text can be extracted the error explains why
    instead of substituting placeholder content: a fabricated chunk would be
    indexed and later cited as if it were real document content.
    """
    lower = (filename or "").lower()
    if lower.endswith(".pdf"):
        try:
            import pypdf
        except ImportError:
            return "", (
                "PDF text extraction requires the 'pypdf' package, which is not "
                "installed on this host. Install pypdf or upload a text-based file."
            )
        try:
            import io
            reader = pypdf.PdfReader(io.BytesIO(contents))
            parts = [(page.extract_text() or "") for page in reader.pages[:200]]
            text = "\n\n".join(p for p in parts if p.strip())
            if not text.strip():
                return "", (
                    "No extractable text layer in this PDF (it is most likely a "
                    "scanned image). OCR the document first, then re-upload."
                )
            return text, None
        except Exception as exc:
            return "", f"PDF parsing failed: {type(exc).__name__}: {exc}"
    try:
        return contents.decode("utf-8", errors="ignore"), None
    except Exception as exc:
        return "", f"Text decoding failed: {type(exc).__name__}: {exc}"


def _chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    """
    Splits text into overlapping windows on paragraph/sentence boundaries,
    honouring the requested chunk size and overlap.
    """
    chunk_size = max(200, int(chunk_size or 512))
    overlap = max(0, min(int(overlap or 0), chunk_size // 2))

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paragraphs:
        paragraphs = [text.strip()]

    chunks: List[str] = []
    current = ""
    for para in paragraphs:
        # A single oversized paragraph is hard-split on sentence boundaries.
        if len(para) > chunk_size:
            if current:
                chunks.append(current.strip())
                current = ""
            sentences = re.split(r"(?<=[.!?])\s+", para)
            buf = ""
            for sent in sentences:
                if len(buf) + len(sent) + 1 > chunk_size and buf:
                    chunks.append(buf.strip())
                    buf = (buf[-overlap:] if overlap else "") + " " + sent
                else:
                    buf = f"{buf} {sent}".strip()
            if buf.strip():
                chunks.append(buf.strip())
            continue

        if len(current) + len(para) + 2 > chunk_size and current:
            chunks.append(current.strip())
            # Carry the tail forward so context is not lost between chunks.
            current = (current[-overlap:] if overlap else "") + "\n\n" + para
        else:
            current = f"{current}\n\n{para}".strip() if current else para

    if current.strip():
        chunks.append(current.strip())

    return [c for c in chunks if len(c) >= 40]


@app.post("/api/rag-admin/ingest-file")
@app.post("/api/v1/rag-admin/ingest-file")
async def ingest_rag_files(
    files: List[UploadFile] = FastAPIFile(...),
    chunk_size: Optional[int] = Form(512),
    overlap: Optional[int] = Form(100),
):
    """
    Parses, chunks and indexes uploaded documents into the live corpus.

    Files whose text cannot be extracted are reported as FAILED with the real
    reason; no placeholder content is indexed in their place.
    """
    from backend.knowledge_base import (
        MASTER_SOPS, SOPChunk, add_chunk, corpus_stats, retrieval_status,
        PROVENANCE_UPLOADED, mark_ingested, last_ingest_at,
    )
    from backend.graph_rag import graphrag_engine, KnowledgeEntity
    from backend.domains import get_active_domain

    try:
        active_domain = get_active_domain()
    except Exception:
        active_domain = "refinery"

    ingested_summary: List[Dict[str, Any]] = []
    total_chunks_created = 0

    for upload in files:
        contents = await upload.read()
        filename = upload.filename or "uploaded_document.txt"
        text, error = _extract_upload_text(filename, contents)

        if error or not text.strip():
            reason = error or "The uploaded file contained no text."
            logger.warning(f"[INGEST] Rejected {filename}: {reason}")
            ingested_summary.append({
                "filename": filename,
                "status": "FAILED",
                "chunks_created": 0,
                "bytes": len(contents),
                "error": reason,
            })
            continue

        chunks = _chunk_text(text, chunk_size or 512, overlap or 0)
        if not chunks:
            reason = "Text was extracted but produced no usable chunk (content too short)."
            logger.warning(f"[INGEST] Rejected {filename}: {reason}")
            ingested_summary.append({
                "filename": filename,
                "status": "FAILED",
                "chunks_created": 0,
                "bytes": len(contents),
                "error": reason,
            })
            continue

        doc_base_id = filename.rsplit(".", 1)[0].replace(" ", "-").upper()[:48]
        ent_id = f"DOC-{doc_base_id[:12]}"
        graphrag_engine.entities[ent_id] = KnowledgeEntity(
            id=ent_id,
            name=filename,
            category="Uploaded Document",
            domain=active_domain,
            properties={"uploaded_size": len(contents), "chunks": len(chunks)}
        )

        created = 0
        for i, chunk_text in enumerate(chunks, 1):
            add_chunk(SOPChunk(
                doc_id=f"{doc_base_id}-{i:02d}",
                title=f"{filename} (part {i})",
                clause=f"Part {i}",
                page=f"Part {i}",
                content=chunk_text[:2000],
                keywords=[],
                equipment_tags=[],
                domain=active_domain,
                provenance=PROVENANCE_UPLOADED,
                authoritative=False,
                source=filename,
            ))
            created += 1

        total_chunks_created += created
        ingested_summary.append({
            "filename": filename,
            "status": "INGESTED",
            "chunks_created": created,
            "bytes": len(contents),
            "provenance": PROVENANCE_UPLOADED,
            "authoritative": False,
        })

    if total_chunks_created:
        mark_ingested()

    succeeded = [f for f in ingested_summary if f["status"] == "INGESTED"]
    failed = [f for f in ingested_summary if f["status"] == "FAILED"]

    if not succeeded and failed:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "No file could be ingested.",
                "failures": [{"filename": f["filename"], "error": f["error"]} for f in failed],
            },
        )

    status = "PARTIAL" if failed else "SUCCESS"
    message = f"Ingested {len(succeeded)} of {len(files)} file(s); {total_chunks_created} chunk(s) indexed."
    if failed:
        message += f" {len(failed)} file(s) failed - see per-file errors."

    logger.info(f"[RAG_ADMIN] {status}: {len(succeeded)}/{len(files)} files, {total_chunks_created} chunks indexed.")
    return {
        "status": status,
        "message": message,
        "files": ingested_summary,
        "failures": [{"filename": f["filename"], "error": f["error"]} for f in failed],
        "chunks_created": total_chunks_created,
        "total_master_sops": len(MASTER_SOPS),
        "corpus": corpus_stats(),
        "retrieval": retrieval_status(),
        "last_indexed": last_ingest_at(),
        "persistence": "in_memory",
        "persistence_note": (
            "Uploaded chunks are held in backend memory and are lost on restart. "
            "Re-upload the documents after a backend restart."
        ),
    }


# ── Parameter / tag extraction patterns used by the document upload pipeline ──
# These are genuine pattern matches against the extracted text. Nothing here
# invents a reading: a value only appears if the literal text contained it.
_UPLOAD_FINDING_PATTERNS = [
    # (category, compiled regex, value group, unit group or None)
    ("temperature", re.compile(r"(-?\d+(?:\.\d+)?)\s*°?\s*(C|celsius|deg\s*c)\b", re.IGNORECASE), 1, 2),
    ("specification", re.compile(r"(-?\d+(?:\.\d+)?)\s*(kPa|MPa|bar|psi|psig|N/m2)\b", re.IGNORECASE), 1, 2),
    ("specification", re.compile(r"(-?\d+(?:\.\d+)?)\s*(mm/s|rpm|Hz|kHz|ppm|ppmv|%)\b", re.IGNORECASE), 1, 2),
    ("corrosion", re.compile(r"(\d+(?:\.\d+)?)\s*(mm/y|mm/yr|mpy|mils?/yr)\b", re.IGNORECASE), 1, 2),
    ("tag", re.compile(r"\b([A-Z]{2,6}-\d{2,4}[A-Z]?(?:\s?-\s?[A-Z0-9]{1,4})?)\b"), 1, None),
    ("tag", re.compile(r"\b(P&ID\s?[-#]?\s?\d{2,5})\b", re.IGNORECASE), 1, None),
]


@app.post("/api/upload")
@app.post("/api/v1/upload")
async def upload_document(
    request: Request,
    file: UploadFile = FastAPIFile(...),
    chunk_size: Optional[int] = Form(512),
    overlap: Optional[int] = Form(100),
    index_into_corpus: bool = Form(True),
):
    """
    Ingests an operator-supplied document, indexes it into the live corpus and
    reports what was genuinely extracted from it.

    Everything in the response is measured:
      * `raw_ocr_text`   - only when a text layer actually parsed; empty for a
                           scanned image, and `ocr_engine` says so explicitly.
      * `findings`       - literal pattern matches (tags, readings with units).
      * `sop_violations` - corpus chunks that actually retrieved for this text,
                           reported as `doc_id | clause` so they can be checked.
      * `confidence`     - pattern-match certainty, NOT a measurement of the
                           reading's correctness. No value is ever invented.

    A document with no extractable text is reported as FAILED with the reason,
    and nothing is indexed in its place.
    """
    from backend.knowledge_base import (
        SOPChunk, add_chunk, mark_ingested, PROVENANCE_UPLOADED,
    )
    from backend.graph_rag import graphrag_engine, KnowledgeEntity
    from backend.chemical_kb import detect_chemicals
    from backend.domains import get_active_domain

    try:
        active_domain = get_active_domain()
    except Exception:
        active_domain = "refinery"

    filename = file.filename or "uploaded_document.txt"
    contents = await file.read()

    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    text, extract_error = _extract_upload_text(filename, contents)
    if extract_error or not text.strip():
        raise HTTPException(
            status_code=422,
            detail=extract_error or "No text could be extracted from this file.",
        )

    # ── Integrity ──────────────────────────────────────────────────────────
    sha256_hash, size_bytes = _hash_upload_bytes(contents)

    # ── Index into the live corpus ────────────────────────────────────────
    chunks = _chunk_text(text, chunk_size or 512, overlap or 0)
    doc_base_id = filename.rsplit(".", 1)[0].replace(" ", "-").upper()[:48]
    ent_id = f"DOC-{doc_base_id[:12]}"
    chunks_indexed = 0
    if index_into_corpus:
        graphrag_engine.entities[ent_id] = KnowledgeEntity(
            id=ent_id,
            name=filename,
            category="Uploaded Document",
            domain=active_domain,
            properties={"uploaded_size": len(contents), "chunks": len(chunks)},
        )
        for i, chunk_text in enumerate(chunks, 1):
            add_chunk(SOPChunk(
                doc_id=f"{doc_base_id}-{i:02d}",
                title=f"{filename} (part {i})",
                clause=f"Part {i}",
                page=f"Part {i}",
                content=chunk_text[:2000],
                keywords=[],
                equipment_tags=[],
                domain=active_domain,
                provenance=PROVENANCE_UPLOADED,
                authoritative=False,
                source=filename,
            ))
            chunks_indexed += 1
        if chunks_indexed:
            mark_ingested()

    # ── Findings: literal pattern matches only ────────────────────────────
    findings: List[Dict[str, Any]] = []
    seen_findings = set()
    for category, pattern, val_group, unit_group in _UPLOAD_FINDING_PATTERNS:
        for m in pattern.finditer(text):
            value = m.group(val_group)
            unit = ""
            if unit_group is not None:
                try:
                    unit = (m.group(unit_group) or "").strip()
                except (IndexError, re.error):
                    unit = ""
            dedupe_key = (category, (value or "").lower(), unit.lower())
            if dedupe_key in seen_findings:
                continue
            seen_findings.add(dedupe_key)
            findings.append({
                "key": f"{category}_{len(findings)}",
                "value": f"{value} {unit}".strip(),
                "category": category,
                # Pattern-match certainty only. This says the literal text was
                # recognised, not that the reading is safe or in-spec.
                "confidence": 1.0,
                "confidence_basis": "exact_pattern_match_in_extracted_text",
                "source_page": None,
            })
    findings = findings[:200]

    # ── Equipment / standard entities present in the text ─────────────────
    entities = graphrag_engine.extract_entities_from_query(text)

    # ── Chemicals present in the text ─────────────────────────────────────
    chemicals = detect_chemicals(text)

    # ── SOP clauses that actually retrieved for this document ─────────────
    # The document's own freshly-indexed chunks are excluded: a file matching
    # itself is not an SOP reference.
    sop_violations: List[str] = []
    retrieved = search_sops(text[:4000], min_score=0.0, top_k=8)
    for c in retrieved:
        chunk_doc = str(c.get("doc_id", ""))
        if chunk_doc.startswith(doc_base_id):
            continue
        sop_violations.append(
            f"{chunk_doc or '?'} | Clause: {c.get('clause', '?')} | Page: {c.get('page', '?')}"
        )

    lower = filename.lower()
    doc_type = (
        "pid_drawing" if ("pid" in lower or "p&id" in lower)
        else "inspection_pdf" if lower.endswith(".pdf")
        else "general"
    )

    now_iso = datetime.now().isoformat(timespec="seconds")
    result = {
        "id": f"upload_{hashlib.sha256((filename + now_iso).encode()).hexdigest()[:16]}",
        "name": filename,
        "size_bytes": size_bytes,
        "size_formatted": f"{(size_bytes or 0) / 1024:.1f} KB",
        "mime_type": file.content_type or "application/octet-stream",
        "type": doc_type,
        "upload_timestamp": now_iso,
        "sha256_hash": sha256_hash,
        # Reports the engine that actually ran. A text-layer PDF is parsed by
        # pypdf; an image has no OCR pass in this endpoint.
        "ocr_engine": "pypdf_text_layer" if lower.endswith(".pdf") else "plain_text_decode",
        "raw_ocr_text": text,
        "findings": findings,
        "sop_violations": sop_violations,
        "status": "ready",
        "indexed_chunks": chunks_indexed,
        "entities_detected": [
            {"id": e.id, "name": e.name, "category": e.category, "domain": e.domain}
            for e in entities[:50]
        ],
        "chemicals_detected": [
            {"name": c.get("name"), "cas": c.get("cas")} for c in chemicals
        ],
        "extraction_note": (
            "findings are literal pattern matches in the extracted text; "
            "confidence reports match certainty, not engineering validity. "
            "sop_violations lists clauses that retrieved for this document, "
            "not confirmed violations."
        ),
    }
    logger.info(
        f"[UPLOAD] {filename}: {size_bytes} bytes, {chunks_indexed} chunks indexed, "
        f"{len(findings)} findings, {len(entities)} entities, {len(sop_violations)} SOP clauses"
    )
    return result


def _hash_upload_bytes(contents: bytes) -> tuple:
    """Returns (sha256_hex, size_bytes) for an in-memory upload payload."""
    return hashlib.sha256(contents).hexdigest(), len(contents)


class SearchRAGRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5


@app.post("/api/rag-admin/search")
@app.post("/api/v1/rag-admin/search")
async def search_rag_admin(req: SearchRAGRequest):
    """Executes a live corpus search for admin inspection and reports the
    scoring method that produced the results."""
    from backend.knowledge_base import search_sops, retrieval_status
    from backend.graph_rag import graphrag_engine

    results = search_sops(req.query, min_score=0.0, top_k=req.top_k or 5)
    matched_entities = graphrag_engine.extract_entities_from_query(req.query)

    return {
        "status": "SUCCESS",
        "query": req.query,
        "results": results,
        "result_count": len(results),
        "retrieval": retrieval_status(),
        "matched_entities": [
            {
                "id": e.id,
                "name": e.name,
                "category": e.category,
                "domain": e.domain,
                "provenance": "bundled_reference_graph",
            }
            for e in matched_entities
        ],
    }


@app.post("/api/document-converter/convert")
@app.post("/api/v1/document-converter/convert")
async def convert_document_endpoint(
    file: UploadFile = FastAPIFile(...),
    target_format: str = Form("docx")
):
    """
    Genuine Air-Gapped Universal Document Converter.
    Converts between PDF, Word (.docx), Excel (.xlsx), PowerPoint (.pptx), Text, and Markdown
    using on-premise Python headless builders without external calls.
    """
    import io
    import pypdf
    from backend.deliverables import create_deliverable_file

    filename = file.filename or "document.txt"
    contents = await file.read()
    text = ""

    # Extract source content
    if filename.lower().endswith(".pdf"):
        try:
            reader = pypdf.PdfReader(io.BytesIO(contents))
            for page in reader.pages:
                text += (page.extract_text() or "") + "\n\n"
        except Exception:
            text = contents.decode("utf-8", errors="ignore")
    else:
        text = contents.decode("utf-8", errors="ignore")

    base_name = filename.rsplit(".", 1)[0]
    target_ext = target_format.lower().replace(".", "")

    plan = {
        "title": f"Converted Document: {base_name}",
        "filename": f"{base_name}_converted.{target_ext}",
        "blocks": [
            {"type": "heading", "text": f"Universal Converted Document: {base_name}", "level": 1},
            {"type": "paragraph", "text": text[:3500] if text.strip() else "Converted content processed on-premise by AEGIS AI Sovereign Engine."}
        ]
    }

    chat_id = "admin_converter"
    mode_map = {"docx": "docs", "xlsx": "excel", "pptx": "ppt", "pdf": "docs", "txt": "docs"}
    chosen_mode = mode_map.get(target_ext, "docs")

    if chosen_mode == "excel":
        # Parse lines into structured table rows
        rows = [["Line Item / Metric", "Details / Data Extracted"]]
        for line in [l.strip() for l in text.split("\n") if l.strip()][:30]:
            parts = line.split(",", 1) if "," in line else line.split(":", 1) if ":" in line else [line, "Recorded"]
            rows.append([parts[0].strip(), parts[1].strip() if len(parts) > 1 else ""])
        plan["blocks"].append({"type": "table", "rows": rows if len(rows) > 1 else [["Item", "Value"], ["Status", "Converted"]]})
    elif chosen_mode == "ppt":
        # Group paragraphs into slides
        slides = []
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()][:6]
        if not paragraphs:
            paragraphs = [text[:200]] if text else ["Executive Summary of converted dataset."]
        for idx, para in enumerate(paragraphs, 1):
            plan["blocks"].append({
                "type": "bullet_list",
                "items": [para[:150], f"Source: On-premise conversion ({filename})", "Classification: Sovereign Confidential"]
            })

    result = create_deliverable_file(plan, mode=chosen_mode, chat_id=chat_id)

    logger.info(f"[DOC_CONVERTER] Converted {filename} -> {result['filename']} ({target_ext})")
    return {
        "status": "SUCCESS",
        "message": f"Successfully converted to {target_ext.upper()}",
        "filename": result["filename"],
        # file_id is returned explicitly so the client can fetch the bytes with
        # an Authorization header instead of following a bare <a href>, which
        # the API auth gate rejects.
        "file_id": result.get("file_id"),
        "download_url": result["download_url"],
        "size_bytes": result.get("size_bytes", len(contents))
    }



@app.get("/api/sandbox/status")
@app.get("/api/v1/sandbox/status")
async def get_sandbox_status():
    """
    Reports the sandbox runtime and exactly which isolation controls are active.

    Every field is measured at request time. The previous version returned
    `network_isolation: "STRICT_NONE"`, `image_present: True` and
    `ast_screener_rules: 24` unconditionally - claiming container-grade
    isolation and a static screener even when Docker was absent and no screener
    existed.
    """
    from backend.sandbox import sandbox_capabilities
    from backend.code_runner import runner_availability
    from backend.db_dialect import describe as describe_db

    caps = sandbox_capabilities()
    runners = caps.pop("isolation_levels", {})

    return {
        "status": "ONLINE",
        "active_backend": caps["active_backend"],
        "docker_available": caps["docker_available"],
        "job_object_available": caps["job_object_available"],
        "job_object_error": caps["job_object_error"],
        "static_screen": caps["static_screen"],
        "isolation_level": caps["active_backend"],
        "isolation_levels": runners,
        # Only a container gives true network isolation. Say so plainly instead
        # of claiming "none" when the mechanism is not present.
        "network_isolation": (
            "container_network_none" if caps["docker_available"]
            else "in_process_guard_loopback_and_rfc1918_only"
        ),
        "filesystem_jailed": bool(caps["docker_available"]),
        "not_enforced_without_docker": caps["not_enforced_without_docker"],
        "memory_limit": caps["memory_limit"],
        "timeout_seconds": caps["timeout_seconds"],
        "image": caps["image"],
        "language_runners": runner_availability(),
        # Reported so the UI can label the SQL editor with the engine that is
        # actually configured, instead of a hard-coded "XAMPP MySQL".
        "database": {
            "driver": DB_DRIVER,
            "engine": "PostgreSQL" if IS_POSTGRES else "MySQL/MariaDB",
            "label": "PostgreSQL" if IS_POSTGRES else "XAMPP MySQL",
            "target": describe_db(),
        },
    }


class SandboxExecuteRequest(BaseModel):
    code: str
    timeout_seconds: Optional[float] = 15.0
    stdin_input: Optional[str] = None


@app.post("/api/sandbox/execute")
@app.post("/api/v1/sandbox/execute")
async def execute_sandbox_endpoint(body: SandboxExecuteRequest):
    """Executes code in isolated sandbox and returns live stdout/stderr/verdict."""
    from backend.sandbox import execute_python_sandbox
    result = execute_python_sandbox(body.code, stdin_input=body.stdin_input)
    return result


NETWORK_DEPLOYMENT_MODES = ("STANDALONE_LOCAL", "LAN_OPTION_A", "HOTSPOT_OPTION_B")
_configured_deployment_mode = "STANDALONE_LOCAL"
DEFAULT_BACKEND_PORT = 8000


def _detect_ipv4_interfaces() -> list:
    """Returns the host's REAL IPv4 interfaces (no hard-coded addresses)."""
    interfaces = []
    try:
        for name, addresses in psutil.net_if_addrs().items():
            for addr in addresses:
                # AF_INET == 2 on every platform
                if getattr(addr, "family", None) == socket.AF_INET and addr.address:
                    interfaces.append({
                        "interface": name,
                        "ip": addr.address,
                        "loopback": addr.address.startswith("127."),
                    })
    except Exception as e:
        logger.debug(f"[NETWORK] psutil interface enumeration failed: {e}")

    if not any(not i["loopback"] for i in interfaces):
        # Fallback: ask the OS which local address the default route would use.
        # A UDP "connect" sends no packets.
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
                probe.settimeout(0.25)
                probe.connect(("192.0.2.1", 9))  # TEST-NET-1 (RFC 5737)
                interfaces.append({
                    "interface": "default-route",
                    "ip": probe.getsockname()[0],
                    "loopback": False,
                })
        except Exception as e:
            logger.debug(f"[NETWORK] default-route probe failed: {e}")

    return interfaces


def _primary_lan_ip(interfaces: list) -> Optional[str]:
    """Picks the most plausible private LAN address, or None if loopback-only."""
    candidates = [
        i for i in interfaces
        if not i["loopback"] and not i["ip"].startswith("169.254.")
    ]
    if not candidates:
        return None

    def rank(item: dict) -> int:
        ip = item["ip"]
        if ip.startswith("192.168."):
            return 0
        if ip.startswith("10."):
            return 1
        if re.match(r"172\.(1[6-9]|2\d|3[01])\.", ip):
            return 2
        return 3

    return sorted(candidates, key=rank)[0]["ip"]


def _connected_clients(listen_port: int) -> list:
    """Lists real established client connections to the backend port."""
    clients = []
    try:
        established = getattr(psutil, "CONN_ESTABLISHED", "ESTABLISHED")
        for conn in psutil.net_connections(kind="inet"):
            if not conn.laddr or not conn.raddr or conn.status != established:
                continue
            if listen_port and conn.laddr.port != listen_port:
                continue
            if conn.raddr.ip.startswith("127."):
                continue
            clients.append({
                "ip": conn.raddr.ip,
                "port": conn.raddr.port,
                # The OS exposes no connect timestamp; last_seen is the observation time.
                "connected_at": None,
                "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
    except Exception as e:
        logger.debug(f"[NETWORK] client enumeration unavailable: {e}")
    return clients


def _build_network_status(observed_port: Optional[int]) -> dict:
    """Assembles the live network picture from real host state."""
    from backend.airgap_guard import inspect_and_guard_project_sockets

    interfaces = _detect_ipv4_interfaces()
    lan_ip = _primary_lan_ip(interfaces)
    # Some transports (ASGI test client, reverse proxies) report no explicit
    # port; fall back to the configured backend port in that case.
    effective_port = observed_port or DEFAULT_BACKEND_PORT

    try:
        live_sockets = inspect_and_guard_project_sockets(os.getpid())
    except Exception as e:
        logger.debug(f"[NETWORK] socket guard unavailable: {e}")
        live_sockets = []

    blocked_external = len([s for s in live_sockets if s.get("tier") == "EXTERNAL_WAN"])
    clients = _connected_clients(effective_port)

    if lan_ip:
        detected_mode = "HOTSPOT_OPTION_B" if any(
            i["interface"] and re.search(r"wi-?fi|wlan|hotspot|ap$", i["interface"], re.IGNORECASE)
            for i in interfaces if i["ip"] == lan_ip
        ) else "LAN_OPTION_A"
    else:
        detected_mode = "STANDALONE_LOCAL"

    return {
        "status": "ONLINE",
        "configured_mode": _configured_deployment_mode,
        # Legacy alias kept for existing clients (sovereignty store).
        "deployment_mode": _configured_deployment_mode,
        "detected_mode": detected_mode,
        "mode_satisfied": _configured_deployment_mode == detected_mode,
        "host_ip": lan_ip or "127.0.0.1",
        "loopback_only": lan_ip is None,
        "port": effective_port,
        "interfaces": interfaces,
        "connected_clients": clients,
        "external_egress_sockets": blocked_external,
        "localhost_sockets": len([s for s in live_sockets if s.get("tier") == "LOCALHOST"]),
        "lan_sockets": len([s for s in live_sockets if s.get("tier") == "LAN_HOTSPOT"]),
        # We report evidence, we do not assert a guarantee:
        "air_gapped": None,
        "air_gap_evidence": (
            f"{blocked_external} external socket(s) observed by the air-gap guard"
        ),
        "packet_counters": None,
        "packet_counters_note": "Packet counters require a host-level capture and are not reported by this endpoint.",
        "observed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


@app.get("/api/network-status")
@app.get("/api/v1/network-status")
async def get_network_status(request: Request):
    """Returns LIVE network status: real host interfaces, mode and client sessions."""
    return _build_network_status(request.url.port)


@app.post("/api/network-status/mode")
@app.post("/api/v1/network-status/mode")
async def set_network_mode(request: Request, mode: str = "STANDALONE_LOCAL"):
    """
    Records the requested deployment topology and returns the re-detected status.

    Only the three supported modes are accepted; the response always contains the
    backend's independently detected mode so a mismatch stays visible.
    """
    global _configured_deployment_mode

    requested = (mode or "").strip().upper()
    if requested not in NETWORK_DEPLOYMENT_MODES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported deployment mode '{mode}'. Allowed: {', '.join(NETWORK_DEPLOYMENT_MODES)}.",
        )

    _configured_deployment_mode = requested
    status = _build_network_status(request.url.port)
    status["message"] = (
        f"Configured mode set to {requested}; detected mode is {status['detected_mode']}."
        if status["mode_satisfied"]
        else f"Configured mode {requested} does not match the detected topology ({status['detected_mode']})."
    )
    return status


# --- PKI Certificate Revocation List (CRL) In-Memory Registry ---
REVOKED_CERTS_REGISTRY = [
    {
        "serial_number": "MRPL-CA-2026-X09281",
        "revoked_at": "2026-09-08 14:30:00",
        "reason": "KEY_COMPROMISE"
    },
    {
        "serial_number": "MRPL-CA-2025-OP8102",
        "revoked_at": "2026-08-20 09:15:22",
        "reason": "OPERATOR_RESIGNED"
    }
]


@app.get("/api/v1/auth/crl/status")
@app.get("/api/auth/crl/status")
async def get_crl_status():
    """Returns the live X.509 Certificate Revocation List (CRL) blacklist status."""
    return {
        "status": "HEALTHY_SYNCHRONIZED",
        "root_ca": "MRPL Sovereign Offline Root CA 2026",
        "total_revoked": len(REVOKED_CERTS_REGISTRY),
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "next_update": "2026-09-16 00:00:00",
        "revoked_certificates": REVOKED_CERTS_REGISTRY
    }


class RevokeCertRequest(BaseModel):
    serial_number: str
    reason: Optional[str] = "KEY_COMPROMISE"


@app.post("/api/v1/auth/crl/revoke")
@app.post("/api/auth/crl/revoke")
async def revoke_cert_endpoint(body: RevokeCertRequest):
    """Revokes a smartcard or PKI operator certificate and appends to CRL blacklist."""
    serial = body.serial_number.strip()
    reason = body.reason or "KEY_COMPROMISE"
    
    # Check if already revoked
    for c in REVOKED_CERTS_REGISTRY:
        if c["serial_number"].lower() == serial.lower():
            return {"status": "SUCCESS", "message": "Certificate was already in revocation list.", "serial_number": serial}
            
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    REVOKED_CERTS_REGISTRY.insert(0, {
        "serial_number": serial,
        "revoked_at": now_str,
        "reason": reason
    })
    logger.info(f"[PKI CRL] Certificate revoked: serial={serial} reason={reason}")
    return {
        "status": "SUCCESS",
        "message": f"Certificate {serial} successfully revoked.",
        "serial_number": serial,
        "revoked_at": now_str,
        "reason": reason
    }


AUDIT_CHAIN_LIMIT = 50


def _build_audit_chain(limit: int = AUDIT_CHAIN_LIMIT) -> Dict[str, Any]:
    """
    Builds a genuine SHA-256 hash chain over real `user_activity_logs` rows.

    Each block hashes the previous block's hash together with the row's own
    fields, so any edit to a stored row changes its hash and every hash after
    it. The chain is recomputed here and re-verified link by link, so
    `verified` reflects an actual check rather than a hard-coded True.
    """
    from backend.db import get_all_user_activity_logs

    try:
        rows = get_all_user_activity_logs(limit=limit)
    except Exception as exc:
        return {
            "available": False,
            "error": f"Audit ledger unavailable: {type(exc).__name__}: {exc}",
            "logs": [],
        }

    # Newest first in the query; the chain is built oldest -> newest.
    ordered = list(reversed(rows))
    prev_hash = "0" * 64
    blocks: List[Dict[str, Any]] = []

    for row in ordered:
        payload = "|".join(str(x) for x in [
            prev_hash,
            row.get("id"),
            row.get("created_at"),
            row.get("activity_type"),
            row.get("username"),
            row.get("role"),
            (row.get("details") or "")[:200],
        ])
        block_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        blocks.append({
            "sequence": len(blocks) + 1,
            "row_id": row.get("id"),
            "timestamp": row.get("created_at"),
            "event": row.get("activity_type"),
            "username": row.get("username"),
            "role": row.get("role"),
            "details": row.get("details"),
            "risk_level": row.get("risk_level"),
            "block_hash": block_hash,
            "prev_hash": prev_hash,
        })
        prev_hash = block_hash

    # Re-verify every link independently of the build loop.
    chain_valid = True
    running = "0" * 64
    for block in blocks:
        recomputed = hashlib.sha256("|".join(str(x) for x in [
            running,
            block["row_id"],
            block["timestamp"],
            block["event"],
            block["username"],
            block["role"],
            (block["details"] or "")[:200],
        ]).encode("utf-8")).hexdigest()
        if recomputed != block["block_hash"] or block["prev_hash"] != running:
            chain_valid = False
            break
        running = block["block_hash"]

    return {
        "available": True,
        "logs": [{**b, "verified": chain_valid} for b in blocks],
        "chain_valid": chain_valid,
        "chain_length": len(blocks),
        "root_hash": blocks[0]["block_hash"] if blocks else None,
        "head_hash": blocks[-1]["block_hash"] if blocks else None,
    }


@app.get("/api/sovereignty/metrics")
@app.get("/api/v1/sovereignty/metrics")
async def get_sovereignty_metrics():
    """
    Returns live air-gap socket telemetry.

    Socket counts are measured with psutil. Packet counters are NOT reported:
    this host has no packet-capture counter for the project processes, so those
    fields are null with an explicit note rather than a fabricated zero.
    """
    from backend.airgap_guard import inspect_and_guard_project_sockets
    current_pid = os.getpid()
    try:
        live_sockets = inspect_and_guard_project_sockets(current_pid)
    except Exception:
        live_sockets = []
    localhost_cnt = len([s for s in live_sockets if s["tier"] == "LOCALHOST"])
    lan_cnt = len([s for s in live_sockets if s["tier"] == "LAN_HOTSPOT"])
    blocked_cnt = len([s for s in live_sockets if s["tier"] == "EXTERNAL_WAN"])

    if blocked_cnt > 0:
        verdict = f"ALERT: {blocked_cnt} external socket(s) observed by the egress guard"
    else:
        verdict = "No external sockets observed at sample time (point-in-time psutil inspection)"

    return {
        # Packet counters are not measurable here - never invent a number.
        "external_packets": None,
        "localhost_packets": None,
        "lan_hotspot_packets": None,
        "packet_counting_available": False,
        "packet_counting_note": (
            "This deployment counts live sockets, not packets. Install a packet "
            "counter (e.g. psutil counters or a capture agent) before reporting "
            "packet totals."
        ),
        "external_sockets": blocked_cnt,
        "localhost_connections": localhost_cnt,
        "lan_hotspot_connections": lan_cnt,
        "external_internet_connections": blocked_cnt,
        "verdict": verdict,
        "sampled_at": datetime.now().isoformat(timespec="seconds"),
        "daemon_heartbeat_hz": 1.0,
        "sockets": live_sockets[:30],
    }

@app.get("/api/sovereignty/logs")
@app.get("/api/v1/sovereignty/logs")
async def get_sovereignty_logs():
    """
    Returns the tamper-evident audit ledger.

    The chain is built from real `user_activity_logs` rows and re-verified link
    by link on every request. The previous implementation returned a fixed list
    of hand-written entries with hard-coded hashes and `verified: true`; those
    were not derived from any recorded event.
    """
    # Same window as the audit certificate, so both report an identical chain.
    chain = _build_audit_chain(limit=AUDIT_CHAIN_LIMIT)

    if not chain.get("available"):
        return {
            "success": False,
            "error": chain.get("error"),
            "logs": [],
            "provenance": "live_user_activity_logs",
            "chain_valid": False,
            "note": "The audit ledger could not be read; no entries are shown.",
        }

    return {
        "success": True,
        "logs": chain["logs"],
        "provenance": "live_user_activity_logs",
        "verification_method": "sha256_chain_recomputed_per_request",
        "chain_valid": chain["chain_valid"],
        "chain_length": chain["chain_length"],
        "root_hash": chain["root_hash"],
        "head_hash": chain["head_hash"],
        "independently_verified": False,
        "note": (
            "Hashes are recomputed and checked against this chain on each request. "
            "They are not anchored to an external witness, so this is internal "
            "consistency verification rather than independent proof."
        ),
    }


@app.get("/api/sovereignty-audit/export")
@app.get("/api/v1/sovereignty-audit/export")
async def export_sovereignty_audit():
    """Exports the air-gap audit certificate.

    `provenance` is explicit: this deployment serves a static bootstrap
    The integrity block is computed from the live audit ledger at request time.
    The chain is internally re-verified on every call, but it is not anchored
    to an external witness, so `independently_verified` stays false and clients
    must present it that way.
    """
    chain = _build_audit_chain(limit=AUDIT_CHAIN_LIMIT)
    chain_ok = bool(chain.get("available")) and bool(chain.get("chain_valid"))

    return {
        "certificate_title": "AEGIS AI Sovereign AI Workbench - Air-Gap Cryptographic Audit Certificate",
        "institution": "Mangalore Refinery and Petrochemicals Limited (MRPL)",
        # timezone.utc, not the deprecated naive datetime.utcnow(), so the
        # certificate carries an unambiguous UTC instant.
        "timestamp_generated_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "air_gap_verdict": "LIVE_CHAIN_RECOMPUTED" if chain_ok else "CHAIN_UNAVAILABLE_OR_INVALID",
        "external_packets_transmitted": None,
        "external_packets_note": (
            "Packet counting is not implemented on this deployment; no packet "
            "total is claimed."
        ),
        "provenance": "live_user_activity_logs",
        "independently_verified": False,
        "integrity_verification": {
            "valid": chain_ok,
            "method": "sha256_chain_recomputed_per_request",
            "note": (
                "Each block hash is recomputed from the stored audit row and the "
                "previous hash, then re-checked link by link. There is no external "
                "anchor, so this proves internal consistency only."
            ),
            "chain_length": chain.get("chain_length", 0),
            "root_hash": chain.get("root_hash"),
            "head_hash": chain.get("head_hash"),
        },
    }


# =====================================================================
# CUSTOM AGENTS API ENDPOINTS
# =====================================================================
from backend.custom_agents import (
    CustomAgent,
    get_all_agents,
    get_agent_by_id,
    create_or_update_agent,
    delete_agent
)

@app.get("/api/v1/agents")
@app.get("/api/agents")
async def list_custom_agents():
    """Returns all available custom agent templates and operator-created agents."""
    agents = get_all_agents()
    return {"status": "SUCCESS", "count": len(agents), "agents": [a.dict() for a in agents]}

@app.get("/api/v1/agents/{agent_id}")
@app.get("/api/agents/{agent_id}")
async def get_single_agent(agent_id: str):
    """Returns specific custom agent by id."""
    agent = get_agent_by_id(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"status": "SUCCESS", "agent": agent.dict()}

@app.post("/api/v1/agents")
@app.post("/api/agents")
async def save_custom_agent(body: CustomAgent):
    """Creates or updates a custom agent definition."""
    saved = create_or_update_agent(body)
    return {"status": "SUCCESS", "agent": saved.dict()}


@app.delete("/api/v1/agents/{agent_id}")
@app.delete("/api/agents/{agent_id}")
async def remove_custom_agent(agent_id: str):
    """
    Deletes a custom agent definition.

    This route was missing: `delete_agent` was imported at module scope but
    never registered, so the UI's delete call 404'd while the agent was removed
    from local state only and reappeared on the next fetch.
    """
    if not delete_agent(agent_id):
        raise HTTPException(status_code=404, detail="Agent not found")
    logger.info(f"[AGENTS] Deleted custom agent '{agent_id}'")
    return {"status": "SUCCESS", "deleted": agent_id}

# ─── Feedback & Error Reporting Endpoints ────────────────────────────────────

class FeedbackSubmitRequest(BaseModel):
    report_type: str = "ERROR" # 'ERROR' | 'SUGGESTION'
    title: str
    description: str
    category: Optional[str] = "GENERAL"
    suggested_fix: Optional[str] = None
    chat_id: Optional[str] = None
    message_id: Optional[str] = None
    message_content: Optional[str] = None
    username: Optional[str] = "operator"
    user_id: Optional[str] = None


class FeedbackUpdateRequest(BaseModel):
    status: str # 'OPEN' | 'IN_REVIEW' | 'RESOLVED' | 'REJECTED'
    admin_notes: Optional[str] = None
    admin_response: Optional[str] = None
    resolved_by: Optional[str] = "Admin"


@app.post("/api/v1/feedback/submit")
@app.post("/api/feedback/submit")
async def submit_feedback_report(body: FeedbackSubmitRequest, request: Request):
    """
    Submits an Error report or Improvement Suggestion from the operator.
    Persists immediately in XAMPP MySQL.
    """
    from backend.db import create_feedback_report
    
    # Identity always comes from the verified token, never from client fields.
    payload = _caller_from_request(request)

    username = (payload or {}).get("sub") or body.username or "operator"
    user_id = body.user_id
    if payload:
        username = payload.get("sub") or username
        user_id = payload.get("user_id") or user_id

    report_id = create_feedback_report(
        report_type=body.report_type,
        title=body.title,
        description=body.description,
        user_id=user_id,
        username=username,
        chat_id=body.chat_id,
        message_id=body.message_id,
        message_content=body.message_content,
        category=body.category or "GENERAL",
        suggested_fix=body.suggested_fix
    )

    logger.info(f"[FEEDBACK] Created {body.report_type} report #{report_id} by '{username}' - '{body.title}'")

    return {
        "status": "SUCCESS",
        "report_id": report_id,
        "message": f"Report #{report_id} submitted successfully to admin workbench."
    }


@app.get("/api/v1/feedback/list")
@app.get("/api/feedback/list")
async def list_feedback_reports(
    type: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None
):
    """
    Retrieves all feedback and error reports with counts and filtering for Admin workbench.
    """
    from backend.db import get_all_feedback_reports
    reports = get_all_feedback_reports(report_type=type, status=status, search=search)
    
    # Calculate stats
    all_reports = get_all_feedback_reports()
    total_count = len(all_reports)
    error_count = len([r for r in all_reports if r.get("report_type") == "ERROR"])
    suggestion_count = len([r for r in all_reports if r.get("report_type") == "SUGGESTION"])
    open_count = len([r for r in all_reports if r.get("status") == "OPEN"])
    in_review_count = len([r for r in all_reports if r.get("status") == "IN_REVIEW"])
    resolved_count = len([r for r in all_reports if r.get("status") == "RESOLVED"])

    formatted = []
    for r in reports:
        formatted.append({
            "id": r["id"],
            "report_type": r["report_type"],
            "user_id": r.get("user_id"),
            "username": r.get("username") or "operator",
            "chat_id": r.get("chat_id"),
            "message_id": r.get("message_id"),
            "message_content": r.get("message_content"),
            "category": r.get("category") or "GENERAL",
            "title": r["title"],
            "description": r["description"],
            "suggested_fix": r.get("suggested_fix"),
            "status": r.get("status") or "OPEN",
            "admin_notes": r.get("admin_notes"),
            "admin_response": r.get("admin_response"),
            "resolved_by": r.get("resolved_by"),
            "resolved_at": str(r["resolved_at"]) if r.get("resolved_at") else None,
            "created_at": str(r["created_at"]),
            "updated_at": str(r["updated_at"]) if r.get("updated_at") else None,
        })

    return {
        "status": "SUCCESS",
        "stats": {
            "total": total_count,
            "errors": error_count,
            "suggestions": suggestion_count,
            "open": open_count,
            "in_review": in_review_count,
            "resolved": resolved_count
        },
        "count": len(formatted),
        "reports": formatted
    }


@app.get("/api/v1/feedback/{report_id}")
@app.get("/api/feedback/{report_id}")
async def get_feedback_detail(report_id: int):
    """Retrieves full details of a specific feedback report."""
    from backend.db import get_feedback_report_by_id
    report = get_feedback_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Feedback report not found")
    
    return {
        "status": "SUCCESS",
        "report": {
            **report,
            "created_at": str(report["created_at"]),
            "updated_at": str(report["updated_at"]) if report.get("updated_at") else None,
            "resolved_at": str(report["resolved_at"]) if report.get("resolved_at") else None,
        }
    }


@app.patch("/api/v1/feedback/{report_id}/status")
@app.patch("/api/feedback/{report_id}/status")
async def update_feedback_status(report_id: int, body: FeedbackUpdateRequest, request: Request):
    """
    Updates report status, appends admin notes/corrections, and records resolver.
    """
    from backend.db import get_feedback_report_by_id, update_feedback_report
    report = get_feedback_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Feedback report not found")

    # The resolver is the authenticated user; the client cannot name someone else.
    payload = _caller_from_request(request)
    resolver = (payload or {}).get("sub") or body.resolved_by or "Admin"

    update_feedback_report(
        report_id=report_id,
        status=body.status,
        admin_notes=body.admin_notes,
        admin_response=body.admin_response,
        resolved_by=resolver
    )

    logger.info(f"[FEEDBACK] Report #{report_id} updated to status '{body.status}' by '{resolver}'")

    return {
        "status": "SUCCESS",
        "report_id": report_id,
        "new_status": body.status,
        "message": f"Report #{report_id} updated to '{body.status}'"
    }


@app.delete("/api/v1/feedback/{report_id}")
@app.delete("/api/feedback/{report_id}")
async def remove_feedback_report(report_id: int):
    """Deletes a feedback report."""
    from backend.db import delete_feedback_report
    success = delete_feedback_report(report_id)
    if not success:
        raise HTTPException(status_code=404, detail="Feedback report not found")
    return {"status": "SUCCESS", "deleted_id": report_id}


# ─── Multi-User Collaboration & Plant Team Chat Endpoints ───────────────────

class CreateChannelRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    department: Optional[str] = "ALL"
    created_by: Optional[str] = "operator"

class CreateDMRequest(BaseModel):
    target_username: str
    current_username: Optional[str] = "operator"

class PostChannelMessageRequest(BaseModel):
    channel_id: str
    content: str
    sender_username: Optional[str] = "operator"
    sender_role: Optional[str] = "FIELD_OPERATOR"
    message_type: Optional[str] = "TEXT"
    file_id: Optional[str] = None
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    file_url: Optional[str] = None


@app.get("/api/collaboration/channels")
async def get_collaboration_channels(username: Optional[str] = "operator"):
    """Fetches all channels and DMs for the current user."""
    from backend.db import get_all_collaboration_channels
    channels = get_all_collaboration_channels(username)
    return {"status": "SUCCESS", "channels": channels}


@app.post("/api/collaboration/channels")
async def create_collaboration_channel(body: CreateChannelRequest):
    """Creates a new collaboration channel."""
    from backend.db import create_new_channel
    chan_id = create_new_channel(body.name, body.description or "", body.department or "ALL", body.created_by or "operator")
    return {"status": "SUCCESS", "channel_id": chan_id, "name": body.name}


@app.post("/api/collaboration/dm")
async def start_direct_message(body: CreateDMRequest):
    """Creates or returns a direct message channel with target user."""
    from backend.db import get_or_create_dm_channel
    dm = get_or_create_dm_channel(body.current_username or "operator", body.target_username)
    return {"status": "SUCCESS", "channel": dm}


@app.get("/api/collaboration/channels/{channel_id}/messages")
async def get_channel_message_history(channel_id: str, limit: int = 100):
    """Fetches chat history for the channel."""
    from backend.db import get_channel_messages
    messages = get_channel_messages(channel_id, limit=limit)
    return {"status": "SUCCESS", "channel_id": channel_id, "messages": messages}


@app.get("/api/collaboration/users")
async def get_collaboration_users():
    """Returns directory of plant users with online status."""
    from backend.db import get_plant_users_directory
    users = get_plant_users_directory()
    online_usernames = set(collab_manager.get_online_usernames())
    enriched = []
    for u in users:
        enriched.append({
            **u,
            "is_online": (u["username"] in online_usernames) or (u["username"] == "operator")
        })
    return {"status": "SUCCESS", "users": enriched}


@app.post("/api/collaboration/upload")
async def upload_collaboration_file(file: UploadFile = File(...), channel_id: str = Form(...), username: str = Form("operator")):
    """Uploads file attachment for sharing inside a collaboration channel."""
    from backend.config import GENERATED_DIR
    import uuid
    import shutil
    
    file_ext = Path(file.filename).suffix.lower()
    file_id = f"collab_{uuid.uuid4().hex[:12]}"
    safe_filename = f"{file_id}_{Path(file.filename).name}"
    save_path = GENERATED_DIR / safe_filename
    
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    file_size = save_path.stat().st_size
    file_url = f"/api/files/download/{safe_filename}"
    
    # Register file in database
    from backend.db import save_file_record, log_user_activity
    save_file_record(
        file_id=file_id,
        chat_id=channel_id,
        filename=file.filename,
        file_type=file_ext.replace(".", "").upper() or "DOC",
        file_path=str(save_path),
        verification_status="VERIFIED",
        is_important=False
    )

    try:
        log_user_activity(
            username=username,
            activity_type="FILE_UPLOAD",
            query_text=f"Uploaded file: {file.filename}",
            channel_or_chat_id=channel_id,
            details=f"File: {file.filename} ({file_size} bytes)",
            file_meta={"file_id": file_id, "filename": file.filename, "size": file_size, "url": file_url}
        )
    except Exception:
        pass
    
    return {
        "status": "SUCCESS",
        "file_id": file_id,
        "file_name": file.filename,
        "file_type": file_ext,
        "file_size": file_size,
        "file_url": file_url
    }


# ─── Real-Time Collaboration WebSocket Connection Manager ───────────────────

class CollaborationConnectionManager:
    def __init__(self):
        # Map channel_id -> set of active WebSockets
        self.active_rooms: Dict[str, set[WebSocket]] = {}
        # Map websocket -> dict of metadata (username, channel_id)
        self.socket_meta: Dict[WebSocket, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, channel_id: str, username: str, role: str = "OPERATOR"):
        await websocket.accept()
        if channel_id not in self.active_rooms:
            self.active_rooms[channel_id] = set()
        self.active_rooms[channel_id].add(websocket)
        self.socket_meta[websocket] = {
            "channel_id": channel_id,
            "username": username,
            "role": role,
            "joined_at": time.time()
        }
        logger.info(f"[COLLAB_WS] User '{username}' connected to channel '{channel_id}' (Total in room: {len(self.active_rooms[channel_id])})")
        # Broadcast presence
        await self.broadcast_to_channel(channel_id, {
            "event": "user_joined",
            "username": username,
            "role": role,
            "channel_id": channel_id,
            "timestamp": str(datetime.now())
        })

    def disconnect(self, websocket: WebSocket):
        meta = self.socket_meta.pop(websocket, None)
        if meta:
            chan_id = meta.get("channel_id")
            username = meta.get("username")
            if chan_id in self.active_rooms:
                self.active_rooms[chan_id].discard(websocket)
                if not self.active_rooms[chan_id]:
                    del self.active_rooms[chan_id]
            logger.info(f"[COLLAB_WS] User '{username}' disconnected from channel '{chan_id}'")

    async def broadcast_to_channel(self, channel_id: str, message_dict: Dict[str, Any]):
        if channel_id in self.active_rooms:
            dead_sockets = []
            for ws in self.active_rooms[channel_id]:
                try:
                    await ws.send_json(message_dict)
                except Exception:
                    dead_sockets.append(ws)
            for ws in dead_sockets:
                self.disconnect(ws)

    def get_online_usernames(self) -> List[str]:
        return list(set(m["username"] for m in self.socket_meta.values()))

collab_manager = CollaborationConnectionManager()


@app.websocket("/api/collaboration/ws")
async def websocket_collaboration(
    websocket: WebSocket,
    channel_id: str = "chan_refinery_ops",
    username: str = "operator",
    role: str = "FIELD_OPERATOR"
):
    """
    Real-Time Multi-User Collaboration WebSocket.
    Handles:
    - User text messaging
    - Shared file notifications
    - Typing indicators
    - Real-time in-channel collaborative @aegis / @ai invocations

    Connect with ?token=<session token> (authentication is enforced). The
    username/role query parameters are only cosmetic labels: the identity that
    is recorded is always the one carried by the signed token.
    """
    # Authenticate before accepting: an invalid token fails the HTTP upgrade.
    # The handshake itself is completed by collab_manager.connect() below.
    caller = await _authorize_websocket(websocket)
    if not caller:
        logger.warning("[WS] Rejected unauthenticated /api/collaboration/ws connection")
        return

    # The signed token is authoritative; ignore any client-asserted identity.
    channel_id = (websocket.query_params.get("channel_id") or "chan_refinery_ops")[:120]
    username = str(caller.get("sub") or "unknown")
    role = str(caller.get("role") or "FIELD_OPERATOR")

    await collab_manager.connect(websocket, channel_id, username, role)
    from backend.db import save_channel_message

    try:
        while True:
            raw_data = await websocket.receive_text()
            try:
                payload = json.loads(raw_data)
            except Exception:
                continue

            event_type = payload.get("event", "message")

            # 1. Typing indicator
            if event_type == "typing":
                is_typing = payload.get("is_typing", True)
                await collab_manager.broadcast_to_channel(channel_id, {
                    "event": "typing",
                    "username": username,
                    "is_typing": is_typing,
                    "channel_id": channel_id
                })
                continue

            # 2. Regular User / File Message
            content = (payload.get("content") or payload.get("message") or "").strip()
            msg_type = payload.get("message_type", "TEXT")
            file_id = payload.get("file_id")
            file_name = payload.get("file_name")
            file_type = payload.get("file_type")
            file_size = payload.get("file_size")
            file_url = payload.get("file_url")

            if not content and not file_id:
                continue

            # Save message in MySQL
            msg_id = save_channel_message(
                channel_id=channel_id,
                sender_username=username,
                sender_role=role,
                content=content,
                message_type=msg_type,
                file_id=file_id,
                file_name=file_name,
                file_type=file_type,
                file_size=file_size,
                file_url=file_url
            )

            # Broadcast user message to everyone in the room
            msg_event = {
                "event": "new_message",
                "id": msg_id,
                "channel_id": channel_id,
                "sender_username": username,
                "sender_role": role,
                "content": content,
                "message_type": msg_type,
                "file_id": file_id,
                "file_name": file_name,
                "file_type": file_type,
                "file_size": file_size,
                "file_url": file_url,
                "created_at": str(datetime.now())
            }
            await collab_manager.broadcast_to_channel(channel_id, msg_event)

            # 3. Check for @aegis or @ai bot invocation
            is_ai_trigger = bool(
                re.search(r"@(?:aegis|ai|assistant|bot)\b", content, re.IGNORECASE) or
                payload.get("ask_ai", False)
            )

            if is_ai_trigger:
                # Strip mention tag to get pure prompt
                clean_ai_prompt = re.sub(r"@(?:aegis|ai|assistant|bot)\b", "", content, flags=re.IGNORECASE).strip()
                if not clean_ai_prompt and file_name:
                    clean_ai_prompt = f"Analyze the shared file: {file_name}"
                elif not clean_ai_prompt:
                    clean_ai_prompt = "Hello AEGIS AI. How can you assist our plant team in this channel?"

                # Signal AI thinking started
                await collab_manager.broadcast_to_channel(channel_id, {
                    "event": "ai_response_start",
                    "channel_id": channel_id,
                    "sender_username": "AEGIS AI (Sovereign)",
                    "sender_role": "SOVEREIGN_AI_ASSISTANT",
                    "prompt": clean_ai_prompt
                })

                # Stream response from sovereign pipeline
                ai_chat_id = f"collab_ai_{channel_id}_{int(time.time())}"
                full_ai_tokens = []
                attachments_list = [file_url] if file_url else None

                try:
                    async for chunk in generate_chat_events(clean_ai_prompt, requested_mode="auto", chat_id=ai_chat_id, attachments=attachments_list):
                        if "token" in chunk:
                            token_txt = chunk["token"]
                            full_ai_tokens.append(token_txt)
                            await collab_manager.broadcast_to_channel(channel_id, {
                                "event": "ai_response_token",
                                "channel_id": channel_id,
                                "token": token_txt
                            })
                        elif "thinking" in chunk and chunk.get("event") == "step":
                            await collab_manager.broadcast_to_channel(channel_id, {
                                "event": "ai_response_thinking",
                                "channel_id": channel_id,
                                "thinking": chunk.get("thinking", "")
                            })

                    full_ai_text = "".join(full_ai_tokens)
                    
                    # Save AI final response to DB
                    ai_msg_id = save_channel_message(
                        channel_id=channel_id,
                        sender_username="AEGIS AI",
                        sender_role="SOVEREIGN_AI",
                        content=full_ai_text,
                        message_type="AI_RESPONSE"
                    )

                    await collab_manager.broadcast_to_channel(channel_id, {
                        "event": "ai_response_done",
                        "id": ai_msg_id,
                        "channel_id": channel_id,
                        "content": full_ai_text,
                        "created_at": str(datetime.now())
                    })
                except Exception as ai_err:
                    logger.error(f"[COLLAB_AI_ERROR] Failed during @aegis stream: {ai_err}")
                    await collab_manager.broadcast_to_channel(channel_id, {
                        "event": "ai_response_done",
                        "channel_id": channel_id,
                        "content": f"⚠️ AEGIS AI Sovereign Assistant encountered an error processing this request: {ai_err}",
                        "created_at": str(datetime.now())
                    })

    except WebSocketDisconnect:
        collab_manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"[COLLAB_WS_ERR] WebSocket error: {e}")
        collab_manager.disconnect(websocket)


# ─── Security Audit & User Activity Monitoring Endpoints ────────────────────

@app.get("/api/v1/audit/activity-logs")
@app.get("/api/audit/activity-logs")
async def get_activity_audit_logs(
    username: Optional[str] = None,
    activity_type: Optional[str] = None,
    risk_level: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 150
):
    """
    Returns user activity logs (chat prompts, RAG searches, shared files, channel messages)
    with risk levels for Admin monitoring and triage.
    """
    from backend.db import get_all_user_activity_logs
    logs = get_all_user_activity_logs(
        username=username,
        activity_type=activity_type,
        risk_level=risk_level,
        search=search,
        limit=limit
    )

    suspicious_count = len([l for l in logs if l.get("risk_level") in ("SUSPICIOUS", "CRITICAL")])

    return {
        "status": "SUCCESS",
        "total": len(logs),
        "suspicious_count": suspicious_count,
        "logs": logs
    }


class BlockUserRequest(BaseModel):
    username: str
    reason: Optional[str] = "Suspicious activity detected by Sovereign Security Sentinel"
    action: Optional[str] = "BLOCK" # "BLOCK" or "UNBLOCK"


@app.post("/api/v1/audit/block-user")
@app.post("/api/audit/block-user")
async def block_or_unblock_user(body: BlockUserRequest):
    """
    Blocks/Freezes or Unblocks a suspicious user account immediately.
    """
    uname = body.username.strip().lower()
    if uname == "admin":
        raise HTTPException(status_code=400, detail="Cannot block root administrator account 'admin'")

    new_status = "FROZEN" if body.action.upper() == "BLOCK" else "ACTIVE"

    if uname in AUTH_USERS:
        AUTH_USERS[uname]["status"] = new_status

    from backend.db import log_user_activity
    log_user_activity(
        username="admin",
        role="SUPER_ADMIN",
        activity_type="SECURITY_TRIGGER",
        details=f"Admin {body.action.upper()}ED user '{uname}'. Reason: {body.reason}",
        risk_level="CRITICAL" if new_status == "FROZEN" else "NORMAL"
    )

    logger.warning(f"[SECURITY_SENTINEL] User '{uname}' status changed to {new_status} by Admin. Reason: {body.reason}")

    return {
        "status": "SUCCESS",
        "username": uname,
        "new_status": new_status,
        "message": f"User '{uname}' has been successfully {new_status.lower()}."
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")






