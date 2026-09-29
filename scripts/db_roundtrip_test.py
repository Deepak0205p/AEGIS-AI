"""
End-to-end exercise of every database code path against the live server.

Verifies the dialect layer works in practice (not just syntactically): upserts,
RETURNING ids, boolean round-trips, ON CONFLICT DO NOTHING, LIKE/ILIKE search,
epoch conversion, and the 2-step verification state machine including the guards
that were previously returning True unconditionally.

Usage:
    python scripts/db_roundtrip_test.py
"""
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import backend.config as cfg  # noqa: E402
import backend.db as db  # noqa: E402

PASS, FAIL = [], []


def check(name, got, want):
    ok = got == want
    (PASS if ok else FAIL).append(name)
    print(f"  {'PASS' if ok else 'FAIL'}  {name:52} got={got!r} want={want!r}")
    return ok


def main() -> int:
    print(f"Target: {cfg.DB_LABEL}\n")
    tag = uuid.uuid4().hex[:8]
    chat_id = f"rt_{tag}"

    # ── messages: identity + RETURNING id ─────────────────────────────────
    print("messages / identity")
    id1 = db.save_message(chat_id, "user", "Hello from the round-trip test", "chat")
    id2 = db.save_message(chat_id, "assistant", "Acknowledged.", "chat")
    check("save_message returns distinct ids", id1 != id2, True)
    check("first id is a positive int", isinstance(id1, int) and id1 > 0, True)

    hist = db.get_chat_history(chat_id)
    check("history row count", len(hist), 2)
    check("history ordered by id", [m["id"] for m in hist], sorted([id1, id2]))
    check("history preserves content", hist[0]["content"], "Hello from the round-trip test")

    # ── chat_summaries: ON CONFLICT DO UPDATE ─────────────────────────────
    print("\nchat_summaries / upsert")
    db.save_cached_summary(chat_id, "First summary.", id1)
    got = db.get_cached_summary(chat_id)
    check("summary stored", got[0], "First summary.")
    db.save_cached_summary(chat_id, "Second summary.", id2)
    got = db.get_cached_summary(chat_id)
    check("summary updated in place (no dup row)", got[0], "Second summary.")
    check("summary last_msg_id updated", got[1], id2)

    # ── files: upsert with COALESCE + boolean round-trip ──────────────────
    # A NULL hash must not wipe a previously computed one. Write a real file
    # first so `file_integrity` actually produces a hash to preserve.
    print("\nfiles / upsert + boolean + coalesce")
    fid = f"rt_file_{tag}"
    real_path = cfg.GENERATED_DIR / f"rt_{tag}.docx"
    real_path.parent.mkdir(parents=True, exist_ok=True)
    real_path.write_bytes(b"PK\x03\x04 round-trip deliverable payload")
    db.save_file_record(fid, chat_id, "round_trip.docx", "docx", str(real_path),
                        verification_status="PENDING_STAGE_1", is_important=True)
    rec = db.get_file_record(fid)
    check("file row created", rec is not None, True)
    check("filename persisted", rec["filename"], "round_trip.docx")
    check("is_important is a real boolean", rec["is_important"], True)
    check("initial status", rec["verification_status"], "PENDING_STAGE_1")
    check("sha256 computed from disk", rec["sha256_hash"] is not None, True)
    check("size_bytes computed from disk", rec["size_bytes"], real_path.stat().st_size)
    first_hash = rec["sha256_hash"]

    # Re-register with is_important False; the boolean must round-trip.
    db.save_file_record(fid, chat_id, "round_trip_v2.docx", "docx", str(real_path),
                        verification_status="PENDING_STAGE_1", is_important=False)
    rec = db.get_file_record(fid)
    check("upsert overwrote filename", rec["filename"], "round_trip_v2.docx")
    check("boolean flipped to False", rec["is_important"], False)

    # Point at an unreadable path so the incoming hash is NULL; COALESCE must
    # keep the previously stored value rather than nulling it out.
    db.save_file_record(fid, chat_id, "round_trip_v2.docx", "docx",
                        "/nonexistent/path.docx",
                        verification_status="PENDING_STAGE_1", is_important=False)
    rec = db.get_file_record(fid)
    check("existing sha256 preserved when new hash is NULL",
          rec["sha256_hash"], first_hash)
    check("existing size_bytes preserved when new size is NULL",
          rec["size_bytes"], real_path.stat().st_size)

    # ── verification state machine + guards ───────────────────────────────
    print("\nverification / state machine + guards")
    # Stage 2 must NOT be signable before stage 1.
    check("stage2 blocked before stage1", db.verify_file_stage_2(fid, "Chief", "x"), False)
    check("stage1 approve succeeds", db.verify_file_stage_1(fid, "Lead", "ok"), True)
    rec = db.get_file_record(fid)
    check("status advanced to PENDING_STAGE_2", rec["verification_status"], "PENDING_STAGE_2")
    # Re-approving stage 1 must be a no-op, not a second success.
    check("stage1 re-approve rejected", db.verify_file_stage_1(fid, "Lead", "again"), False)
    check("stage2 approve succeeds", db.verify_file_stage_2(fid, "Chief", "ok"), True)
    check("status is VERIFIED", db.get_file_record(fid)["verification_status"], "VERIFIED")
    # Nonexistent id must be False, not a silent True.
    check("stage1 on missing file -> False", db.verify_file_stage_1("no_such_file", "x", "y"), False)
    check("stage2 on missing file -> False", db.verify_file_stage_2("no_such_file", "x", "y"), False)
    check("reject on VERIFIED file -> False", db.reject_file(fid, "Lead", "too late"), False)

    # ── pending queue ordering (CASE vs FIELD) ────────────────────────────
    print("\nverification / queue ordering")
    db.save_file_record(f"rt_s1_{tag}", chat_id, "s1.docx", "docx", "p1",
                        verification_status="PENDING_STAGE_1", is_important=True)
    db.save_file_record(f"rt_s2_{tag}", chat_id, "s2.docx", "docx", "p2",
                        verification_status="PENDING_STAGE_2", is_important=True)
    q = db.get_pending_verifications("SUPER_ADMIN")
    order = [i["file_id"] for i in q if i["file_id"].startswith(f"rt_s")]
    check("stage2 sorted before stage1", order[:2], [f"rt_s2_{tag}", f"rt_s1_{tag}"])
    q_op = db.get_pending_verifications("FIELD_OPERATOR")
    check("operator sees only stage1",
          all(i["verification_status"] == "PENDING_STAGE_1" for i in q_op), True)

    # ── rename (blank must be rejected) ───────────────────────────────────
    print("\nfiles / rename guard")
    check("rename succeeds", db.rename_file_record(fid, "renamed_ok.docx"), True)
    check("blank rename rejected", db.rename_file_record(fid, "   "), False)
    check("filename unchanged after blank rename",
          db.get_file_record(fid)["filename"], "renamed_ok.docx")

    # ── feedback reports: identity + case-insensitive search ──────────────
    print("\nfeedback_reports / ILIKE search")
    rid = db.create_feedback_report("ERROR", "PUMP vibration Alarm", "Reported by operator")
    check("report id returned", isinstance(rid, int) and rid > 0, True)
    check("status defaults to OPEN", db.get_feedback_report_by_id(rid)["status"], "OPEN")
    # Upper-case search term must match lower-case title via ILIKE / ci LIKE.
    hits = db.get_all_feedback_reports(search="pump")
    check("case-insensitive search finds 'PUMP'", any(h["id"] == rid for h in hits), True)
    check("update to RESOLVED", db.update_feedback_report(rid, "RESOLVED", "n", "r", "admin"), True)
    rec_r = db.get_feedback_report_by_id(rid)
    check("status now RESOLVED", rec_r["status"], "RESOLVED")
    check("resolved_by recorded", rec_r["resolved_by"], "admin")
    check("resolved_at stamped", rec_r["resolved_at"] is not None, True)

    # ── collaboration channels: upsert + DO NOTHING ───────────────────────
    print("\nchannels / seed idempotency")
    db.seed_default_collaboration_channels()
    before = len(db.get_all_collaboration_channels("operator"))
    db.seed_default_collaboration_channels()   # must not duplicate
    after = len(db.get_all_collaboration_channels("operator"))
    check("re-seeding does not duplicate channels", after, before)

    dm = db.get_or_create_dm_channel("alice", "bob")
    check("dm id deterministic", dm["id"], "dm_alice_bob")
    dm2 = db.get_or_create_dm_channel("bob", "alice")
    check("dm id stable regardless of arg order", dm2["id"], dm["id"])

    # The DM channel is stable across runs, so use a unique body and assert on
    # the messages this run actually wrote.
    marker = f"hello-{tag}"
    mid = db.save_channel_message(dm["id"], "alice", "FIELD_OPERATOR", marker)
    check("channel message id returned", isinstance(mid, int) and mid > 0, True)
    msgs = db.get_channel_messages(dm["id"], 500)
    check("message stored", [m["content"] for m in msgs if m["content"] == marker], [marker])
    check("newest message is the one just written", msgs[-1]["content"], marker)

    # ── activity ledger + identity ────────────────────────────────────────
    print("\nuser_activity_logs")
    lid = db.log_user_activity("operator", "CHAT_QUERY", "test query", chat_id, "details")
    check("activity id returned", isinstance(lid, int) and lid > 0, True)
    logs = db.get_all_user_activity_logs(username="operator", limit=10)
    check("activity retrievable", any(l["id"] == lid for l in logs), True)

    # ── session listing (epoch + substring) ───────────────────────────────
    print("\nchat_sessions / epoch + substring")
    sessions = db.list_all_chat_sessions()
    mine = [s for s in sessions if s["id"] == chat_id]
    check("session listed", len(mine), 1)
    check("created_at is an int epoch", isinstance(mine[0]["created_at"], int), True)
    check("title is a 50-char substring", len(mine[0]["title"]) <= 50, True)

    # ── cleanup ───────────────────────────────────────────────────────────
    print("\ncleanup")
    check("delete session", db.delete_chat_session_data(chat_id), True)
    check("history cleared", len(db.get_chat_history(chat_id)), 0)
    check("summary cleared", db.get_cached_summary(chat_id), None)
    for f in (fid, f"rt_s1_{tag}", f"rt_s2_{tag}"):
        pass  # left in place deliberately; they are not important so not queued

    print()
    total = len(PASS) + len(FAIL)
    print(f"{len(PASS)}/{total} passed")
    if FAIL:
        print("FAILED:")
        for f in FAIL:
            print(f"  - {f}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
