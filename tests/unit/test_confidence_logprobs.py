import json
import math

import pytest

from ledge_lang.confidence import extract_logprob_signal


def warning_set(evidence):
    return set(evidence.warnings)


def test_logprobs_none_emits_unavailable_without_inventing_values():
    evidence = extract_logprob_signal(None, boundary_id="refund_route")

    assert evidence.score == 0.0
    assert "logprobs_unavailable" in warning_set(evidence)
    assert evidence.sources[0].status == "unavailable"
    assert evidence.sources[0].score is None
    assert evidence.sources[0].details["logprobs_provided"] is False


def test_numeric_logprob_list_produces_deterministic_summary():
    evidence = extract_logprob_signal([-0.1, -0.2, -0.3], boundary_id="refund_route")
    details = evidence.sources[0].details

    assert evidence.sources[0].status == "passed"
    assert details["count"] == 3
    assert details["mean_logprob"] == pytest.approx(-0.2)
    assert math.isfinite(details["mean_logprob"])
    assert details["min_logprob"] == -0.3
    assert details["max_logprob"] == -0.1
    assert 0.0 < evidence.score <= 1.0


def test_dict_logprob_list_works_and_hashes_tokens_without_raw_text():
    evidence = extract_logprob_signal(
        [
            {"token": "private_token_alpha", "logprob": -0.1},
            {"token": "private_token_beta", "logprob": -0.4},
        ],
        boundary_id="refund_route",
    )
    rendered = json.dumps(evidence.to_dict(), sort_keys=True)

    assert evidence.sources[0].details["count"] == 2
    assert len(evidence.sources[0].details["token_hashes"]) == 2
    assert evidence.sources[0].details["raw_token_text_stored"] is False
    assert "private_token_alpha" not in rendered
    assert "private_token_beta" not in rendered


def test_provider_style_dict_payload_uses_nested_logprobs():
    evidence = extract_logprob_signal(
        {"logprobs": [{"token": "ok", "logprob": -0.2}]},
        boundary_id="refund_route",
    )

    assert evidence.sources[0].details["count"] == 1
    assert evidence.sources[0].details["invalid_count"] == 0


def test_bool_nan_inf_and_non_numeric_values_are_warned_and_skipped():
    evidence = extract_logprob_signal(
        [True, float("nan"), float("inf"), "bad", -0.2],
        boundary_id="refund_route",
    )
    details = evidence.sources[0].details

    assert "invalid_logprob_value" in warning_set(evidence)
    assert evidence.sources[0].status == "warning"
    assert details["count"] == 1
    assert details["invalid_count"] == 4


def test_all_invalid_logprobs_fail_to_zero():
    evidence = extract_logprob_signal(
        [True, float("nan"), "bad"],
        boundary_id="refund_route",
    )

    assert evidence.score == 0.0
    assert evidence.sources[0].status == "failed"
    assert "logprobs_invalid" in warning_set(evidence)


def test_positive_logprob_score_is_clamped_without_overflow():
    evidence = extract_logprob_signal([1000.0], boundary_id="refund_route")

    assert evidence.score == 1.0


def test_logprob_evidence_is_hashable_and_canonical_serializable():
    evidence = extract_logprob_signal([-0.1, -0.2], boundary_id="refund_route")

    assert evidence.evidence_hash == evidence.compute_hash()
    assert evidence.to_canonical_json() == evidence.to_canonical_json()
