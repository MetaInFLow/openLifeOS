#!/usr/bin/env python3
"""Agent-facing progress gate for openLifeOS initialization."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCTOR_SCRIPT = ROOT / "scripts" / "doctor_avatar_repo.py"


def main() -> int:
    args = sys.argv[1:]
    if not args or args[0] in {"-h", "--help"}:
        print("Usage: python scripts/openlifeos_progress.py <target-lifeos-repo> [--strict] [--json]")
        print()
        print("Agent-facing wrapper around doctor_avatar_repo.py.")
        print("Use this as the progress gate after each openLifeOS initialization phase.")
        return 0 if args else 2

    return subprocess.call([sys.executable, str(DOCTOR_SCRIPT), *args])


if __name__ == "__main__":
    raise SystemExit(main())
