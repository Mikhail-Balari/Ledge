"""Bundled Ledge demos. Listed and run by `ledge demo <name>`.

Each demo is a .ledge file in this directory that runs without an API key
and exercises a specific language feature (uncertainty handling, audit
trail, type narrowing). Demos are intentionally small enough to read in
under a minute and pass the strict static checker.
"""

import os

DEMOS_DIR = os.path.dirname(os.path.abspath(__file__))


def list_demos():
    """Return sorted list of bundled demo names (filename stems)."""
    names = []
    for entry in os.listdir(DEMOS_DIR):
        if entry.endswith(".ledge"):
            names.append(entry[:-len(".ledge")])
    return sorted(names)


def demo_path(name: str) -> str:
    """Return the absolute path to the bundled demo file, or '' if not found."""
    candidate = os.path.join(DEMOS_DIR, name + ".ledge")
    return candidate if os.path.isfile(candidate) else ""
