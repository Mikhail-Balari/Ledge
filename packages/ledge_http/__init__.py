"""
ledge_http — HTTP utilities for Ledge
=======================================
Simple HTTP client for Ledge programs.

Usage:
    import "python:ledge_http" as http
    define response as http["get"]("https://api.example.com/data")
    define data as response["json"]()
"""
import urllib.request, json

LEDGE_PACKAGE = "ledge_http"
VERSION = "1.0.0"

class Response:
    def __init__(self, status, body, headers):
        self.status = status
        self._body = body
        self.headers = headers

    def text(self):
        return self._body.decode("utf-8")

    def json(self):
        return json.loads(self._body)

    def __getitem__(self, key):
        if key == "status": return self.status
        if key == "text": return self.text()
        if key == "json": return self.json()
        return None

def get(url, headers=None, timeout=10):
    """Make a GET request."""
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return Response(resp.status, resp.read(), dict(resp.headers))
    except Exception as e:
        return {"error": str(e), "status": 0}

def post(url, body=None, headers=None, timeout=10):
    """Make a POST request."""
    data = json.dumps(body).encode() if isinstance(body, dict) else (body or b"")
    hdrs = {"Content-Type": "application/json", **(headers or {})}
    req = urllib.request.Request(url, data=data, headers=hdrs, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return Response(resp.status, resp.read(), dict(resp.headers))
    except Exception as e:
        return {"error": str(e), "status": 0}
