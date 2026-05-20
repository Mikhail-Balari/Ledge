import os
import subprocess
import sys
import textwrap


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "ledge_lang.cli", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=20,
    )


def write_ledge(tmp_path, name, source):
    path = tmp_path / name
    path.write_text(textwrap.dedent(source).strip() + "\n", encoding="utf-8")
    return path


def test_run_rejects_unchecked_value_of_before_execution(tmp_path):
    program = write_ledge(
        tmp_path,
        "unsafe_value_of.ledge",
        """
        show "EXECUTED"
        define r as classify("message") using ["safe", "unsafe"]
        show value_of(r)
        """,
    )

    result = run_cli("run", str(program))
    combined = result.stdout + result.stderr

    assert result.returncode != 0
    assert "static typecheck failed" in result.stderr
    assert "value_of" in combined
    assert "EXECUTED" not in result.stdout


def test_run_unsafe_bypasses_typecheck_and_executes(tmp_path):
    program = write_ledge(
        tmp_path,
        "unsafe_value_of.ledge",
        """
        show "EXECUTED"
        define r as classify("message") using ["safe", "unsafe"]
        show value_of(r)
        """,
    )

    result = run_cli("run", str(program), "--unsafe")

    assert result.returncode == 0
    assert "EXECUTED" in result.stdout
    assert "nothing" in result.stdout
    assert "static typecheck failed" not in result.stderr


def test_check_types_behavior_is_unchanged(tmp_path):
    program = write_ledge(
        tmp_path,
        "unsafe_show.ledge",
        """
        define r as classify("message") using ["safe", "unsafe"]
        show r
        """,
    )

    result = run_cli("check", "--types", str(program))
    combined = result.stdout + result.stderr

    assert result.returncode != 0
    assert "Unsafe use of Uncertain value" in combined
    assert "static typecheck failed" not in combined


def test_check_types_accepts_utf8_bom_file(tmp_path):
    program = tmp_path / "bom_safe.ledge"
    program.write_text('show "ok"\n', encoding="utf-8-sig")

    check_result = run_cli("check", "--types", str(program))
    run_result = run_cli("run", str(program))

    assert check_result.returncode == 0
    assert "no type issues" in check_result.stdout
    assert run_result.returncode == 0
    assert run_result.stdout.strip() == "ok"


def test_demo_medical_triage_still_runs():
    result = run_cli("demo", "medical_triage")

    assert result.returncode == 0
    assert "=== MEDICAL TRIAGE DEMO ===" in result.stdout
    assert "ESCALATE TO HUMAN" in result.stdout
