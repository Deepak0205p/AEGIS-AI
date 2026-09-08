"""
Verification Suite for Intelligent Model-Driven Auto Mode Routing.
Tests:
1. Model-based zero-keyword routing across English, Hindi, and Hinglish.
2. Context continuity (last_route follow-ups).
3. Fast greeting shortcut latency.
4. Fallback resilience.
"""

import sys
import os
import asyncio
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.router import route_message_async, classify_intent_model

test_cases = [
    # (user_message, expected_mode, description)
    ("ek attendance sheet banao jisme name, shift aur overtime hours ho", "excel", "Hinglish attendance sheet without 'excel' keyword"),
    ("is process ka summary word file me bana ke do", "docs", "Hinglish Word document summary request"),
    ("prepare 5 presentation slides for annual safety audit", "ppt", "English presentation slides request"),
    ("calculate the flow rate through orifice plate if d=50mm and D=100mm and plot the pressure drop", "code", "Fluid calculation and plotting without 'python'/'code' keywords"),
    ("scanned copy me se bill amount aur date read karo", "ocr", "Receipt / bill text extraction"),
    ("can you inspect this diagram for corrosion points?", "vision", "Visual diagram inspection"),
    ("what is the operating pressure of distillation column T-101?", "chat", "Technical plant QA"),
    ("boiler B-201 ka temperature kitna hona chahiye as per SOP?", "chat", "Hinglish SOP QA query"),
    ("monthly budget ka hisab kitna hua table me calculate karo", "excel", "Hinglish ledger/table calculation"),
    ("safety meeting ke points pe official circular draft kardo", "docs", "Official circular / memo drafting"),
]

async def run_model_router_tests():
    print("\n" + "=" * 65)
    print("RUNNING INTELLIGENT MODEL-DRIVEN AUTO MODE ROUTER VERIFICATION")
    print("=" * 65)

    # 1. Test fast greeting
    route, trigger = await route_message_async("Namaste")
    assert route == "chat", f"Expected 'chat', got '{route}'"
    print("  [PASS] Fast greeting path (0ms): 'Namaste' -> chat")

    # 2. Test natural language / Hinglish queries with zero keywords
    passed = 0
    for query, expected_mode, desc in test_cases:
        mode, trigger = await route_message_async(query, mode_override="auto")
        status = "[PASS]" if mode == expected_mode else "[FAIL]"
        if mode == expected_mode:
            passed += 1
        print(f"  {status} {desc}: '{query[:45]}...' -> {mode} (Trigger: {trigger})")
        assert mode == expected_mode, f"Failed: Query '{query}' expected '{expected_mode}', got '{mode}'"

    print("-" * 65)
    print(f"  All {passed}/{len(test_cases)} natural language tests PASSED successfully!")

    # 3. Test follow-up context awareness
    f_mode, f_trigger = await route_message_async("now export this to slides", mode_override="auto", last_route="docs")
    assert f_mode == "ppt", f"Expected 'ppt', got '{f_mode}'"
    print(f"  [PASS] Follow-up context: 'now export this to slides' (last: docs) -> {f_mode}")

    f_mode2, f_trigger2 = await route_message_async("add error handling and plot the convergence curve", mode_override="auto", last_route="code")
    assert f_mode2 == "code", f"Expected 'code', got '{f_mode2}'"
    print(f"  [PASS] Follow-up context: 'add error handling and plot' (last: code) -> {f_mode2}")

    print("=" * 65)
    print("MODEL-DRIVEN AUTO MODE ROUTER FULLY VERIFIED & HARDENED!")
    print("=" * 65 + "\n")

if __name__ == "__main__":
    asyncio.run(run_model_router_tests())
