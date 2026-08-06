#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: ./uninstall.sh --apply /path/to/repository" >&2
}

if [ "${1:-}" != "--apply" ] || [ -z "${2:-}" ]; then
  usage
  exit 2
fi

REPO="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$2")"
PROFILE_DIR="$HOME/.omp/profiles/factory/agent"

echo "[uninstall] repository: $REPO"

for rel in ".omp" ".project-factory" "AGENTS.md"; do
  if [ -e "$REPO/$rel" ]; then
    rm -rf "$REPO/$rel"
    echo "[uninstall] removed $REPO/$rel"
  fi
done

LATEST_BACKUP="$(python3 - "$PROFILE_DIR" <<'PY'
import pathlib, sys
profile = pathlib.Path(sys.argv[1])
items = sorted(profile.glob('config.yml.backup.*'))
print(items[-1] if items else '')
PY
)"
if [ -n "$LATEST_BACKUP" ]; then
  cp -p "$LATEST_BACKUP" "$PROFILE_DIR/config.yml"
  echo "[uninstall] restored $PROFILE_DIR/config.yml from $LATEST_BACKUP"
elif [ -f "$PROFILE_DIR/config.yml" ]; then
  rm -f "$PROFILE_DIR/config.yml"
  echo "[uninstall] removed $PROFILE_DIR/config.yml"
fi

echo "[uninstall] project docs and application code were preserved"
echo "[uninstall] inspect *.backup.* files manually if you want to restore prior state"
