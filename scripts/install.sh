#!/usr/bin/env bash
set -euo pipefail

skill_home="${CODEX_HOME:-$HOME/.codex}/skills"
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

mkdir -p "$skill_home"

for skill in "$repo_dir"/skills/*; do
  [ -d "$skill" ] || continue
  name="$(basename "$skill")"
  target="$skill_home/$name"

  if [ -e "$target" ] && [ ! -L "$target" ]; then
    echo "skip $name: target exists and is not a symlink: $target"
    continue
  fi

  ln -sfn "$skill" "$target"
  echo "linked $name -> $target"
done
