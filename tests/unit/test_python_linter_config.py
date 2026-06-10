from pathlib import Path

import pytest

from ledge_lang.python_linter.config import LintConfig, LintConfigError, load_config


def test_missing_config_uses_defaults(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    config = load_config()

    assert isinstance(config, LintConfig)
    assert config.critical_actions == set()
    assert config.unsafe_unwrap_requires_reason is True


def test_config_loads_critical_actions(tmp_path):
    config_path = tmp_path / "ledge.toml"
    config_path.write_text(
        "\n".join(
            [
                "[ledge]",
                "min_confidence = 0.85",
                "",
                "[ledge.actions]",
                'critical = ["refund_customer", "send_email"]',
                "",
                "[ledge.allow]",
                "unsafe_unwrap_requires_reason = true",
            ]
        ),
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.min_confidence == 0.85
    assert config.critical_actions == {"refund_customer", "send_email"}
    assert config.unsafe_unwrap_requires_reason is True


def test_config_loads_utf8_bom_file(tmp_path):
    config_path = tmp_path / "ledge.toml"
    config_path.write_text(
        "\n".join(
            [
                "[ledge]",
                "min_confidence = 0.85",
                "",
                "[ledge.actions]",
                'critical = ["refund_customer"]',
            ]
        ),
        encoding="utf-8-sig",
    )

    config = load_config(config_path)

    assert config.min_confidence == 0.85
    assert config.critical_actions == {"refund_customer"}


def test_invalid_min_confidence_above_one_reports_clear_error(tmp_path):
    config_path = tmp_path / "ledge.toml"
    config_path.write_text("[ledge]\nmin_confidence = 1.5\n", encoding="utf-8")

    with pytest.raises(LintConfigError, match="min_confidence"):
        load_config(config_path)


def test_invalid_min_confidence_boolean_reports_clear_error(tmp_path):
    config_path = tmp_path / "ledge.toml"
    config_path.write_text("[ledge]\nmin_confidence = true\n", encoding="utf-8")

    with pytest.raises(LintConfigError, match="min_confidence"):
        load_config(config_path)


def test_invalid_min_confidence_string_reports_clear_error(tmp_path):
    config_path = tmp_path / "ledge.toml"
    config_path.write_text('[ledge]\nmin_confidence = "high"\n', encoding="utf-8")

    with pytest.raises(LintConfigError, match="min_confidence"):
        load_config(config_path)


def test_invalid_min_confidence_non_finite_reports_clear_error():
    with pytest.raises(LintConfigError, match="min_confidence"):
        LintConfig.from_mapping({"ledge": {"min_confidence": float("nan")}})

    with pytest.raises(LintConfigError, match="min_confidence"):
        LintConfig.from_mapping({"ledge": {"min_confidence": float("inf")}})


def test_invalid_config_reports_clear_error(tmp_path):
    config_path = tmp_path / "ledge.toml"
    config_path.write_text(
        "\n".join(
            [
                "[ledge.actions]",
                'critical = "refund_customer"',
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(LintConfigError, match="critical"):
        load_config(config_path)
