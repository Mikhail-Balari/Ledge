"""Deterministic invariants for the persistent AuditStore hash chain."""

import json
import os
import sqlite3

import pytest

from ledge_lang.audit_store import AnchorStore, AuditStore


def make_store(tmp_path, count=4):
    db_path = tmp_path / "audit.db"
    store = AuditStore(db_path=str(db_path))
    ids = []
    for idx in range(count):
        decision_id = f"d{idx + 1}"
        ids.append(decision_id)
        store.record(
            operation=f"op{idx + 1}",
            input_hash=f"input-hash-{idx + 1}",
            output_type="text",
            confidence=0.7 + (idx * 0.01),
            model="test-model",
            program_id="program-a",
            decision_id=decision_id,
        )

    # Timestamps are not part of the hash. Normalize them so ordering-based
    # invariants are deterministic across fast test environments.
    with connect(store) as conn:
        for idx, decision_id in enumerate(ids, start=1):
            conn.execute(
                "UPDATE decisions SET timestamp = ? WHERE id = ?",
                (float(idx), decision_id),
            )
        conn.commit()

    return store, ids


def connect(store):
    return sqlite3.connect(store._db_path)


def verify_failed(store):
    ok, bad_id = store.verify(program_id="program-a")
    assert ok is False
    assert bad_id is not None


def chain_hashes(store):
    return [row["chain_hash"] for row in store.query(program_id="program-a")]


def test_empty_store_behavior_is_defined(tmp_path):
    store, _ = make_store(tmp_path, count=0)

    assert store.verify() == (True, None)
    assert store.verify(program_id="missing-program") == (True, None)
    assert store.query() == []


def test_valid_event_sequence_verifies_successfully(tmp_path):
    store, ids = make_store(tmp_path, count=4)

    assert ids == ["d1", "d2", "d3", "d4"]
    assert store.verify(program_id="program-a") == (True, None)


def test_modifying_existing_event_causes_verification_failure(tmp_path):
    store, _ = make_store(tmp_path, count=3)

    with connect(store) as conn:
        conn.execute(
            "UPDATE decisions SET operation = ? WHERE id = ?",
            ("tampered-op", "d2"),
        )
        conn.commit()

    verify_failed(store)


def test_deleting_middle_event_causes_verification_failure(tmp_path):
    store, _ = make_store(tmp_path, count=4)

    with connect(store) as conn:
        conn.execute("DELETE FROM decisions WHERE id = ?", ("d2",))
        conn.commit()

    verify_failed(store)


def test_tail_deletion_is_detected_when_anchor_is_checked(tmp_path):
    store, _ = make_store(tmp_path, count=4)
    anchor_path = tmp_path / "anchors.jsonl"
    anchors = AnchorStore(str(anchor_path))

    latest_hash = chain_hashes(store)[0]
    anchors.add_anchor(latest_hash, entry_count=4, timestamp=1_700_000_000.0)

    with connect(store) as conn:
        conn.execute("DELETE FROM decisions WHERE id = ?", ("d4",))
        conn.commit()

    # DB-only verification is a chain-integrity check, not a completeness
    # proof. The separate anchor is what makes this tail deletion detectable in
    # the documented local threat model.
    assert store.verify(program_id="program-a") == (True, None)
    result = anchors.verify_against_store(store)
    assert result["store_matches_anchors"] is False
    assert result["anchors_failed"] == 1


def test_inserting_event_causes_verification_failure(tmp_path):
    store, _ = make_store(tmp_path, count=3)

    with connect(store) as conn:
        row = conn.execute("SELECT * FROM decisions WHERE id = ?", ("d2",)).fetchone()
        conn.execute(
            """INSERT INTO decisions
               (id, timestamp, program_id, operation, input_hash, output_type,
                confidence, model, chain_hash, prev_hash)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "fake",
                2.5,
                row[2],
                "fake-op",
                "fake-input",
                row[5],
                1.0,
                "fake-model",
                "f" * 64,
                row[8],
            ),
        )
        conn.commit()

    verify_failed(store)


def test_reordering_events_causes_verification_failure(tmp_path):
    store, _ = make_store(tmp_path, count=3)

    with connect(store) as conn:
        conn.execute("UPDATE decisions SET timestamp = ? WHERE id = ?", (3.5, "d1"))
        conn.commit()

    verify_failed(store)


def test_corrupting_hash_causes_verification_failure(tmp_path):
    store, _ = make_store(tmp_path, count=3)

    with connect(store) as conn:
        conn.execute(
            "UPDATE decisions SET chain_hash = ? WHERE id = ?",
            ("0" * 64, "d2"),
        )
        conn.commit()

    verify_failed(store)


def test_anchor_file_integrity_mismatch_is_detected(tmp_path):
    store, _ = make_store(tmp_path, count=2)
    anchor_path = tmp_path / "anchors.jsonl"
    anchors = AnchorStore(str(anchor_path))

    latest_hash = chain_hashes(store)[0]
    anchors.add_anchor(latest_hash, entry_count=2, timestamp=1_700_000_000.0)
    record = json.loads(anchor_path.read_text(encoding="utf-8").strip())
    record["anchor_hash"] = "bad" * 21 + "b"
    anchor_path.write_text(json.dumps(record) + "\n", encoding="utf-8")

    result = anchors.verify_against_store(store)
    assert result["store_matches_anchors"] is False
    assert result["anchors_failed"] == 1
    assert result["details"][0]["integrity_ok"] is False


def test_partial_corrupt_audit_store_fails_safely(tmp_path):
    store, _ = make_store(tmp_path, count=1)
    db_path = store._db_path
    for suffix in ("", "-wal", "-shm"):
        path = db_path + suffix
        if os.path.exists(path):
            os.remove(path)
    with open(db_path, "wb") as f:
        f.write(b"not a sqlite database")

    broken = object.__new__(AuditStore)
    broken._db_path = db_path
    broken._lock = store._lock

    with pytest.raises(sqlite3.DatabaseError):
        broken.verify()
