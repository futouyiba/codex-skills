#!/usr/bin/env python3
"""Template for a small source-driven D2 diagram generator.

Copy this into a project and adapt load(), node definitions, and edge list.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "diagram-source"
GENERATED = ROOT / "generated"


def q(text: str) -> str:
    return json.dumps(text, ensure_ascii=False)


def edge(source: str, target: str, label: str, dashed: bool = False) -> str:
    attrs = ['style.stroke: "#3154c9"', "style.stroke-width: 2"]
    if dashed:
        attrs.append("style.stroke-dash: 5")
    return f"{source} -> {target}: {q(label)} {{ {'; '.join(attrs)} }}"


def render(source: Path, stem: str) -> None:
    d2 = shutil.which("d2") or str(ROOT / ".bin" / "d2")
    if not Path(d2).exists() and shutil.which("d2") is None:
        print("warning: d2 CLI not found; wrote source only")
        return
    svg = GENERATED / f"{stem}.svg"
    png = GENERATED / f"{stem}.png"
    subprocess.run([d2, str(source), str(svg)], check=True)
    if shutil.which("sips"):
        subprocess.run(["sips", "-s", "format", "png", str(svg), "--out", str(png)], check=True)


def main() -> int:
    GENERATED.mkdir(exist_ok=True)
    lines = [
        "direction: down",
        "",
        'A: "Top Layer" { direction: right; A1: "Item 1"; A2: "Item 2" }',
        'B: "Anchor Metrics" { direction: right; B1: "Primary"; B2: "Secondary" }',
        'C: "Main Module"',
        'F: "Outcome Layer"',
        "",
        edge("A", "B", "drives"),
        edge("B.B1", "C", "specific causal link"),
        edge("C", "F", "forms outcome"),
    ]
    out = GENERATED / "overview.d2"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    render(out, "overview-d2")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
