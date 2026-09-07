"""Unit tests for filter_thinking, detect_department, routing, and templates."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.ollama_client import filter_thinking
from backend.departments import detect_department
from backend.router import (
    route_message,
    get_thinking_decision_with_reason,
    decide_thinking,
    is_follow_up_query,
)
from backend.templates import detect_template


def test_filter_thinking_basic():
    """Basic <think> tag stripping."""
    assert filter_thinking("") == ""
    assert filter_thinking("Hello world") == "Hello world"
    assert filter_thinking("<think>some reasoning</think>Hello") == "Hello"
    assert filter_thinking("<think>reasoning</think>") == ""
    print("  PASS: filter_thinking_basic")


def test_filter_thinking_split_tags():
    """Split tags across token boundaries."""
    # Simulated token split: ["<thi", "nk>hidden</thi", "nk>visible"]
    combined = "<thi" + "nk>hidden</thi" + "nk>visible"
    result = filter_thinking(combined)
    assert "hidden" not in result
    assert "visible" in result
    print("  PASS: filter_thinking_split_tags")


def test_filter_thinking_thinking_process():
    """Strip Thinking Process: prefix."""
    text = "Thinking Process:\n\n1. Analyze input\n2. Generate response\n\nHello, how can I help?"
    result = filter_thinking(text)
    assert "Hello" in result
    assert "Thinking Process" not in result
    print("  PASS: filter_thinking_thinking_process")


def test_detect_department():
    """Equipment tag and keyword-based department detection."""
    # Equipment tags
    dept, trigger = detect_department("Check F-101 temperature")
    assert dept == "operations", f"Expected operations, got {dept}"
    assert "F-101" in trigger

    dept, trigger = detect_department("HEX-201 inspection needed")
    assert dept == "inspection", f"Expected inspection, got {dept}"
    assert "HEX" in trigger

    dept, trigger = detect_department("TK-1002 tank level")
    assert dept == "oil_movement", f"Expected oil_movement, got {dept}"
    assert "TK" in trigger

    dept, trigger = detect_department("P-101A vibration check")
    assert dept == "maintenance", f"Expected maintenance, got {dept}"
    assert "P-" in trigger or "P-101" in trigger

    dept, trigger = detect_department("MOV-104 valve issue")
    assert dept == "operations", f"Expected operations, got {dept}"
    assert "MOV" in trigger

    # Keyword-based
    dept, trigger = detect_department("Leave policy for employees")
    assert dept == "hr", f"Expected hr, got {dept}"
    assert "keyword" in trigger

    dept, trigger = detect_department("Furnace temperature alarm")
    assert dept == "operations", f"Expected operations, got {dept}"

    dept, trigger = detect_department("PSV pop test calibration")
    assert dept == "inspection", f"Expected inspection, got {dept}"

    dept, trigger = detect_department("Oil spill near storage tank")
    assert dept == "hse", f"Expected hse, got {dept}"

    # General / no match
    dept, trigger = detect_department("hi")
    assert dept == "general", f"Expected general, got {dept}"

    print("  PASS: detect_department")


def test_route_message():
    """Routing decisions."""
    # Code mode
    route, trigger = route_message("write a python script")
    assert route == "code", f"Expected code, got {route}"

    # Email stays in chat (not docs)
    route, trigger = route_message("write an email to hr for leave")
    assert route == "chat", f"Expected chat for email, got {route}"

    route, trigger = route_message("send a mail to the team")
    assert route == "chat", f"Expected chat for mail, got {route}"

    # Docs mode
    route, trigger = route_message("make a report")
    assert route == "docs", f"Expected docs, got {route}"

    # Default chat
    route, trigger = route_message("hi there")
    assert route == "chat", f"Expected chat, got {route}"

    # Manual override
    route, trigger = route_message("do something", mode_override="code")
    assert route == "code", f"Expected code override, got {route}"

    print("  PASS: route_message")


def test_thinking_decision():
    """Adaptive thinking decisions."""
    # Code mode -> True
    think, reason = get_thinking_decision_with_reason("anything", "code")
    assert think is True
    assert "code" in reason

    # Docs mode -> False
    think, reason = get_thinking_decision_with_reason("anything", "docs")
    assert think is False
    assert "json" in reason

    # Creation verb -> False
    think, reason = get_thinking_decision_with_reason("write an email to hr", "chat")
    assert think is False
    assert "creation" in reason

    think, reason = get_thinking_decision_with_reason("draft a letter", "chat")
    assert think is False

    think, reason = get_thinking_decision_with_reason("banao ek report", "chat")
    assert think is False

    # Short simple chat -> False
    think, reason = get_thinking_decision_with_reason("hi", "chat")
    assert think is False
    assert "short" in reason

    think, reason = get_thinking_decision_with_reason("what is your name", "chat")
    assert think is False

    # Analytical keyword -> True
    think, reason = get_thinking_decision_with_reason("why did F-101 fail?", "chat")
    assert think is True
    assert "analytical" in reason

    think, reason = get_thinking_decision_with_reason("explain the process", "chat")
    assert think is True

    # Multi-question -> True
    think, reason = get_thinking_decision_with_reason("what is X? and also what is Y?", "chat")
    assert think is True
    assert "multi" in reason

    print("  PASS: thinking_decision")


def test_follow_up_detection():
    """Follow-up query detection."""
    assert is_follow_up_query("explain more") is True
    assert is_follow_up_query("aur batao") is True
    assert is_follow_up_query("continue") is True
    assert is_follow_up_query("hello") is False
    assert is_follow_up_query("what is F-101") is False
    print("  PASS: follow_up_detection")


def test_template_detection():
    """Template intent detection."""
    assert detect_template("CDU shift handover log") == "shift_handover"
    assert detect_template("daily production report") == "daily_production_report"
    assert detect_template("F-101 inspection report") == "inspection_report"
    assert detect_template("oil spill incident report") == "incident_report"
    assert detect_template("mock drill report") == "mock_drill_report"
    assert detect_template("approval note for procurement") == "approval_note"
    assert detect_template("breakdown analysis for pump") == "breakdown_analysis"
    assert detect_template("material indent") == "indent_letter"
    assert detect_template("office circular") == "circular"
    assert detect_template("hi there") is None
    print("  PASS: template_detection")


def test_chemical_db_detection():
    """Chemical detection and verified CAS/TLV integrity."""
    from backend.chemical_kb import detect_chemicals, format_chemical_context_block
    
    # Benzene detection
    chems = detect_chemicals("what is benzene")
    assert len(chems) == 1
    assert chems[0]["name"] == "Benzene"
    assert chems[0]["cas"] == "71-43-2"
    assert "0.02 ppm" in chems[0]["tlv_twa"]

    # H2S detection
    chems = detect_chemicals("H2S ka TLV and exposure symptoms?")
    assert len(chems) == 1
    assert chems[0]["name"] == "Hydrogen Sulfide"
    assert chems[0]["cas"] == "7783-06-4"

    # Multi-chemical detection
    chems = detect_chemicals("Handling of toluene, xylene and nh3")
    names = [c["name"] for c in chems]
    assert "Toluene" in names
    assert "Xylene (Mixed Isomers)" in names
    assert "Ammonia (Anhydrous)" in names

    # General query without chemicals
    chems = detect_chemicals("what is photosynthesis?")
    assert len(chems) == 0

    print("  PASS: chemical_db_detection")


if __name__ == "__main__":
    print("Running unit tests...")
    test_filter_thinking_basic()
    test_filter_thinking_split_tags()
    test_filter_thinking_thinking_process()
    test_detect_department()
    test_route_message()
    test_thinking_decision()
    test_follow_up_detection()
    test_template_detection()
    test_chemical_db_detection()
    print("\n=== ALL UNIT TESTS PASSED ===")
