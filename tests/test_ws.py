"""
WebSocket End-to-End Test Suite for Sovereign AI Backend.
Tests ws://localhost:8000/api/chat/stream and ws://localhost:8000/api/audit-stream.
"""

import sys
import os
import json
import asyncio
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    import websockets
except ImportError:
    print("[ERROR] websockets package is not installed.")
    sys.exit(1)


import uuid

async def test_chat_stream_protocol():
    """Tests /api/chat/stream with standard {message, mode, chat_id} protocol."""
    uri = "ws://127.0.0.1:8000/api/chat/stream"
    print(f"\n[TEST 1] Connecting to {uri} ...")
    
    async with websockets.connect(uri) as ws:
        chat_id = f"ws_chat_{uuid.uuid4().hex[:8]}"
        payload = {
            "message": "Hello, please reply in 5 words.",
            "mode": "chat",
            "chat_id": chat_id
        }
        await ws.send(json.dumps(payload))
        print(f"[TEST 1] Sent payload: {payload}")
        
        # 1. First frame MUST contain 'route'
        first_frame_raw = await asyncio.wait_for(ws.recv(), timeout=10.0)
        first_frame = json.loads(first_frame_raw)
        print(f"[TEST 1] First Frame Received: {first_frame}")
        assert "route" in first_frame, f"Expected 'route' in first frame, got {first_frame}"
        assert first_frame["route"] in ("chat", "code", "docs", "excel", "ppt")
        print(f"  --> Route verified: '{first_frame['route']}'")
        
        # 2. Collect streaming tokens until 'done' is true
        tokens = []
        done_frame = None
        
        while True:
            frame_raw = await asyncio.wait_for(ws.recv(), timeout=60.0)
            frame = json.loads(frame_raw)
            if "token" in frame:
                tokens.append(frame["token"])
            if frame.get("done") is True:
                done_frame = frame
                break
                
        print(f"[TEST 1] Received {len(tokens)} token frames.")
        print(f"[TEST 1] Done Frame Received: {done_frame}")
        assert done_frame is not None, "Did not receive done frame!"
        assert done_frame.get("done") is True
        full_text = "".join(tokens)
        print(f"[TEST 1] Reconstructed Response Sample ({len(full_text)} chars): {full_text[:80]}...")
        print("[TEST 1] PASSED: Standard chat stream protocol verified successfully.")


async def test_chat_frontend_payload():
    """Tests /api/chat/stream with Next.js frontend format: {prompt, role, session_id}."""
    uri = "ws://127.0.0.1:8000/api/chat/stream"
    print(f"\n[TEST 2] Testing Frontend Client Format at {uri} ...")
    
    async with websockets.connect(uri) as ws:
        sess_id = f"ws_sess_{uuid.uuid4().hex[:8]}"
        payload = {
            "prompt": "List 2 primary safety precautions for furnace startup.",
            "role": "orchestrator",
            "session_id": sess_id,
            "attachments": [],
            "history": []
        }
        await ws.send(json.dumps(payload))
        print(f"[TEST 2] Sent frontend payload: {payload}")
        
        first_frame_raw = await asyncio.wait_for(ws.recv(), timeout=10.0)
        first_frame = json.loads(first_frame_raw)
        print(f"[TEST 2] First Frame Received: {first_frame}")
        assert "route" in first_frame
        
        tokens = []
        done_frame = None
        while True:
            frame_raw = await asyncio.wait_for(ws.recv(), timeout=60.0)
            frame = json.loads(frame_raw)
            if "token" in frame:
                tokens.append(frame["token"])
            if frame.get("done") is True:
                done_frame = frame
                break
                
        print(f"[TEST 2] Received {len(tokens)} token frames.")
        assert done_frame is not None and done_frame.get("done") is True
        print("[TEST 2] PASSED: Frontend format compatibility verified successfully.")


async def test_audit_stream():
    """Tests /api/audit-stream continuous telemetry feed."""
    uri = "ws://127.0.0.1:8000/api/audit-stream"
    print(f"\n[TEST 3] Testing Telemetry Stream at {uri} ...")
    
    async with websockets.connect(uri) as ws:
        frame_raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
        frame = json.loads(frame_raw)
        print(f"[TEST 3] Audit Frame Received: {frame}")
        assert "sovereignty" in frame, "Expected 'sovereignty' in audit frame"
        assert "vram" in frame, "Expected 'vram' in audit frame"
        print("[TEST 3] PASSED: Telemetry audit stream verified successfully.")


async def main():
    print("=" * 70)
    print("  RUNNING WEBSOCKET END-TO-END VERIFICATION")
    print("=" * 70)
    await test_chat_stream_protocol()
    await test_chat_frontend_payload()
    await test_audit_stream()
    print("\n" + "=" * 70)
    print("  ALL WEBSOCKET TESTS PASSED END-TO-END!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
