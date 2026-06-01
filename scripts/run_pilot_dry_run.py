"""Source-checkout wrapper for the packaged pilot dry-run module."""

from __future__ import annotations

from ledge_lang.pilot_dry_run import main


if __name__ == "__main__":
    raise SystemExit(main())
