"""
ledge_env — Environment and configuration for Ledge
Secure access to environment variables and config files.
"""
import os, json

LEDGE_PACKAGE = "ledge_env"
VERSION = "1.0.0"

def get(key, default=None):
    return os.environ.get(str(key), default)

def require(key):
    val = os.environ.get(str(key))
    if val is None:
        raise ValueError(f"Required environment variable not set: {key}")
    return val

def set_var(key, value):
    os.environ[str(key)] = str(value)
    return value

def has(key):
    return str(key) in os.environ

def all_vars():
    return dict(os.environ)

def load_json_config(path):
    with open(str(path)) as f:
        return json.load(f)

def openai_key():
    return get("OPENAI_API_KEY")

def anthropic_key():
    return get("ANTHROPIC_API_KEY")
