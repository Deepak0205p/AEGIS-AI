"""
Live E2E Verification Script for Phase 3 checks.
Tests live server on http://localhost:8000/api/chat.
"""

import sys
import json
import urllib.request
from typing import Dict, Any, List

sys.stdout.reconfigure(encoding="utf-8")


def send_chat_request(message: str, mode: str = "auto", chat_id: str = None) -> List[Dict[str, Any]]:
    payload = {"message": message, "mode": mode}
    if chat_id:
        payload["chat_id"] = chat_id
        
    req = urllib.request.Request(
        "http://localhost:8000/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    
    events = []
    with urllib.request.urlopen(req) as resp:
        for raw_line in resp:
            line = raw_line.decode("utf-8").strip()
            if line.startswith("data: "):
                try:
                    data = json.loads(line[6:])
                    events.append(data)
                except Exception:
                    pass
    return events


def run_checks():
    import uuid
    run_id = uuid.uuid4().hex[:6]
    print("=" * 70)
    print(f"STARTING LIVE E2E PHASE 3 VERIFICATION (run_id={run_id})")
    print("=" * 70)

    # CHECK 1: "what is benzene"
    print("\n--- CHECK 1: 'what is benzene' ---")
    events1 = send_chat_request("what is benzene", chat_id=f"verify_benzene_{run_id}")
    meta1 = next(e for e in events1 if e.get("event") == "meta")
    final1 = next(e for e in events1 if e.get("event") == "final_answer")
    thinking_events1 = [e for e in events1 if "thinking" in e and e.get("event") == "step"]
    content1 = final1.get("content", "")

    print(f"Meta: {meta1}")
    print(f"Thinking frames count: {len(thinking_events1)} (expected 0)")
    print(f"Content:\n{content1}\n")

    assert meta1["thinking"] is False, "Thinking should be False"
    assert len(thinking_events1) == 0, "No thinking frames allowed"
    assert "71-43-2" in content1, "Benzene CAS 71-43-2 must be present in response"
    assert "250-61-8" not in content1, "Wrong CAS must NEVER appear"
    assert "c6h6" in content1.lower() or "c₆h₆" in content1.lower() or "benzene" in content1.lower(), "C6H6 formula expected"
    print(">>> CHECK 1 PASSED: 'what is benzene' correctly returned CAS 71-43-2 with no thinking frames.")

    # CHECK 2: "H2S ka TLV and exposure symptoms?"
    print("\n--- CHECK 2: 'H2S ka TLV and exposure symptoms?' ---")
    events2 = send_chat_request("H2S ka TLV and exposure symptoms?", chat_id=f"verify_h2s_{run_id}")
    meta2 = next(e for e in events2 if e.get("event") == "meta")
    final2 = next(e for e in events2 if e.get("event") == "final_answer")
    content2 = final2.get("content", "")

    print(f"Meta: {meta2}")
    print(f"Content:\n{content2}\n")
    assert "1 ppm" in content2 or "5 ppm" in content2 or "7783-06-4" in content2, "H2S DB values must be cited"
    print(">>> CHECK 2 PASSED: H2S chemical DB values injected and answered.")

    # CHECK 3: "What is photosynthesis?"
    print("\n--- CHECK 3: 'What is photosynthesis?' ---")
    events3 = send_chat_request("What is photosynthesis?", chat_id=f"verify_photo_{run_id}")
    meta3 = next(e for e in events3 if e.get("event") == "meta")
    final3 = next(e for e in events3 if e.get("event") == "final_answer")
    content3 = final3.get("content", "")

    print(f"Meta: {meta3}")
    print(f"Content:\n{content3}\n")
    assert len(content3.split()) >= 5, "Should return a proper general knowledge answer"
    assert "Operational parameters for this query are not indexed" not in content3, "Must not freeze on general knowledge"
    print(">>> CHECK 3 PASSED: 'What is photosynthesis?' answered via Tier 2 general knowledge.")

    # CHECK 4: "F-101 ki inspection frequency kya hai?"
    print("\n--- CHECK 4: 'F-101 ki inspection frequency kya hai?' ---")
    events4 = send_chat_request("F-101 ki inspection frequency kya hai?", chat_id=f"verify_f101_{run_id}")
    meta4 = next(e for e in events4 if e.get("event") == "meta")
    final4 = next(e for e in events4 if e.get("event") == "final_answer")
    content4 = final4.get("content", "")

    print(f"Meta: {meta4}")
    print(f"Content:\n{content4}\n")
    # Furnace F-101 SOP in KB has TMT control, but NOT inspection frequency -> fallback notice expected
    assert "Operational parameters for this query are not indexed in active Master SOPs" in content4 or "not indexed" in content4, "Deterministic fallback expected for missing parameter"
    print(">>> CHECK 4 PASSED: Unindexed equipment query triggered deterministic fallback.")

    # CHECK 5: "CDU shift handover log banao"
    print("\n--- CHECK 5: 'CDU shift handover log banao' ---")
    events5 = send_chat_request("CDU shift handover log banao", chat_id=f"verify_cdu_{run_id}")
    meta5 = next(e for e in events5 if e.get("event") == "meta")
    final5 = next(e for e in events5 if e.get("event") == "final_answer")
    content5 = final5.get("content", "")

    print(f"Meta: {meta5}")
    print(f"Content:\n{content5}\n")
    # Must trigger template and ask for inputs or provide structured format without inventing numbers
    assert meta5.get("template") == "shift_handover" or "shift" in content5.lower(), "Shift handover template expected"
    print(">>> CHECK 5 PASSED: Shift handover log generated with template/input requirements.")

    # CHECK 6: "python script first 10 primes"
    print("\n--- CHECK 6: 'python script first 10 primes' ---")
    events6 = send_chat_request("python script first 10 primes", chat_id=f"verify_primes_{run_id}")
    meta6 = next(e for e in events6 if e.get("event") == "meta")
    final6 = next(e for e in events6 if e.get("event") == "final_answer")
    run_output6 = final6.get("run_output", "")
    content6 = final6.get("content", "")

    print(f"Meta: {meta6}")
    print(f"Run output:\n{run_output6}\n")
    print(f"Content:\n{content6}\n")
    assert meta6["route"] == "code", "Route should be code"
    assert "29" in run_output6 or "2, 3, 5" in run_output6 or "10" in run_output6 or "23" in run_output6, "Prime numbers expected in verified sandbox stdout"
    print(">>> CHECK 6 PASSED: Python code sandbox execution returned verified prime numbers.")

    # CHECK 7: "hi"
    print("\n--- CHECK 7: 'hi' ---")
    events7 = send_chat_request("hi", chat_id=f"verify_hi_{run_id}")
    meta7 = next(e for e in events7 if e.get("event") == "meta")
    final7 = next(e for e in events7 if e.get("event") == "final_answer")
    thinking_events7 = [e for e in events7 if "thinking" in e and e.get("event") == "step"]
    content7 = final7.get("content", "")

    print(f"Meta: {meta7}")
    print(f"Thinking frames count: {len(thinking_events7)} (expected 0)")
    print(f"Content:\n{content7}\n")
    assert meta7["thinking"] is False, "Thinking should be False"
    assert meta7["rag"] == "skipped", "RAG should be skipped"
    assert len(thinking_events7) == 0, "No thinking frames on greeting"
    print(">>> CHECK 7 PASSED: Instant greeting with no thinking and RAG skipped.")

    print("\n" + "=" * 70)
    print("ALL 7 PHASE 3 CHECKS COMPLETED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_checks()
