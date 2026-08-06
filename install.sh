#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'EOF'
Usage:
  ./install.sh /path/to/repository        # dry-run
  ./install.sh --apply /path/to/repository
EOF
}

APPLY=0
REPO=""
if [ "${1:-}" = "--apply" ]; then
  APPLY=1
  REPO="${2:-}"
else
  REPO="${1:-}"
fi

if [ -z "$REPO" ]; then
  usage
  exit 2
fi
if [ ! -d "$REPO" ]; then
  echo "ERROR: repository path does not exist: $REPO" >&2
  exit 2
fi
if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 is required" >&2
  exit 2
fi

ROOT_DIR="$(python3 -c 'import os; print(os.path.realpath("."))')"
REPO="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$REPO")"
STAMP="$(date +%Y%m%d-%H%M%S)"
PROFILE_DIR="$HOME/.omp/profiles/factory/agent"
PROJECT_SRC="$ROOT_DIR/project"
TEMPLATES_SRC="$ROOT_DIR/templates"

echo "[install] mode: $( [ "$APPLY" -eq 1 ] && echo APPLY || echo DRY-RUN )"
echo "[install] package root: $ROOT_DIR"
echo "[install] repository: $REPO"

for rel in \
  ".omp" \
  ".project-factory" \
  "docs" \
  "PROJECT_BRIEF.md" \
  "AGENTS.md"
do
  if [ -e "$REPO/$rel" ]; then
    echo "[install] existing path: $rel"
  fi
done

if [ "$APPLY" -ne 1 ]; then
  echo "[install] dry-run only. No files were changed. Re-run with --apply to install."
  exit 0
fi

mkdir -p "$PROFILE_DIR"
if [ -f "$PROFILE_DIR/config.yml" ]; then
  cp -p "$PROFILE_DIR/config.yml" "$PROFILE_DIR/config.yml.backup.$STAMP"
  echo "[install] backup: $PROFILE_DIR/config.yml.backup.$STAMP"
fi
cp -p "$ROOT_DIR/profile/config.yml" "$PROFILE_DIR/config.yml"

for rel in ".omp" ".project-factory" "docs" "PROJECT_BRIEF.md" "AGENTS.md"; do
  if [ -e "$REPO/$rel" ]; then
    cp -pR "$REPO/$rel" "$REPO/$rel.backup.$STAMP"
    echo "[install] backup: $REPO/$rel.backup.$STAMP"
  fi
done

mkdir -p "$REPO"
cp -pR "$PROJECT_SRC/." "$REPO/"
mkdir -p "$REPO/.project-factory"
cp -p "$TEMPLATES_SRC/QUALITY_GATES.json" "$REPO/.project-factory/quality-gates.json"
cp -p "$TEMPLATES_SRC/PROJECT_BRIEF.md" "$REPO/PROJECT_BRIEF.md"
cp -p "$TEMPLATES_SRC/PROJECT_STATE.json" "$REPO/docs/PROJECT_STATE.json"

echo "[install] installed factory profile and project payload"
echo "[install] no dependencies, MCP servers or plugins were installed"
echo "[install] next: ./verify.sh \"$REPO\""
