"""
ledge_audit — Extended audit utilities for Ledge
Compliance-grade audit trail management.
"""
import json, time, hashlib

LEDGE_PACKAGE = "ledge_audit"
VERSION = "1.0.0"

_AUDIT_LOG = []

def log(event_type, data=None, user=None, session=None):
    entry = {
        "timestamp": time.time(),
        "event": event_type,
        "user": user,
        "session": session,
        "data_hash": hashlib.sha256(json.dumps(data, default=str).encode()).hexdigest()[:12] if data else None,
    }
    _AUDIT_LOG.append(entry)
    return entry

def export():
    return list(_AUDIT_LOG)

def export_json():
    return json.dumps(_AUDIT_LOG, indent=2)

def filter_by(event_type=None, user=None, since=None):
    results = _AUDIT_LOG
    if event_type: results = [e for e in results if e["event"] == event_type]
    if user: results = [e for e in results if e["user"] == user]
    if since: results = [e for e in results if e["timestamp"] >= float(since)]
    return results

def count(): return len(_AUDIT_LOG)
def clear(): _AUDIT_LOG.clear()
