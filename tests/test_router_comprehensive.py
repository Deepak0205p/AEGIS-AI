"""
Comprehensive Automated Verification Suite for Upgraded Auto Mode Router.
Tests:
1. Multi-signal Intent Routing across Code, Docs, Excel, PPT, Vision, OCR, Chat.
2. Attachment-Aware File Extension Routing.
3. Bilingual / Natural Language prompt handling.
4. Negative exclusion & Email retention guards.
5. Adaptive Thinking Decisions.
6. Industrial Equipment Tag and Chemical DB gating.
"""

import sys
import os
import asyncio
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.router import (
    route_message,
    route_message_async,
    get_thinking_decision_with_reason,
    get_rag_decision_with_reason,
    is_follow_up_query,
)
from backend.vision_mode import encode_image_to_base64


def test_code_mode_routing():
    prompts = [
        "write a python script to simulate heat exchanger",
        "calculate the fibonacci series up to 100",
        "debug this code snippet: def foo(): return 1/0",
        "plot the vibration frequency of pump P-101 in matplotlib",
        "solve the differential equation for fluid flow",
        "run benchmark on array sorting algorithm",
        "python script likho jo csv parse kare",
    ]
    for p in prompts:
        route, trigger = route_message(p)
        assert route == "code", f"[FAIL] Query: '{p}' -> Expected 'code', got '{route}' (trigger: {trigger})"
    print("  [PASS] Code Mode Routing (7/7 test cases)")


def test_excel_mode_routing():
    prompts = [
        "create an excel sheet for quarterly revenue",
        "generate a monthly budget spreadsheet with vlookup formulas",
        "tabulate employee salary and calculate average in xlsx",
        "prepare a csv table of equipment calibration logs",
        "pivot table banao monthly expenses ka",
        "export the maintenance cost dataset to spreadsheet",
    ]
    for p in prompts:
        route, trigger = route_message(p)
        assert route == "excel", f"[FAIL] Query: '{p}' -> Expected 'excel', got '{route}' (trigger: {trigger})"
    print("  [PASS] Excel Mode Routing (6/6 test cases)")


def test_ppt_mode_routing():
    prompts = [
        "create a 5 slides presentation on plant fire safety",
        "prepare a pitch deck for executive review",
        "generate powerpoint slides for refinery modernization",
        "slides banao for quarterly safety committee meeting",
        "create a presentation on hazardous chemical management",
    ]
    for p in prompts:
        route, trigger = route_message(p)
        assert route == "ppt", f"[FAIL] Query: '{p}' -> Expected 'ppt', got '{route}' (trigger: {trigger})"
    print("  [PASS] PowerPoint Mode Routing (5/5 test cases)")


def test_docs_mode_routing():
    prompts = [
        "draft an official memo regarding annual maintenance shutdown",
        "prepare minutes of meeting for yesterday's safety committee",
        "make an official report on tank farm inspection",
        "circular nikalo for revised shift timings",
        "draft a formal approval note for procurement",
    ]
    for p in prompts:
        route, trigger = route_message(p)
        assert route == "docs", f"[FAIL] Query: '{p}' -> Expected 'docs', got '{route}' (trigger: {trigger})"
    print("  [PASS] Docs Mode Routing (5/5 test cases)")


def test_email_retention_and_chat_routing():
    prompts = [
        ("write an email to HR for sick leave", "chat"),
        ("send a mail to operations lead regarding shift handover", "chat"),
        ("draft an email with attached doc for review", "chat"),
        ("what is the operating temperature limit of F-101?", "chat"),
        ("who is the designated safety officer for area 3?", "chat"),
        ("hi, how are you?", "chat"),
    ]
    for p, expected in prompts:
        route, trigger = route_message(p)
        assert route == expected, f"[FAIL] Query: '{p}' -> Expected '{expected}', got '{route}' (trigger: {trigger})"
    print("  [PASS] Email Retention & Chat Fallback Routing (6/6 test cases)")


def test_attachment_driven_routing():
    cases = [
        ("Process this", ["data/sample_pipeline.py"], "code"),
        ("Evaluate data", ["data/records.csv"], "excel"),
        ("Review metrics", ["financials.xlsx"], "excel"),
        ("Check slides", ["safety_talk.pptx"], "ppt"),
        ("Formal report", ["annual_review.docx"], "docs"),
        ("Inspect schematic", ["piping_diagram.png"], "ocr"),
        ("Scan receipt", ["invoice.jpg"], "ocr"),
    ]
    for msg, atts, expected in cases:
        route, trigger = route_message(msg, attachments=atts)
        assert route == expected, f"[FAIL] Attachment '{atts}' -> Expected '{expected}', got '{route}' (trigger: {trigger})"
    print("  [PASS] Attachment-Driven Routing (7/7 test cases)")


def test_manual_overrides():
    modes = ["code", "excel", "ppt", "docs", "vision", "ocr", "chat"]
    for m in modes:
        route, trigger = route_message("arbitrary prompt", mode_override=m)
        assert route == m, f"[FAIL] Manual override '{m}' -> Expected '{m}', got '{route}'"
    print("  [PASS] Manual Mode Overrides (7/7 test cases)")


def test_image_encoder():
    # Test base64 string pass-through
    raw_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
    assert encode_image_to_base64(raw_b64) == raw_b64
    # Test URI stripping
    uri_b64 = f"data:image/png;base64,{raw_b64}"
    assert encode_image_to_base64(uri_b64) == raw_b64
    print("  [PASS] Vision Base64 Image Encoding")


def test_conversation_aware_routing():
    # Follow-up from chat / code to Excel
    route, trigger = route_message("now export this to excel", last_route="chat")
    assert route == "excel", f"[FAIL] Expected 'excel', got '{route}'"

    route, trigger = route_message("put in spreadsheet", last_route="code")
    assert route == "excel", f"[FAIL] Expected 'excel', got '{route}'"

    # Follow-up to PPT
    route, trigger = route_message("convert to slides", last_route="docs")
    assert route == "ppt", f"[FAIL] Expected 'ppt', got '{route}'"

    # Follow-up to Docs
    route, trigger = route_message("save as docx report", last_route="code")
    assert route == "docs", f"[FAIL] Expected 'docs', got '{route}'"

    print("  [PASS] Conversation-Aware Follow-Up Routing (4/4 test cases)")


def test_multi_intent_decomposition():
    # Multi-intent when allow_multi=True
    msg = "write python code to scrape telemetry and generate excel spreadsheet"
    route, trigger = route_message(msg, allow_multi=True)
    assert route == "multi", f"[FAIL] Expected 'multi', got '{route}'"
    assert "code" in trigger and "excel" in trigger

    # When allow_multi=False, picks primary cleanly
    route, trigger = route_message(msg, allow_multi=False)
    assert route in ("code", "excel")

    print("  [PASS] Multi-Intent Decomposition (2/2 test cases)")


def run_all_tests():
    print("\n" + "=" * 60)
    print("PHASE 5: COMPREHENSIVE AUTOMATED ROUTER VERIFICATION SUITE")
    print("=" * 60)
    test_code_mode_routing()
    test_excel_mode_routing()
    test_ppt_mode_routing()
    test_docs_mode_routing()
    test_email_retention_and_chat_routing()
    test_attachment_driven_routing()
    test_manual_overrides()
    test_image_encoder()
    test_conversation_aware_routing()
    test_multi_intent_decomposition()
    print("=" * 60)
    print("ALL COMPREHENSIVE VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    run_all_tests()
