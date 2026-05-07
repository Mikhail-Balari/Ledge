"""
Ledge Studio — in-browser IDE for Ledge programs.

Start with:  ledge studio
             python -m ledge_lang.studio.server
"""

import os
import sys
import glob
import threading
import webbrowser

# ── Flask / flask-socketio ────────────────────────────────────────────────────

try:
    from flask import Flask, render_template, request, jsonify
    from flask_socketio import SocketIO, emit
except ImportError:
    print("Ledge Studio requires: pip install ledge-lang[studio]")
    sys.exit(1)

# ── App setup ─────────────────────────────────────────────────────────────────

_TMPL_DIR = os.path.join(os.path.dirname(__file__), "templates")

app = Flask(__name__, template_folder=_TMPL_DIR)
app.config["SECRET_KEY"] = "ledge-studio-2026"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# Working directory is captured when start_studio() is called, not at import time.
WORKING_DIR = os.getcwd()


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("studio.html")


@app.route("/favicon.ico")
def favicon():
    return "", 204


@app.route("/api/files")
def api_files():
    pattern = os.path.join(WORKING_DIR, "*.ledge")
    files = sorted(os.path.basename(p) for p in glob.glob(pattern))
    return jsonify({"files": files})


@app.route("/api/file/<name>")
def api_file(name):
    name = os.path.basename(name)          # strip any path components
    if not name.endswith(".ledge"):
        return jsonify({"error": "invalid filename"}), 400
    path = os.path.join(WORKING_DIR, name)
    if not os.path.exists(path):
        return jsonify({"error": "not found"}), 404
    with open(path, encoding="utf-8") as f:
        return jsonify({"content": f.read()})


@app.route("/api/check", methods=["POST"])
def api_check():
    code = (request.json or {}).get("code", "")
    try:
        from ledge_lang.typechecker import check_types
        issues = check_types(code)
        return jsonify({"issues": [
            {"message": i.message, "line": getattr(i, "line", 0), "is_error": i.is_error}
            for i in issues
        ]})
    except Exception as exc:
        return jsonify({"issues": [{"message": str(exc), "line": 0, "is_error": True}]})


@app.route("/api/guarantees")
def api_guarantees():
    from ledge_lang import run as ledge_run
    from ledge_lang.typechecker import check_types
    from ledge_lang.ai_types import GLOBAL_AUDIT

    results = {}

    # G1 — confidence=0 always without backend
    try:
        lines, _ = ledge_run(
            'define r as classify("x") using ["a","b"]\nshow confidence_of(r)',
            output_fn=lambda _: None, reset_audit=True,
        )
        results["G1"] = lines[0] == "0"
    except Exception:
        results["G1"] = False

    # G2 — typechecker blocks unsafe AI use
    try:
        issues = check_types('define r as classify("x") using ["a","b"]\nshow r')
        results["G2"] = any(i.is_error for i in issues)
    except Exception:
        results["G2"] = False

    # G3 — cryptographic audit trail detects tampering
    try:
        ledge_run(
            'define r1 as classify("x") using ["a","b"]',
            output_fn=lambda _: None, reset_audit=True,
        )
        ok_before = GLOBAL_AUDIT.verify()
        saved = GLOBAL_AUDIT._entries[0]["confidence"]
        GLOBAL_AUDIT._entries[0]["confidence"] = 0.99
        ok_after = GLOBAL_AUDIT.verify()
        GLOBAL_AUDIT._entries[0]["confidence"] = saved
        results["G3"] = ok_before and not ok_after
    except Exception:
        results["G3"] = False

    # G4 — safe failure: no backend → is_confident returns false
    try:
        lines, _ = ledge_run(
            'define r as classify("x") using ["a","b"]\nshow is_confident(r)',
            output_fn=lambda _: None, reset_audit=True,
        )
        results["G4"] = lines[0] == "false"
    except Exception:
        results["G4"] = False

    return jsonify(results)


# ── WebSocket: streaming run ──────────────────────────────────────────────────

@socketio.on("run")
def handle_run(data):
    code = (data or {}).get("code", "")
    try:
        from ledge_lang import run as ledge_run

        def output_fn(line):
            emit("output", {"line": line})
            socketio.sleep(0)   # yield so the emit is flushed immediately

        ledge_run(code, output_fn=output_fn, reset_audit=True)
        emit("done", {"error": None})
    except Exception as exc:
        emit("done", {"error": str(exc)})


# ── Entry point ───────────────────────────────────────────────────────────────

def start_studio(host="127.0.0.1", port=5000, working_dir=None, open_browser=True):
    global WORKING_DIR
    if working_dir:
        WORKING_DIR = working_dir

    if open_browser:
        def _open_browser():
            import time
            time.sleep(0.9)
            webbrowser.open(f"http://{host}:{port}")
        threading.Thread(target=_open_browser, daemon=True).start()

    print(f"Ledge Studio v1.1.0")
    print(f"Working directory : {WORKING_DIR}")
    print(f"URL               : http://{host}:{port}")
    print(f"Press Ctrl+C to stop.\n")

    socketio.run(app, host=host, port=port, debug=False, allow_unsafe_werkzeug=True)


if __name__ == "__main__":
    start_studio()
