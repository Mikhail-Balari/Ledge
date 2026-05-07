"""
ledge_io — File I/O utilities for Ledge
"""
import os, json, csv, io

LEDGE_PACKAGE = "ledge_io"
VERSION = "1.0.0"

def read_text(path):
    with open(str(path), encoding="utf-8") as f: return f.read()

def write_text(path, content):
    with open(str(path), "w", encoding="utf-8") as f: f.write(str(content))
    return True

def read_json(path):
    with open(str(path)) as f: return json.load(f)

def write_json(path, data):
    with open(str(path), "w") as f: json.dump(data, f, indent=2, default=str)
    return True

def read_lines(path):
    with open(str(path), encoding="utf-8") as f: return f.read().splitlines()

def append_text(path, content):
    with open(str(path), "a", encoding="utf-8") as f: f.write(str(content) + "\n")
    return True

def file_exists(path): return os.path.exists(str(path))
def file_size(path): return os.path.getsize(str(path))
def list_dir(path): return os.listdir(str(path))
def make_dir(path): os.makedirs(str(path), exist_ok=True); return True
def delete_file(path): os.remove(str(path)); return True
