"""
ledge_metrics — Metrics collection for Ledge AI pipelines
Track accuracy, latency, and confidence distribution.
"""
import time

LEDGE_PACKAGE = "ledge_metrics"
VERSION = "1.0.0"

_metrics = {"calls": 0, "errors": 0, "latency_ms": [], "confidence": []}

def record_call(latency_ms, confidence=None, error=False):
    _metrics["calls"] += 1
    if error: _metrics["errors"] += 1
    _metrics["latency_ms"].append(float(latency_ms))
    if confidence is not None:
        _metrics["confidence"].append(float(confidence))

def avg_latency():
    lats = _metrics["latency_ms"]
    return sum(lats)/len(lats) if lats else 0.0

def p95_latency():
    lats = sorted(_metrics["latency_ms"])
    if not lats: return 0.0
    return lats[int(len(lats)*0.95)]

def avg_confidence():
    confs = _metrics["confidence"]
    return sum(confs)/len(confs) if confs else 0.0

def error_rate():
    return _metrics["errors"] / _metrics["calls"] if _metrics["calls"] > 0 else 0.0

def summary():
    return {
        "calls": _metrics["calls"],
        "error_rate": error_rate(),
        "avg_latency_ms": avg_latency(),
        "p95_latency_ms": p95_latency(),
        "avg_confidence": avg_confidence(),
    }

def reset(): 
    _metrics.update({"calls":0,"errors":0,"latency_ms":[],"confidence":[]})
