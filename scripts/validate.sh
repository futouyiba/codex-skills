#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
validator="${CODEX_SKILL_VALIDATOR:-$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py}"

for skill in "$repo_dir"/skills/*; do
  [ -d "$skill" ] || continue
  python3 "$validator" "$skill"
done
