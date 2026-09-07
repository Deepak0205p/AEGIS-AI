"""
E2E tests for the Air-Gapped Backend.
Tests real HTTP/WS requests against the live server.
"""
import httpx
import json
import time
import sys
import io

# Fix Windows console encoding for emoji
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = "http://localhost:8000"


def chat_sse(message, mode="auto", chat_id=None, timeout=120):
    """Send POST /api/chat and collect SSE frames."""
    payload = {"message": message, "mode": mode}
    if chat_id:
        payload["chat_id"] = chat_id
    frames = []
    start = time.time()
    with httpx.Client(timeout=timeout) as client:
        with client.stream("POST", f"{BASE}/api/chat", json=payload) as resp:
            for line in resp.iter_lines():
                line = line.strip()
                if line.startswith("data: "):
                    try:
                        frames.append(json.loads(line[6:]))
                    except json.JSONDecodeError:
                        pass
    elapsed = round(time.time() - start, 2)
    return frames, elapsed


def get_meta(frames):
    """Extract meta frame."""
    return frames[0] if frames else {}


def get_tokens(frames):
    """Extract token texts."""
    return [f.get("token", "") for f in frames if f.get("token")]


def get_done(frames):
    """Extract done frame."""
    for f in frames:
        if f.get("done"):
            return f
    return {}


def get_thinking_frames(frames):
    """Extract thinking frames."""
    return [f for f in frames if f.get("step_type") == "thought"]


passed = 0
failed = 0


def check(name, condition, detail=""):
    global passed, failed
    if condition:
        print(f"  PASS: {name}")
        passed += 1
    else:
        print(f"  FAIL: {name} {detail}")
        failed += 1


# ============================================================
print("=" * 70)
print("TEST 1: 'hi' -> fast reply, thinking:false, rag:skipped, dept:general")
print("=" * 70)
frames1, t1 = chat_sse("hi", chat_id="e2e_test1")
meta1 = get_meta(frames1)
tokens1 = get_tokens(frames1)
done1 = get_done(frames1)
content1 = done1.get("content", "")

check("meta frame has route", meta1.get("route") == "chat")
check("meta frame thinking=false", meta1.get("thinking") is False)
check("meta frame rag=skipped", meta1.get("rag") == "skipped")
check("meta frame department=general", meta1.get("department") == "general")
check("meta frame has model", meta1.get("model") is not None)
check("has tokens", len(tokens1) > 0)
check("content not empty", len(content1) > 0)
check("no thinking text in content", "thinking process" not in content1.lower() and "<think>" not in content1)
check("fast reply (<30s)", t1 < 30)
print(f"  Time: {t1}s | Tokens: {len(tokens1)} | Content: {content1[:80]}...")
print()

# ============================================================
print("=" * 70)
print("TEST 2: 'write an email to hr for leave' -> chat route, creation verb")
print("=" * 70)
frames2, t2 = chat_sse("write an email to hr for leave", chat_id="e2e_test2")
meta2 = get_meta(frames2)
tokens2 = get_tokens(frames2)
done2 = get_done(frames2)
content2 = done2.get("content", "")

check("route is chat (email stays in chat)", meta2.get("route") == "chat")
check("thinking=false (creation verb)", meta2.get("thinking") is False)
check("department=hr", meta2.get("department") == "hr")
check("has tokens", len(tokens2) > 0)
check("content not empty", len(content2) > 0)
print(f"  Time: {t2}s | Content: {content2[:120]}...")
print()

# ============================================================
print("=" * 70)
print("TEST 3: 'CDU ki shift handover log banao' -> template:shift_handover")
print("=" * 70)
frames3, t3 = chat_sse("CDU ki shift handover log banao", chat_id="e2e_test3")
meta3 = get_meta(frames3)
tokens3 = get_tokens(frames3)
done3 = get_done(frames3)
content3 = done3.get("content", "")

check("route is chat", meta3.get("route") == "chat")
check("template=shift_handover", meta3.get("template") == "shift_handover")
check("department=operations", meta3.get("department") == "operations")
check("thinking=false (creation verb banao)", meta3.get("thinking") is False)
check("has tokens", len(tokens3) > 0)
print(f"  Time: {t3}s | Content: {content3[:120]}...")
print()

# ============================================================
print("=" * 70)
print("TEST 4: 'F-101 inspection report...' -> RAG hit, dept:inspection")
print("=" * 70)
frames4, t4 = chat_sse(
    "F-101 inspection report. UTM: previous 12.5mm (2023-04), current 9.8mm, min required 8.7mm, service 2 years",
    chat_id="e2e_test4",
    timeout=120
)
meta4 = get_meta(frames4)
tokens4 = get_tokens(frames4)
done4 = get_done(frames4)
content4 = done4.get("content", "")

check("route is chat", meta4.get("route") == "chat")
check("rag=hit", meta4.get("rag") == "hit")
check("department=operations (F-101 is furnace)", meta4.get("department") == "operations")
check("template=inspection_report", meta4.get("template") == "inspection_report")
check("has tokens", len(tokens4) > 0)
check("content not empty", len(content4) > 0)
print(f"  Time: {t4}s | Content: {content4[:150]}...")
print()

# ============================================================
print("=" * 70)
print("TEST 5: 'oil spill near TK-1002, prepare incident report' -> dept:hse")
print("=" * 70)
frames5, t5 = chat_sse(
    "oil spill near TK-1002, prepare incident report",
    chat_id="e2e_test5",
    timeout=120
)
meta5 = get_meta(frames5)
tokens5 = get_tokens(frames5)
done5 = get_done(frames5)

check("route is chat", meta5.get("route") == "chat")
check("department=hse", meta5.get("department") == "hse")
check("template=incident_report", meta5.get("template") == "incident_report")
check("has tokens", len(tokens5) > 0)
print(f"  Time: {t5}s")
print()

# ============================================================
print("=" * 70)
print("TEST 6: 'python script to print first 10 primes' -> code route, sandbox")
print("=" * 70)
frames6, t6 = chat_sse(
    "python script to print first 10 primes",
    mode="code",
    chat_id="e2e_test6",
    timeout=90
)
meta6 = get_meta(frames6)
tokens6 = get_tokens(frames6)
done6 = get_done(frames6)

check("route is code", meta6.get("route") == "code")
check("thinking=true (code mode)", meta6.get("thinking") is True)
check("rag=skipped", meta6.get("rag") == "skipped")
check("sandbox ran (output or error present)", done6.get("run_output") is not None)
check("sandbox has status", done6.get("status") in ("success", "error"))
print(f"  Time: {t6}s | Status: {done6.get('status')}")
print(f"  Run output: {(done6.get('run_output') or '')[:200]}")
print()

# ============================================================
print("=" * 70)
print("TEST 7: 'explain more' -> follow-up, no new RAG retrieval")
print("=" * 70)
# First do an RAG query to populate cache
chat_id_7 = "e2e_test7"
_ = chat_sse("F-101 temperature limits", chat_id=chat_id_7)

# Now "explain more" should reuse cache
frames7, t7 = chat_sse("explain more", chat_id=chat_id_7)
meta7 = get_meta(frames7)
tokens7 = get_tokens(frames7)

check("route is chat", meta7.get("route") == "chat")
check("thinking=true (explain keyword)", meta7.get("thinking") is True)
check("has tokens", len(tokens7) > 0)
print(f"  Time: {t7}s")
print()

# ============================================================
print("=" * 70)
print("TEST 8: Health check")
print("=" * 70)
health = httpx.get(f"{BASE}/api/health").json()
check("status=ok", health.get("status") == "ok")
check("ollama_connected", health.get("ollama_connected") is True)
check("model matches", health.get("model") == "deepseek-v4-pro:4b")
print()

# ============================================================
print("=" * 70)
print(f"RESULTS: {passed} passed, {failed} failed out of {passed + failed}")
print("=" * 70)
sys.exit(0 if failed == 0 else 1)
