#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: ./audit.sh /path/to/repository" >&2
}

REPO="${1:-}"
if [ -z "$REPO" ]; then
  usage
  exit 2
fi
if [ ! -d "$REPO" ]; then
  echo "ERROR: repository path does not exist: $REPO" >&2
  exit 2
fi
if ! command -v git >/dev/null 2>&1; then
  echo "ERROR: git is required" >&2
  exit 2
fi
if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 is required" >&2
  exit 2
fi
if ! command -v omp >/dev/null 2>&1; then
  echo "ERROR: omp is not installed" >&2
  exit 2
fi

REPO="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$REPO")"

echo "[audit] repository: $REPO"
echo "[audit] omp version: $(omp --version)"

git -C "$REPO" rev-parse --is-inside-work-tree >/dev/null
echo "[audit] git repo: PASS"
echo "[audit] branch: $(git -C "$REPO" branch --show-current || true)"

STATUS="$(git -C "$REPO" status --porcelain=v1 --untracked-files=all)"
if [ -n "$STATUS" ]; then
  echo "[audit] worktree: DIRTY"
  printf '%s\n' "$STATUS"
else
  echo "[audit] worktree: CLEAN"
fi

if [ -e "$REPO/.omp" ]; then
  echo "[audit] existing project .omp: yes"
else
  echo "[audit] existing project .omp: no"
fi

if [ -f "$HOME/.omp/profiles/factory/agent/config.yml" ]; then
  echo "[audit] existing factory profile: yes"
else
  echo "[audit] existing factory profile: no"
fi

for runtime in node python3 git unzip zip; do
  if command -v "$runtime" >/dev/null 2>&1; then
    echo "[audit] runtime $runtime: OK"
  else
    echo "[audit] runtime $runtime: MISSING"
  fi
done

if [ -f "$REPO/RULES.md" ]; then
  echo "[audit] WARNING: repository has top-level RULES.md; compare with project/.omp/RULES.md manually"
fi

echo "[audit] config keys snapshot:"
python3 - <<'PY'
import json, subprocess
data = json.loads(subprocess.check_output(['omp', 'config', 'list', '--json'], text=True))
keys = [
    'modelRoles', 'tools.approvalMode', 'async.enabled', 'task.batch',
    'task.maxConcurrency', 'task.maxRecursionDepth', 'task.isolation.mode',
    'skills.enabled', 'advisor.enabled', 'mcp.enableProjectConfig'
]
for key in keys:
    print(f"- {key}: {'present' if key in data else 'missing'}")
PY

echo "[audit] read-only audit complete"
