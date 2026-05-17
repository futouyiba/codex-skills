#!/usr/bin/env python3
"""Skill entrypoint for Feishu Knowledge Export.

Prefer the shared app project implementation so the Codex skill and macOS app
use one maintained exporter. Fall back to the skill-local core copy if the
shared project is unavailable.
"""

from __future__ import annotations

import runpy
import sys
import os
from pathlib import Path


SHARED_SCRIPT = Path(os.environ.get("FEISHU_KNOWLEDGE_EXPORTER_SCRIPT", ""))
LOCAL_CORE = Path(__file__).with_name("feishu_knowledge_export_core.py")


def ensure_skill_defaults(argv: list[str]) -> list[str]:
    """Default skill runs should try multimodal alt text.

    The shared exporter safely falls back when OPENAI_API_KEY is absent or when
    images are unavailable, so adding this flag by default is low risk.
    """
    if len(argv) < 2 or argv[1] not in {"export", "package"}:
        return argv
    if "--multimodal-alt" not in argv:
        argv.append("--multimodal-alt")
    if "--vision-detail" not in argv:
        argv.extend(["--vision-detail", "high"])
    return argv


def main() -> int:
    target = SHARED_SCRIPT if str(SHARED_SCRIPT) and SHARED_SCRIPT.exists() else LOCAL_CORE
    if not target.exists():
        print(
            "No Feishu Knowledge Export implementation found. Expected one of:\n"
            "- $FEISHU_KNOWLEDGE_EXPORTER_SCRIPT\n"
            f"- {LOCAL_CORE}",
            file=sys.stderr,
        )
        return 127

    sys.argv = ensure_skill_defaults(sys.argv)
    sys.argv[0] = str(target)
    runpy.run_path(str(target), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
