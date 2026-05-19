#!/usr/bin/env python3
"""
ledge - Ledge programming language toolchain

Usage:
  ledge                        Start interactive REPL
  ledge run <file.ledge>       Typecheck, then run a Ledge program
  ledge run <file.ledge> --unsafe
                               Skip static typechecking and run anyway
  ledge demo [name]            List or run a bundled demo (works after `pip install`,
                               no clone needed). `ledge demo` lists available demos;
                               `ledge demo medical_triage` runs that demo.
  ledge check <file.ledge>     Check syntax without running
  ledge fmt <file.ledge>       Format source (canonical style)
  ledge fmt --check <file>     Check formatting without modifying
  ledge debug <file.ledge>     Interactive step-through debugger
  ledge test [dir]             Run .ledge test files
  ledge studio                 Launch Ledge Studio (web IDE) at http://localhost:5000
  ledge audit --show                        Show last 20 decisions from the persistent store
  ledge audit --verify                      Verify cryptographic chain integrity
  ledge audit --verify-anchors              Cross-check external anchor file against the store
  ledge audit --export <file>               Export all decisions as JSON-LD
  ledge audit --stats                       Show real accuracy by model and domain
  ledge audit --calibration <model> <domain>            Calibration report for a model/domain
  ledge audit --calibration-metrics <model> <domain>   Brier score, ECE, and reliability table
  ledge audit --compare <model_a> <model_b> <domain>            Compare two models for migration risk
  ledge audit --export-regulatory <file> [--program <id>]      Export EU AI Act JSON-LD report
  ledge audit --validate-regulatory <file>                     Validate a JSON-LD report
  ledge version                Show version info
  ledge help                   Show this help

Examples:
  ledge run hello.ledge
  ledge run unsafe_experiment.ledge --unsafe
  ledge fmt program.ledge
  ledge debug --break 10 program.ledge
  ledge check *.ledge
  ledge studio
"""

import sys
import os


def main():
    args = sys.argv[1:]

    if not args or args[0] in ("help", "--help", "-h"):
        print(__doc__)
        return

    if args[0] in ("version", "--version", "-v"):
        from ledge_lang import __version__
        import platform
        print(f"Ledge {__version__}")
        print(f"Python {platform.python_version()} on {platform.system()}")
        print(f"Interpreter: tree-walker + bytecode VM")
        return

    if args[0] == "run":
        if len(args) < 2:
            print("Usage: ledge run <file.ledge> [--unsafe]"); sys.exit(1)
        target = args[1]
        if not target.endswith(".ledge") and not os.path.isfile(target):
            _run_nl(target, extra_args=args[2:])
        else:
            _run_file(target, extra_args=args[2:])
        return

    if args[0] == "demo":
        _demo(args[1:])
        return

    if args[0] == "check":
        if len(args) < 2:
            print("Usage: ledge check [--lint] [--types] <file.ledge>"); sys.exit(1)
        lint_mode  = "--lint"  in args
        types_mode = "--types" in args
        files = [a for a in args[1:] if not a.startswith("--")]
        if lint_mode:
            from .linter import lint_file, LintIssue
            any_issue = False
            for path in files:
                issues = lint_file(path)
                if issues:
                    any_issue = True
                    for issue in issues:
                        print(str(issue))
                else:
                    print(f"{path}: no lint issues")
            if any_issue: sys.exit(1)
        elif types_mode:
            from .typechecker import check_file
            any_issue = False
            for path in files:
                issues = check_file(path)
                if issues:
                    any_issue = True
                    for issue in issues:
                        print(str(issue))
                else:
                    print(f"{path}: no type issues")
            if any_issue: sys.exit(1)
        else:
            _check_files(files)
        return

    if args[0] == "fmt":
        from ledge_lang.formatter import main as fmt_main
        sys.argv = ["ledge fmt"] + args[1:]
        fmt_main()
        return

    if args[0] == "debug":
        _debug(args[1:])
        return

    if args[0] == "test":
        _run_tests(args[1:])
        return

    if args[0] == "studio":
        _studio(args[1:])
        return

    if args[0] == "audit":
        _audit(args[1:])
        return

    if args[0] == "bench":
        import subprocess
        bench_path = os.path.join(os.path.dirname(__file__), "..", "benchmarks", "compare.py")
        if os.path.exists(bench_path):
            subprocess.run([sys.executable, bench_path])
        else:
            print("Benchmark suite not found")
        return

    # No subcommand: file path -> run it, or start REPL
    if os.path.isfile(args[0]):
        _run_file(args[0], extra_args=args[1:])
    else:
        _repl()


def _demo(args):
    """List or run a bundled demo. Works after `pip install ledge-lang` -
    no need to clone the repository."""
    from ledge_lang.demos import list_demos, demo_path

    if not args:
        names = list_demos()
        if not names:
            print("ledge demo: no bundled demos found")
            sys.exit(1)
        print("Bundled demos (run with `ledge demo <name>`):")
        for n in names:
            print(f"  {n}")
        return

    name = args[0]
    path = demo_path(name)
    if not path:
        print(f"ledge demo: unknown demo '{name}'", file=sys.stderr)
        print("Run `ledge demo` (no argument) to list available demos.",
              file=sys.stderr)
        sys.exit(1)
    _run_file(path, extra_args=args[1:])


def _run_file(path, extra_args=None):
    if not os.path.exists(path):
        print(f"ledge: file not found: {path}", file=sys.stderr)
        sys.exit(1)
    
    # Parse extra flags
    extra_args = extra_args or []
    unsafe = "--unsafe" in extra_args
    restrict_ffi = "--restrict-ffi" in extra_args or "--safe-mode" in extra_args
    safe_mode = "--safe-mode" in extra_args
    allowed_modules = None
    max_iterations = None
    
    for i, arg in enumerate(extra_args):
        if arg == "--allow-import" and i+1 < len(extra_args):
            allowed_modules = [m.strip() for m in extra_args[i+1].split(",")]
        elif arg.startswith("--allow-import="):
            allowed_modules = [m.strip() for m in arg[15:].split(",")]
        elif arg.startswith("--max-iterations="):
            try: max_iterations = int(arg[17:])
            except ValueError: pass
    
    if restrict_ffi and allowed_modules is None:
        allowed_modules = []  # block all by default with --restrict-ffi
    
    if safe_mode:
        # --safe-mode enables: FFI blocked, iteration limit 100k, no subprocess
        if allowed_modules is None:
            allowed_modules = ["math", "json", "re", "datetime", "collections", "itertools"]
        if max_iterations is None:
            max_iterations = 100_000

    if not unsafe:
        from ledge_lang.typechecker import check_file
        issues = check_file(path)
        if issues:
            print(
                "ledge: static typecheck failed; refusing to run. "
                "Use --unsafe to execute anyway.",
                file=sys.stderr
            )
            for issue in issues:
                print(str(issue), file=sys.stderr)
            sys.exit(1)
    
    from ledge_lang import LexError, ParseError, compile_ledge
    from ledge_lang.interpreter import Interpreter, LedgeError
    try:
        with open(path, encoding="utf-8") as f:
            source = f.read()
        ast = compile_ledge(source)
        interp = Interpreter(output_fn=print, source=source)
        if allowed_modules is not None:
            interp._allowed_modules = set(allowed_modules)
        if max_iterations is not None:
            interp._max_iterations = max_iterations
        interp.run(ast)
    except (LexError, ParseError) as e:
        print(f"ledge: syntax error\n  {e}", file=sys.stderr)
        sys.exit(1)
    except LedgeError as e:
        print(f"ledge: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nledge: interrupted")
        sys.exit(0)


def _check_files(paths):
    from ledge_lang import LexError, ParseError, compile_ledge
    errors = 0
    for path in paths:
        import glob
        for p in (glob.glob(path) if '*' in path else [path]):
            if not os.path.exists(p):
                print(f"ledge: not found: {p}", file=sys.stderr)
                errors += 1
                continue
            try:
                with open(p, encoding="utf-8") as f:
                    source = f.read()
                compile_ledge(source)
                print(f"OK: {p}")
            except (LexError, ParseError) as e:
                print(f"FAIL: {p}: {e}", file=sys.stderr)
                errors += 1
    sys.exit(errors)


def _debug(args):
    import argparse
    parser = argparse.ArgumentParser(prog="ledge debug")
    parser.add_argument("file", help=".ledge file to debug")
    parser.add_argument("--break", "-b", dest="breaks", action="append",
                        type=int, default=[], help="Breakpoint at line N")
    parser.add_argument("--run", "-r", action="store_true",
                        help="Run to first breakpoint")
    opts = parser.parse_args(args)
    
    if not os.path.exists(opts.file):
        print(f"ledge debug: not found: {opts.file}"); sys.exit(1)
    
    with open(opts.file, encoding="utf-8") as f:
        source = f.read()
    
    from ledge_lang.debugger import Debugger
    dbg = Debugger(source=source, source_path=opts.file)
    for bp in opts.breaks:
        dbg.breakpoints.add(bp)
    if opts.run:
        dbg.step_mode = False
    dbg.run()


def _run_tests(args):
    """Run Ledge's own test files."""
    import glob, subprocess
    
    test_dir = args[0] if args else "tests"
    
    if not os.path.exists(test_dir):
        print(f"ledge test: directory not found: {test_dir}"); sys.exit(1)
    
    # Run Python test files
    py_tests = glob.glob(os.path.join(test_dir, "test_*.py"))
    py_tests += glob.glob(os.path.join(test_dir, "conformance.py"))
    
    passed = failed = 0
    for test_file in sorted(py_tests):
        result = subprocess.run([sys.executable, test_file], capture_output=True, text=True)
        if result.returncode == 0:
            passed += 1
            print(f"PASS: {os.path.basename(test_file)}")
        else:
            failed += 1
            print(f"FAIL: {os.path.basename(test_file)}")
            if result.stdout:
                for line in result.stdout.split('\n')[-5:]:
                    if line: print(f"  {line}")
    
    print(f"\n{passed + failed} test suites: {passed} passed, {failed} failed")
    sys.exit(failed)


def _audit(args):
    from ledge_lang.audit_store import AuditStore
    store = AuditStore()

    if not args or "--show" in args:
        decisions = store.query(limit=20)
        if not decisions:
            print("No decisions recorded yet.")
            return
        print(f"{'ID':>14}  {'OPERATION':10}  {'CONF':5}  {'MODEL':12}  {'PROGRAM':16}  OUTCOME")
        print("-" * 78)
        for d in decisions:
            import datetime as _dt
            ts = _dt.datetime.fromtimestamp(d["timestamp"]).strftime("%H:%M:%S")
            outcome = ""
            if d["outcome_correct"] is not None:
                outcome = "OK" if d["outcome_correct"] else "WRONG"
            print(f"  {d['id'][:12]}  {d['operation'][:10]:10}  {d['confidence']:.3f}  "
                  f"{d['model'][:12]:12}  {d['program_id'][:16]:16}  {outcome}")
        return

    if "--verify" in args:
        valid, bad_id = store.verify()
        if valid:
            print("Chain valid: True  - all entries intact.")
        else:
            print(f"Chain valid: False - first invalid entry: {bad_id}")
        return

    if "--verify-anchors" in args:
        from ledge_lang.audit_store import AnchorStore
        anchor_store = AnchorStore()
        result = anchor_store.verify_against_store(store)
        print(f"Anchors verified : {result['anchors_verified']}")
        print(f"Anchors failed   : {result['anchors_failed']}")
        print(f"Store matches    : {result['store_matches_anchors']}")
        if result["details"]:
            print()
            print(f"  {'ENTRY_COUNT':>12}  {'STATUS':8}  DETAIL")
            print("  " + "-" * 48)
            for d in result["details"]:
                detail = ""
                if d["status"] == "failed":
                    detail = (f"integrity={'ok' if d.get('integrity_ok') else 'FAIL'}  "
                              f"store_match={'ok' if d.get('store_match') else 'MISS'}")
                print(f"  {d['entry_count']:>12}  {d['status']:8}  {detail}")
        if result["anchors_failed"] > 0:
            import sys as _sys
            _sys.exit(1)
        return

    if "--export" in args:
        idx = args.index("--export")
        out_path = args[idx + 1] if idx + 1 < len(args) else "audit.json"
        data = store.export_json_ld()
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(data)
        print(f"Exported to {out_path}")
        return

    if "--stats" in args:
        rows = store.stats()
        if not rows:
            print("No decisions recorded yet.")
            return
        print(f"{'MODEL':16}  {'DOMAIN':18}  {'TOTAL':6}  {'AVG_CONF':8}  {'WITH_OUT':8}  {'ACC':6}")
        print("-" * 72)
        for r in rows:
            n_out = r["with_outcome"] or 0
            n_ok  = r["correct"] or 0
            acc   = f"{n_ok/n_out:.1%}" if n_out else "-"
            print(f"  {r['model'][:14]:14}  {r['program_id'][:16]:16}  "
                  f"{r['total']:6}  {r['avg_confidence']:8.3f}  "
                  f"{n_out:8}  {acc:>6}")
        return

    if "--compare" in args:
        idx = args.index("--compare")
        if idx + 3 >= len(args):
            print("Usage: ledge audit --compare <model_a> <model_b> <domain>")
            return
        model_a = args[idx + 1]
        model_b = args[idx + 2]
        domain  = args[idx + 3]
        from ledge_lang.comparison import ModelMigrationAnalyzer
        analyzer = ModelMigrationAnalyzer(store)
        cmp  = analyzer.compare_models(model_a, model_b, program_id=domain)
        risk = analyzer.migration_risk(model_a, model_b, program_id=domain)

        print(f"Model Comparison: {model_a} vs {model_b} / {domain}")
        print(f"  Total decisions ({model_a}): {cmp['total_decisions_a']}")
        print(f"  Total decisions ({model_b}): {cmp['total_decisions_b']}")
        print(f"  Comparable pairs           : {cmp['comparable_pairs']}")
        print(f"  Would have differed        : {cmp['would_have_differed']}  "
              f"(diff_rate={cmp['diff_rate']:.3f})")

        acc_a = cmp['model_a_accuracy']
        acc_b = cmp['model_b_accuracy']
        print(f"  Accuracy {model_a:<12}: "
              f"{acc_a:.3f}" if acc_a is not None else f"  Accuracy {model_a:<12}: n/a")
        print(f"  Accuracy {model_b:<12}: "
              f"{acc_b:.3f}" if acc_b is not None else f"  Accuracy {model_b:<12}: n/a")
        print(f"  Recommendation             : {cmp['recommendation'] or 'tied'}")
        print(f"  Safe to migrate            : {cmp['safe_to_migrate']}")
        print()
        print(f"Migration risk: {model_a} -> {model_b}")
        print(f"  Risk level                 : {risk['risk_level']}")
        print(f"  Decisions that would change: {risk['decisions_that_would_change']}")
        print(f"  Would improve              : {risk['decisions_that_would_improve']}")
        print(f"  Would regress              : {risk['decisions_that_would_regress']}")
        nc = risk['net_accuracy_change']
        print(f"  Net accuracy change        : "
              f"{nc:+.3f}" if nc is not None else f"  Net accuracy change        : n/a")
        print(f"  Recommendation             : {risk['recommendation']}")
        if cmp['critical_differences']:
            print()
            print(f"  Critical differences (first {min(5, len(cmp['critical_differences']))}):")
            for d in cmp['critical_differences'][:5]:
                a_mark = "OK" if d['model_a_correct'] else "WRONG"
                b_mark = "OK" if d['model_b_correct'] else "WRONG"
                print(f"    {d['input_hash'][:16]:16}  "
                      f"{model_a}={a_mark}  {model_b}={b_mark}  "
                      f"conf=({d['model_a_confidence']:.3f}/{d['model_b_confidence']:.3f})")
        return

    if "--export-regulatory" in args:
        idx = args.index("--export-regulatory")
        out_path = args[idx + 1] if idx + 1 < len(args) and not args[idx + 1].startswith("--") else "regulatory_audit.json"
        pid = None
        if "--program" in args:
            pidx = args.index("--program")
            pid = args[pidx + 1] if pidx + 1 < len(args) else None
        import json as _json
        out_dir = os.path.dirname(os.path.abspath(out_path))
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        data = store.export_json_ld(program_id=pid)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(data)
        parsed = _json.loads(data)
        s = parsed["summary"]
        print(f"Exported regulatory report to {out_path}")
        print(f"  Format           : EU AI Act Article 12/13 JSON-LD")
        print(f"  Total decisions  : {s['total_decisions']}")
        print(f"  Models used      : {', '.join(s['models_used']) or '(none)'}")
        print(f"  Domains          : {', '.join(s['domains']) or '(none)'}")
        print(f"  Chain valid      : {parsed['chain_valid']}")
        print(f"  Article 12       : {parsed['eu_ai_act:article12_compliant']}")
        if s["overall_accuracy"] is not None:
            print(f"  Overall accuracy : {s['overall_accuracy']:.1%}")
        return

    if "--validate-regulatory" in args:
        idx = args.index("--validate-regulatory")
        in_path = args[idx + 1] if idx + 1 < len(args) else None
        if not in_path or not os.path.exists(in_path):
            print(f"ledge: file not found: {in_path}", file=sys.stderr)
            sys.exit(1)
        result = store.validate_regulatory_json_ld(path=in_path)
        print(f"Validating: {in_path}")
        for c in result["checks"]:
            mark = "OK  " if c["passed"] else "FAIL"
            print(f"  [{mark}] {c['name']}")
        print()
        if result["valid"]:
            print("VALIDATION PASSED - EU AI Act Article 12/13 evidence fields present")
        else:
            failed = [c["name"] for c in result["checks"] if not c["passed"]]
            print(f"VALIDATION FAILED - {len(failed)} check(s) failed: {', '.join(failed)}")
            sys.exit(1)
        return

    if "--calibration-metrics" in args:
        idx = args.index("--calibration-metrics")
        if idx + 2 >= len(args):
            print("Usage: ledge audit --calibration-metrics <model> <domain>")
            return
        model  = args[idx + 1]
        domain = args[idx + 2]
        from ledge_lang.calibration import DomainCalibrator
        cal     = DomainCalibrator(store)
        metrics = cal.get_calibration_metrics(model, domain)

        print(f"Calibration Metrics: {model} / {domain}")
        if metrics is None:
            print("  Not enough outcome data (need at least 10 recorded outcomes).")
            return
        far_str = f"{metrics['false_accept_rate']:.4f}" if metrics["false_accept_rate"] is not None else "n/a"
        frr_str = f"{metrics['false_reject_rate']:.4f}" if metrics["false_reject_rate"] is not None else "n/a"
        print(f"  Brier score          : {metrics['brier_score']:.4f}  "
              f"(perfect=0.0, random=0.25)")
        print(f"  ECE                  : {metrics['ece']:.4f}  "
              f"(perfect=0.0, well-calibrated < 0.10)")
        print(f"  False accept rate    : {far_str}  "
              f"(accepted when wrong, at threshold {metrics['threshold_used']:.3f})")
        print(f"  False reject rate    : {frr_str}  "
              f"(rejected when right, at threshold {metrics['threshold_used']:.3f})")
        print(f"  Sample size          : {metrics['sample_size']}")
        print(f"  Threshold used       : {metrics['threshold_used']:.3f}")
        print(f"  Well calibrated      : {metrics['well_calibrated']}")
        print(f"  Note                 : {metrics['calibration_note']}")
        print()
        if metrics["reliability_table"]:
            print(f"  {'BUCKET':12}  {'COUNT':>6}  {'MEAN_CONF':>10}  "
                  f"{'ACCURACY':>10}  {'CAL_ERROR':>10}")
            print("  " + "-" * 58)
            for row in metrics["reliability_table"]:
                gap = row["mean_confidence"] - row["real_accuracy"]
                flag = " <- overconfident" if gap > 0.1 else (
                       " <- underconfident" if gap < -0.1 else "")
                print(f"  {row['bucket']:12}  {row['count']:>6}  "
                      f"{row['mean_confidence']:>10.3f}  "
                      f"{row['real_accuracy']:>10.3f}  "
                      f"{row['calibration_error']:>10.3f}{flag}")
        return

    if "--calibration" in args:
        idx = args.index("--calibration")
        if idx + 2 >= len(args):
            print("Usage: ledge audit --calibration <model> <domain>")
            return
        model  = args[idx + 1]
        domain = args[idx + 2]
        from ledge_lang.calibration import DomainCalibrator
        cal = DomainCalibrator(store)

        report    = cal.get_calibration_report(model, domain)
        threshold = cal.get_calibrated_threshold(model, domain)
        trustworthy = cal.is_model_trustworthy(model, domain)

        print(f"Calibration Report: {model} / {domain}")
        if report:
            print(f"  {'RANGE':10}  {'COUNT':>6}  {'ACCURACY':>10}  {'CAL_ERROR':>10}")
            print("  " + "-" * 44)
            for b in report:
                print(f"  {b['range']:10}  {b['count']:>6}  "
                      f"{b['accuracy']:>10.3f}  {b['calibration_error']:>10.3f}")
        else:
            print("  No outcomes recorded for this model/domain.")
        print()
        cal_flag = threshold["calibrated"]
        n        = threshold["sample_size"]
        thr      = threshold["threshold"]
        acc_at   = threshold["actual_accuracy_at_threshold"]
        acc_str  = f"{acc_at:.3f}" if acc_at is not None else "n/a"
        print(f"  Calibrated threshold : {thr:.3f}  "
              f"(calibrated={cal_flag}, n={n}, accuracy_at_threshold={acc_str})")
        if threshold.get("warning"):
            print(f"  Warning              : {threshold['warning']}")
        print(f"  Model trustworthy    : {trustworthy}")
        return

    print("Usage: ledge audit [--show | --verify | --verify-anchors | --export <file> | --stats | --calibration <model> <domain> | --calibration-metrics <model> <domain>]")


def _studio(args):
    try:
        from ledge_lang.studio.server import start_studio
    except ImportError:
        print("Ledge Studio requires: pip install ledge-lang[studio]")
        sys.exit(1)
    port = 5000
    open_browser = "--no-browser" not in args
    for a in args:
        if a.startswith("--port="):
            try:
                port = int(a[7:])
            except ValueError:
                pass
    start_studio(working_dir=os.getcwd(), port=port, open_browser=open_browser)


def _run_nl(text, extra_args=None):
    """Run a natural-language description as a Ledge program."""
    from ledge_lang.nl_interface import NaturalLanguageInterface
    extra_args = extra_args or []

    save_path = None
    if "--save" in extra_args:
        idx = extra_args.index("--save")
        if idx + 1 < len(extra_args):
            save_path = extra_args[idx + 1]

    nl = NaturalLanguageInterface()
    program = nl.generate_ledge_program(text)

    print("# Generated Ledge program:")
    print(program)
    print()

    if save_path:
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(program)
        print(f"# Saved to {save_path}")
        print()

    print("# Running:")
    from ledge_lang import LexError, ParseError, compile_ledge
    from ledge_lang.interpreter import Interpreter, LedgeError
    try:
        ast = compile_ledge(program)
        interp = Interpreter(output_fn=print, source=program)
        interp.run(ast)
    except (LexError, ParseError) as e:
        print(f"ledge: syntax error in generated program\n  {e}", file=sys.stderr)
        sys.exit(1)
    except LedgeError as e:
        print(f"ledge: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nledge: interrupted")
        sys.exit(0)


def _repl():
    from ledge_lang import LedgeREPL
    LedgeREPL().run()


if __name__ == "__main__":
    main()
