#!/usr/bin/env python3
"""
Ledge Domain Calibration Demo
==============================
Shows calibration metrics per (model, domain) pair.
Demonstrates that each domain is calibrated independently.

Run: py examples/showcase/calibration_demo.py
"""
import sys
import os
import tempfile
import hashlib
import uuid
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ledge_lang.audit_store import AuditStore
from ledge_lang.calibration import DomainCalibrator

SEP = "=" * 62


def show_metrics(cal, model, domain, label=""):
    m = cal.get_calibration_metrics(model, domain)
    if m is None:
        print(f"    {model} / {domain}: insufficient data (< 10 outcomes)")
        return
    prefix = f"  [{label}] " if label else "    "
    far_str = f"{m['false_accept_rate']:.4f}" if m["false_accept_rate"] is not None else "n/a"
    frr_str = f"{m['false_reject_rate']:.4f}" if m["false_reject_rate"] is not None else "n/a"
    print(f"{prefix}{model} / {domain}")
    print(f"      Brier score   : {m['brier_score']:.4f}  (perfect=0.0, random=0.25)")
    print(f"      ECE           : {m['ece']:.4f}  (well-calibrated < 0.10)")
    print(f"      False accept  : {far_str}  (accepted when wrong)")
    print(f"      False reject  : {frr_str}  (rejected when right)")
    print(f"      Threshold     : {m['threshold_used']:.3f}")
    print(f"      Sample size   : {m['sample_size']}")
    print(f"      Well cal.     : {m['well_calibrated']}")
    print(f"      Note          : {m['calibration_note']}")


def build_sim_store(scenarios):
    """Build a temporary AuditStore with simulated outcomes."""
    random.seed(42)
    tmp_path = os.path.join(tempfile.gettempdir(), f"ledge_cal_demo_{uuid.uuid4().hex[:8]}.db")
    store = AuditStore(db_path=tmp_path)

    for model, domain, real_acc, n_decisions in scenarios:
        for i in range(n_decisions):
            confidence = round(random.uniform(0.75, 0.98), 3)
            correct = 1 if random.random() < real_acc else 0
            ih = hashlib.sha256(f"{model}_{domain}_{i}".encode()).hexdigest()[:16]
            stored_id = store.record(
                operation="classify",
                input_hash=ih,
                output_type="text",
                confidence=confidence,
                model=model,
                program_id=domain,
            )
            store.record_outcome(stored_id, bool(correct))

    return store, DomainCalibrator(store)


def main():
    print(SEP)
    print("LEDGE DOMAIN CALIBRATION DEMO")
    print(SEP)

    # --- Part 1: Real data from the main audit store ---
    print("\n1. Real audit store — pairs with >= 10 outcomes\n")
    real_store = AuditStore()
    real_cal = DomainCalibrator(real_store)
    rows = real_store.stats()

    real_pairs = [
        (r["model"], r["program_id"])
        for r in rows
        if (r.get("with_outcome") or 0) >= 10
    ]

    if real_pairs:
        print(f"   Found {len(real_pairs)} qualifying pair(s):\n")
        for model, domain in real_pairs:
            show_metrics(real_cal, model, domain)
            print()
    else:
        print("   No pairs with >= 10 outcomes in the real store.\n")

    # --- Part 2: Simulation with 4 distinct domains ---
    scenarios = [
        ("gpt-4",  "medical",  0.65, 20),
        ("gpt-4",  "legal",    0.88, 20),
        ("claude", "hiring",   0.75, 20),
        ("claude", "phishing", 0.91, 20),
    ]

    print(SEP)
    print("\n2. Simulation — 4 domains, independent calibration\n")
    print("   Each (model, domain) pair has its own calibration data.")
    print("   No data leaks between domains.\n")

    sim_store, sim_cal = build_sim_store(scenarios)

    for model, domain, real_acc, n in scenarios:
        print(f"   Simulated: {model} / {domain}  "
              f"(target real accuracy ~{real_acc:.0%}, n={n})")
        show_metrics(sim_cal, model, domain)
        print()

    # --- Part 3: Explicit independence check for gpt-4 ---
    print(SEP)
    print("\n3. Domain independence: gpt-4/medical vs gpt-4/legal\n")
    print("   Same model — different domains — DIFFERENT calibrations.\n")

    m_med = sim_cal.get_calibration_metrics("gpt-4", "medical")
    m_leg = sim_cal.get_calibration_metrics("gpt-4", "legal")
    t_med = sim_cal.get_calibrated_threshold("gpt-4", "medical")["threshold"]
    t_leg = sim_cal.get_calibrated_threshold("gpt-4", "legal")["threshold"]

    print(f"   gpt-4 / medical:")
    print(f"     Brier={m_med['brier_score']:.4f}  "
          f"ECE={m_med['ece']:.4f}  "
          f"calibrated_threshold={t_med:.3f}")
    print(f"   gpt-4 / legal:")
    print(f"     Brier={m_leg['brier_score']:.4f}  "
          f"ECE={m_leg['ece']:.4f}  "
          f"calibrated_threshold={t_leg:.3f}")

    assert t_med != t_leg or m_med["brier_score"] != m_leg["brier_score"], \
        "Domains should have independent calibration"

    print()
    print("   Thresholds differ because real accuracy differs by domain.")
    print("   medical target ~65%  -> higher threshold needed to ensure safety")
    print("   legal target   ~88%  -> lower threshold sufficient")
    print()
    print(SEP)
    print("\nDemo complete.")


if __name__ == "__main__":
    main()
