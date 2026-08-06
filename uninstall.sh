#!/usr/bin/env bash
set -euo pipefail

usage() { echo "Usage: ./uninstall.sh --apply /path/to/repository" >&2; }
if [ "${1:-}" != "--apply" ] || [ -z "${2:-}" ]; then usage; exit 2; fi
if ! command -v python3 >/dev/null 2>&1; then echo "ERROR: python3 is required" >&2; exit 2; fi

REPO="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$2")"
if [ ! -d "$REPO" ]; then echo "ERROR: repository path does not exist: $REPO" >&2; exit 2; fi

echo "[uninstall] repository: $REPO"

python3 - "$REPO" <<'PY'
import hashlib
import json
import pathlib
import shutil
import sys
from datetime import datetime, timezone

repo = pathlib.Path(sys.argv[1]).resolve()
ledger_path = repo / ".project-factory" / "install-ledger.json"
if not ledger_path.is_file():
    raise SystemExit("ERROR: install ledger is missing; refusing broad uninstall")
ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
if ledger.get("schema_version") != 1:
    raise SystemExit("ERROR: unsupported install ledger")

def digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
quarantine = repo / ".project-factory" / "uninstall-quarantine" / stamp
conflicts = []
restored = []
quarantined = []

for entry in sorted(ledger.get("entries", []), key=lambda item: item["path"], reverse=True):
    rel = entry["path"]
    current = repo / rel
    if not current.exists():
        continue
    if not current.is_file() or digest(current) != entry.get("installed_sha256"):
        conflicts.append(rel)
        continue
    if entry.get("action") == "replaced" and entry.get("backup"):
        backup = repo / entry["backup"]
        if not backup.is_file():
            conflicts.append(rel + " (missing backup)")
            continue
        shutil.copy2(backup, current)
        restored.append(rel)
    else:
        target = quarantine / "repo" / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(current), str(target))
        quarantined.append(rel)

profile = ledger.get("profile") or {}
profile_path = pathlib.Path(profile.get("path", "")) if profile.get("path") else None
if profile_path and profile_path.exists():
    if not profile_path.is_file() or digest(profile_path) != profile.get("installed_sha256"):
        conflicts.append(str(profile_path) + " (modified profile)")
    elif profile.get("action") == "replaced" and profile.get("backup"):
        backup = repo / profile["backup"]
        if backup.is_file():
            shutil.copy2(backup, profile_path)
            restored.append(str(profile_path))
        else:
            conflicts.append(str(profile_path) + " (missing profile backup)")
    else:
        target = quarantine / "profile" / "config.yml"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(profile_path), str(target))
        quarantined.append(str(profile_path))

ledger["uninstalled_at"] = datetime.now(timezone.utc).isoformat()
ledger["uninstall_conflicts"] = conflicts
ledger["quarantine"] = str(quarantine.relative_to(repo))
result_path = ledger_path.with_name(f"install-ledger.uninstalled.{stamp}.json")
result_path.write_text(json.dumps(ledger, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
ledger_path.write_text(json.dumps({"schema_version": 1, "status": "uninstalled", "result_ledger": result_path.name}, indent=2) + "\n", encoding="utf-8")

for item in restored:
    print(f"[uninstall] restored: {item}")
for item in quarantined:
    print(f"[uninstall] quarantined unchanged installed file: {item}")
for item in conflicts:
    print(f"[uninstall] PRESERVED modified/conflicted file: {item}")
print(f"[uninstall] reversible quarantine: {quarantine}")
print("[uninstall] project-owned docs, code and post-install modifications were preserved")
if conflicts:
    raise SystemExit("ERROR: uninstall finished with preserved conflicts; review result ledger")
PY
