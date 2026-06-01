#!/usr/bin/env python3
"""Source-checkout wrapper for the installed Ledge CI checker."""

from __future__ import annotations

from ledge_lang.ci_check import main


if __name__ == "__main__":
    raise SystemExit(main())
