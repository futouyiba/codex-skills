#!/usr/bin/env bash
set -euo pipefail

skill_home="${CODEX_HOME:-$HOME/.codex}/skills"
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
replace_existing=false

if [ "${1:-}" = "--replace-existing" ]; then
  replace_existing=true
fi

mkdir -p "$skill_home"

for skill in "$repo_dir"/skills/*; do
  [ -d "$skill" ] || continue
  name="$(basename "$skill")"
  target="$skill_home/$name"

  if [ -e "$target" ] && [ ! -L "$target" ]; then
    if [ "$replace_existing" = false ]; then
      echo "skip $name: target exists and is not a symlink: $target"
      echo "       rerun with --replace-existing to back it up and link this repository copy"
      continue
    fi

    backup="$target.bak-$(date +%Y%m%d%H%M%S)"
    mv "$target" "$backup"
    echo "backed up $name -> $backup"
  fi

  ln -sfn "$skill" "$target"
  echo "linked $name -> $target"
done
