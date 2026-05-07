"""
ledge_crypto — Cryptographic utilities for Ledge
Hashing, signing, and secure comparison.
"""
import hashlib, hmac, secrets, base64

LEDGE_PACKAGE = "ledge_crypto"
VERSION = "1.0.0"

def sha256(text): 
    return hashlib.sha256(str(text).encode()).hexdigest()

def sha512(text):
    return hashlib.sha512(str(text).encode()).hexdigest()

def md5(text):
    return hashlib.md5(str(text).encode()).hexdigest()

def random_token(length=32):
    return secrets.token_hex(int(length))

def random_bytes(n=16):
    return base64.b64encode(secrets.token_bytes(int(n))).decode()

def constant_time_eq(a, b):
    return hmac.compare_digest(str(a), str(b))

def b64encode(text):
    return base64.b64encode(str(text).encode()).decode()

def b64decode(text):
    return base64.b64decode(str(text)).decode()

def hmac_sign(key, message):
    return hmac.new(str(key).encode(), str(message).encode(), hashlib.sha256).hexdigest()
