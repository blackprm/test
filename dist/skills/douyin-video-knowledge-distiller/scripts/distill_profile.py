#!/usr/bin/env python3
"""Run the Douyin video knowledge distiller bundled with this skill."""

from pathlib import Path
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from video_knowledge.cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
