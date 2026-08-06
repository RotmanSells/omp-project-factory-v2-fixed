#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: ./verify.sh /path/to/repository" >&2
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
if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 is required" >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/scripts/verify-package.py" "$REPO"
