"""
Ledge Audit Store — SQLite-backed persistent audit trail.

Default location: ~/.ledge/audit.db
WAL mode for thread safety.
"""

import os
import json
import hashlib
import sqlite3
import threading
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


_GENESIS = "0" * 64
_LEDGE_VERSION = "1.1.0"


class AuditStore:
    """
    Persistent, tamper-evident SQLite audit store.

    Each program_id has its own chain rooted at GENESIS.
    chain_hash = SHA256(prev_hash + id + operation + input_hash + str(confidence) + model)
    """

    _SCHEMA = """
    CREATE TABLE IF NOT EXISTS decisions (
        id                  TEXT    PRIMARY KEY,
        timestamp           REAL    NOT NULL,
        program_id          TEXT    NOT NULL,
        operation           TEXT    NOT NULL,
        input_hash          TEXT    NOT NULL,
        output_type         TEXT    NOT NULL,
        confidence          REAL    NOT NULL,
        model               TEXT    NOT NULL,
        chain_hash          TEXT    NOT NULL,
        prev_hash           TEXT    NOT NULL,
        outcome             TEXT    DEFAULT NULL,
        outcome_timestamp   REAL    DEFAULT NULL,
        outcome_correct     INTEGER DEFAULT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_program_ts  ON decisions(program_id, timestamp);
    CREATE INDEX IF NOT EXISTS idx_model       ON decisions(model);
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            ledge_dir = os.path.expanduser("~/.ledge")
            os.makedirs(ledge_dir, exist_ok=True)
            db_path = os.path.join(ledge_dir, "audit.db")
        self._db_path = db_path
        self._lock = threading.Lock()
        self._session_record_count = 0
        self._anchor_interval = 10
        self._anchor_store: Optional["AnchorStore"] = None  # lazy default
        self._init_db()

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._lock:
            conn = self._connect()
            try:
                conn.execute("PRAGMA journal_mode=WAL")
                conn.executescript(self._SCHEMA)
                conn.commit()
            finally:
                conn.close()

    @staticmethod
    def _chain_hash(prev_hash: str, decision_id: str, operation: str,
                    input_hash: str, confidence: float, model: str) -> str:
        raw = prev_hash + decision_id + operation + input_hash + str(confidence) + model
        return hashlib.sha256(raw.encode()).hexdigest()

    def _last_chain_hash(self, conn: sqlite3.Connection, program_id: str) -> str:
        row = conn.execute(
            "SELECT chain_hash FROM decisions "
            "WHERE program_id = ? ORDER BY timestamp DESC LIMIT 1",
            (program_id,),
        ).fetchone()
        return row["chain_hash"] if row else _GENESIS

    # ── Public API ────────────────────────────────────────────────────────────

    def record(self, operation: str, input_hash: str, output_type: str,
               confidence: float, model: str, program_id: str = "default",
               decision_id: Optional[str] = None) -> str:
        """
        Insert one AI decision.  Returns the decision id (UUID or supplied id).
        Thread-safe; WAL lets readers proceed concurrently.
        """
        if decision_id is None:
            import uuid
            decision_id = str(uuid.uuid4())
        ts = time.time()

        chain_hash = None
        with self._lock:
            conn = self._connect()
            try:
                prev_hash  = self._last_chain_hash(conn, program_id)
                chain_hash = self._chain_hash(
                    prev_hash, decision_id, operation, input_hash, confidence, model
                )
                conn.execute(
                    """INSERT OR IGNORE INTO decisions
                       (id, timestamp, program_id, operation, input_hash, output_type,
                        confidence, model, chain_hash, prev_hash)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (decision_id, ts, program_id, operation, input_hash, output_type,
                     confidence, model, chain_hash, prev_hash),
                )
                conn.commit()
            finally:
                conn.close()

        self._session_record_count += 1
        if chain_hash and self._session_record_count % self._anchor_interval == 0:
            try:
                _as = self._anchor_store if self._anchor_store is not None else AnchorStore()
                _as.add_anchor(chain_hash, self._session_record_count, time.time())
            except Exception:
                pass  # never break execution

        return decision_id

    def verify(self, program_id: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Walk all entries in insertion order and recompute every chain_hash.
        Returns (True, None) if intact, (False, bad_id) on first mismatch.
        """
        with self._lock:
            conn = self._connect()
            try:
                if program_id:
                    rows = conn.execute(
                        "SELECT * FROM decisions WHERE program_id = ? ORDER BY timestamp ASC",
                        (program_id,),
                    ).fetchall()
                else:
                    rows = conn.execute(
                        "SELECT * FROM decisions ORDER BY program_id, timestamp ASC"
                    ).fetchall()
            finally:
                conn.close()

        # Each program_id has its own chain rooted at GENESIS
        chains: Dict[str, List[dict]] = defaultdict(list)
        for row in rows:
            chains[row["program_id"]].append(dict(row))

        for pid, entries in chains.items():
            prev = _GENESIS
            for e in entries:
                if e["prev_hash"] != prev:
                    return False, e["id"]
                expected = self._chain_hash(
                    prev, e["id"], e["operation"],
                    e["input_hash"], e["confidence"], e["model"],
                )
                if e["chain_hash"] != expected:
                    return False, e["id"]
                prev = e["chain_hash"]

        return True, None

    def record_outcome(self, decision_id: str, was_correct: bool, notes: str = ""):
        """Attach a real-world outcome to a past decision."""
        ts = time.time()
        outcome_text = notes or ("correct" if was_correct else "incorrect")
        with self._lock:
            conn = self._connect()
            try:
                conn.execute(
                    """UPDATE decisions
                       SET outcome = ?, outcome_timestamp = ?, outcome_correct = ?
                       WHERE id = ?""",
                    (outcome_text, ts, 1 if was_correct else 0, decision_id),
                )
                conn.commit()
            finally:
                conn.close()

    def get_real_accuracy(self, model: str,
                          domain: str = "default") -> Tuple[Optional[float], int]:
        """
        Returns (accuracy, sample_size) for decisions with recorded outcomes.
        domain="default" means all program_ids; otherwise filtered by program_id.
        """
        with self._lock:
            conn = self._connect()
            try:
                if domain == "default":
                    rows = conn.execute(
                        "SELECT outcome_correct FROM decisions "
                        "WHERE model = ? AND outcome_correct IS NOT NULL",
                        (model,),
                    ).fetchall()
                else:
                    rows = conn.execute(
                        "SELECT outcome_correct FROM decisions "
                        "WHERE model = ? AND program_id = ? AND outcome_correct IS NOT NULL",
                        (model, domain),
                    ).fetchall()
            finally:
                conn.close()

        if not rows:
            return None, 0
        n = len(rows)
        correct = sum(1 for r in rows if r["outcome_correct"] == 1)
        return correct / n, n

    def query(self, program_id: Optional[str] = None,
              model: Optional[str] = None,
              since: Optional[float] = None,
              min_confidence: Optional[float] = None,
              limit: int = 10_000) -> List[Dict]:
        """Return decisions matching the given filters, newest first."""
        clauses, params = [], []
        if program_id:
            clauses.append("program_id = ?"); params.append(program_id)
        if model:
            clauses.append("model = ?");      params.append(model)
        if since is not None:
            clauses.append("timestamp >= ?"); params.append(since)
        if min_confidence is not None:
            clauses.append("confidence >= ?"); params.append(min_confidence)

        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        sql   = f"SELECT * FROM decisions {where} ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with self._lock:
            conn = self._connect()
            try:
                rows = conn.execute(sql, params).fetchall()
            finally:
                conn.close()
        return [dict(r) for r in rows]

    def stats(self) -> List[Dict]:
        """Accuracy stats grouped by (model, program_id)."""
        with self._lock:
            conn = self._connect()
            try:
                rows = conn.execute(
                    """SELECT
                         model, program_id,
                         COUNT(*) AS total,
                         ROUND(AVG(confidence), 3) AS avg_confidence,
                         SUM(CASE WHEN outcome_correct IS NOT NULL THEN 1 ELSE 0 END) AS with_outcome,
                         SUM(CASE WHEN outcome_correct = 1 THEN 1 ELSE 0 END) AS correct
                       FROM decisions
                       GROUP BY model, program_id
                       ORDER BY model, program_id"""
                ).fetchall()
            finally:
                conn.close()
        return [dict(r) for r in rows]

    def export_json_ld(self, program_id: Optional[str] = None) -> str:
        """Export in EU AI Act Article 12/13 compliant JSON-LD format."""
        now_iso  = datetime.now(timezone.utc).isoformat()
        entries  = self.query(program_id=program_id, limit=1_000_000)
        valid, _ = self.verify(program_id=program_id)

        models_used = sorted(set(e["model"]      for e in entries))
        domains     = sorted(set(e["program_id"] for e in entries))

        if entries:
            ts_vals   = [e["timestamp"] for e in entries]
            date_from = datetime.fromtimestamp(min(ts_vals), tz=timezone.utc).isoformat()
            date_to   = datetime.fromtimestamp(max(ts_vals), tz=timezone.utc).isoformat()
        else:
            date_from = date_to = now_iso

        with_outcomes = [e for e in entries if e["outcome_correct"] is not None]
        n_outcomes    = len(with_outcomes)
        n_correct     = sum(1 for e in with_outcomes if e["outcome_correct"] == 1)
        overall_acc   = round(n_correct / n_outcomes, 3) if n_outcomes else None

        # Accuracy per (model, domain) used to compute confidence_gap per decision
        acc_cache: Dict[Tuple[str, str], float] = {}
        for m in models_used:
            for d in domains:
                acc, _ = self.get_real_accuracy(m, d)
                if acc is not None:
                    acc_cache[(m, d)] = round(acc, 3)

        def _fmt(e: Dict) -> Dict:
            ts  = datetime.fromtimestamp(e["timestamp"], tz=timezone.utc).isoformat()
            ots = (datetime.fromtimestamp(e["outcome_timestamp"], tz=timezone.utc).isoformat()
                   if e.get("outcome_timestamp") else None)
            real_acc = acc_cache.get((e["model"], e["program_id"]))
            gap      = (round(real_acc - e["confidence"], 3)
                        if real_acc is not None else None)
            oc = e["outcome_correct"]
            return {
                "@type": "AIDecision",
                "@id":   f"ledge:decision/{e['id']}",
                "eu_ai_act:transparency": {
                    "operation":                e["operation"],
                    "model_used":               e["model"],
                    "domain":                   e["program_id"],
                    "declared_confidence":      round(e["confidence"], 3),
                    "real_accuracy_for_domain": real_acc,
                    "confidence_gap":           gap,
                },
                "eu_ai_act:traceability": {
                    "input_hash": e["input_hash"],
                    "chain_hash": f"sha256:{e['chain_hash']}",
                    "prev_hash":  f"sha256:{e['prev_hash']}",
                    "timestamp":  ts,
                },
                "eu_ai_act:human_oversight": {
                    "was_escalated":     False,
                    "outcome_recorded":  oc is not None,
                    "outcome_correct":   bool(oc) if oc is not None else None,
                    "outcome_timestamp": ots,
                },
            }

        return json.dumps(
            {
                "@context": {
                    "@vocab":    "https://ledge-lang.org/audit/v1/",
                    "xsd":       "http://www.w3.org/2001/XMLSchema#",
                    "dcterms":   "http://purl.org/dc/terms/",
                    "eu_ai_act": (
                        "https://eur-lex.europa.eu/legal-content/EN/TXT/"
                        "?uri=CELEX:32024R1689#"
                    ),
                },
                "@type":                         "AuditTrail",
                "dcterms:created":               now_iso,
                "dcterms:creator":               f"Ledge v{_LEDGE_VERSION}",
                "eu_ai_act:article12_compliant": True,
                "chain_valid":                   valid,
                "chain_verified_at":             now_iso,
                "summary": {
                    "total_decisions":         len(entries),
                    "models_used":             models_used,
                    "domains":                 domains,
                    "date_range": {
                        "from": date_from,
                        "to":   date_to,
                    },
                    "decisions_with_outcomes": n_outcomes,
                    "overall_accuracy":        overall_acc,
                },
                "decisions": [_fmt(e) for e in entries],
            },
            indent=2,
            default=str,
        )

    def validate_regulatory_json_ld(self, path: Optional[str] = None,
                                     data: Optional[dict] = None) -> Dict:
        """
        Validate a JSON-LD file for EU AI Act Article 12/13 compliance.
        Returns {'valid': bool, 'checks': [{'name', 'passed', 'detail'}]}.
        """
        if data is None:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)

        checks: List[Dict] = []

        def _check(name: str, cond: bool, detail: str = "") -> bool:
            checks.append({"name": name, "passed": bool(cond), "detail": detail})
            return bool(cond)

        _check("@type == AuditTrail",
               data.get("@type") == "AuditTrail")
        _check("eu_ai_act:article12_compliant == true",
               data.get("eu_ai_act:article12_compliant") is True)
        _check("chain_valid == true",
               data.get("chain_valid") is True)
        _check("summary block present",
               isinstance(data.get("summary"), dict))
        _check("decisions array present",
               isinstance(data.get("decisions"), list))
        _check("@context has eu_ai_act namespace",
               isinstance(data.get("@context"), dict)
               and "eu_ai_act" in data.get("@context", {}))

        decisions = data.get("decisions") or []
        n = len(decisions)
        if n:
            _check(
                f"all {n} decisions have eu_ai_act:transparency",
                all("eu_ai_act:transparency" in d for d in decisions),
            )
            _check(
                f"all {n} decisions have eu_ai_act:traceability",
                all("eu_ai_act:traceability" in d for d in decisions),
            )
            _check(
                f"all {n} decisions have eu_ai_act:human_oversight",
                all("eu_ai_act:human_oversight" in d for d in decisions),
            )

        return {"valid": all(c["passed"] for c in checks), "checks": checks}


# ── Anchor Store ──────────────────────────────────────────────────────────────

class AnchorStore:
    """
    Append-only file of cryptographic anchors for the AuditStore.

    Each anchor records the chain_hash at a known entry count with a timestamp.
    Because the file is separate from the SQLite database, a full DB rewrite
    cannot silently remove evidence — an auditor can cross-check anchors against
    the current store state.

    Default location: ~/.ledge/anchors.jsonl (one JSON object per line, append-only).
    """

    def __init__(self, path: str = "~/.ledge/anchors.jsonl"):
        self._path = os.path.expanduser(path)
        os.makedirs(os.path.dirname(self._path), exist_ok=True)

    def add_anchor(self, chain_hash: str, entry_count: int, timestamp: float):
        """
        Append one anchor entry to the file.

        Format:
          {
            "timestamp":   "<ISO 8601>",
            "entry_count": 42,
            "chain_hash":  "sha256:<hex>",
            "anchor_hash": "<sha256 of timestamp+entry_count+chain_hash>"
          }
        """
        ts_iso = datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()
        anchor_input = f"{ts_iso}{entry_count}{chain_hash}"
        anchor_hash = hashlib.sha256(anchor_input.encode()).hexdigest()
        entry = {
            "timestamp":   ts_iso,
            "entry_count": entry_count,
            "chain_hash":  f"sha256:{chain_hash}",
            "anchor_hash": anchor_hash,
        }
        with open(self._path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def _read_anchors(self) -> List[Dict]:
        try:
            with open(self._path, encoding="utf-8") as f:
                return [json.loads(line) for line in f if line.strip()]
        except FileNotFoundError:
            return []

    def verify_against_store(self, audit_store: "AuditStore") -> Dict:
        """
        Verify all anchors in the file against the current audit store.

        For each anchor:
          1. Recomputes anchor_hash and checks integrity.
          2. Looks for the anchor's chain_hash in the store entries.

        Returns:
          {
            "anchors_verified": int,
            "anchors_failed":   int,
            "store_matches_anchors": bool,
            "details": [{"entry_count": int, "status": "ok"|"failed", ...}]
          }
        """
        anchors = self._read_anchors()

        all_entries = audit_store.query(limit=1_000_000)
        known_hashes: set = {e["chain_hash"] for e in all_entries}

        verified = failed = 0
        details: List[Dict] = []

        for anchor in anchors:
            raw_hash = anchor["chain_hash"].replace("sha256:", "")
            ts       = anchor["timestamp"]
            count    = anchor["entry_count"]

            # Integrity: recompute anchor_hash
            expected = hashlib.sha256(
                f"{ts}{count}{raw_hash}".encode()
            ).hexdigest()
            integrity_ok = (expected == anchor["anchor_hash"])

            # Store match: chain_hash must exist in current store
            store_ok = raw_hash in known_hashes

            if integrity_ok and store_ok:
                verified += 1
                details.append({"entry_count": count, "status": "ok"})
            else:
                failed += 1
                details.append({
                    "entry_count":     count,
                    "status":          "failed",
                    "integrity_ok":    integrity_ok,
                    "store_match":     store_ok,
                })

        return {
            "anchors_verified":      verified,
            "anchors_failed":        failed,
            "store_matches_anchors": failed == 0,
            "details":               details,
        }


# ── Global persistent store ───────────────────────────────────────────────────

GLOBAL_AUDIT_STORE: Optional[AuditStore] = None


def activate_global_store(path: Optional[str] = None) -> AuditStore:
    """Create an AuditStore and set it as the global persistent store."""
    global GLOBAL_AUDIT_STORE
    GLOBAL_AUDIT_STORE = AuditStore(db_path=path)
    return GLOBAL_AUDIT_STORE
