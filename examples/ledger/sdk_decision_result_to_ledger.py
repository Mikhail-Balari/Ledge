"""End-to-end SDK DecisionResult to decision ledger example.

Synthetic source-checkout example only. This creates local review artifacts
from safe hashes and references; it does not store raw prompts, outputs, or
customer data.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ledge_lang.ledger import (
    DecisionLedger,
    LedgerRecordContext,
    build_ai_review_pack,
    build_manifest,
    export_ledger_review_package,
    record_decision_result,
    verify_ledger,
    write_ai_review_pack,
    write_manifest,
)
from ledge_lang.sdk import DecisionResult


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a low-stakes SDK DecisionResult ledger workflow example."
    )
    parser.add_argument(
        "--out",
        default="examples/ledger/out",
        help="output directory for generated example artifacts",
    )
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    ledger_path = out_dir / "support_ticket_ledger.jsonl"
    manifest_path = out_dir / "ledger_manifest.json"
    export_dir = out_dir / "audit_export"
    review_pack_path = out_dir / "ai_review_pack.json"

    # Low-stakes support-ticket routing result. The value is intentionally not
    # recorded by the ledger adapter; the ledger receives safe hashes only.
    result = DecisionResult(
        action="human_review",
        allowed=False,
        value={"internal_route": "tier_2_support"},
        confidence=0.74,
        reason="confidence below automated-routing threshold",
        policy_name="support_ticket_routing_shadow_policy",
        warnings=["confidence_below_auto_route_threshold"],
        metadata={"example": "source-checkout only"},
    )

    context = LedgerRecordContext(
        boundary_id="support_ticket_routing",
        boundary_version="support_ticket_routing.v1",
        policy_hash="sha256:demo_policy_hash_support_ticket_v1",
        redaction_profile="hash_only",
        trace_id="trace_demo_support_ticket_001",
        request_id="req_demo_support_ticket_001",
        service_name="support-routing-demo",
        environment="local_example",
    )

    event = record_decision_result(
        ledger_path,
        result,
        context=context,
        evidence_hash="sha256:demo_confidence_evidence_hash_001",
        input_hash="sha256:demo_redacted_input_hash_001",
        output_hash="sha256:demo_redacted_output_hash_001",
        policy_result="escalate",
        event_id="evt_support_ticket_demo_001",
        timestamp_utc="2026-06-14T12:00:00Z",
        initialize=True,
    )

    ledger = DecisionLedger(ledger_path)
    manifest = build_manifest(ledger)
    write_manifest(manifest, manifest_path)

    verification = verify_ledger(ledger_path, manifest_path)
    export_result = export_ledger_review_package(
        ledger_path,
        export_dir,
        manifest_path=manifest_path,
        force=True,
    )
    review_pack = build_ai_review_pack(ledger_path, manifest_path=manifest_path)
    write_ai_review_pack(review_pack, review_pack_path, force=True)

    summary = {
        "status": "ok",
        "ledger": str(ledger_path),
        "manifest": str(manifest_path),
        "audit_export": str(export_dir),
        "ai_review_pack": str(review_pack_path),
        "event_id": event.event_id,
        "sequence": event.sequence,
        "current_event_hash": event.current_event_hash,
        "verification_status": verification.status,
        "events_exported": export_result.events_exported,
    }
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
