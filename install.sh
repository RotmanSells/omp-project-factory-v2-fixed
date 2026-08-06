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

if [ -z "$REPO" ]; then usage; exit 2; fi
if [ ! -d "$REPO" ]; then echo "ERROR: repository path does not exist: $REPO" >&2; exit 2; fi
if ! command -v python3 >/dev/null 2>&1; then echo "ERROR: python3 is required" >&2; exit 2; fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$REPO")"

echo "[install] mode: $( [ "$APPLY" -eq 1 ] && echo APPLY || echo DRY-RUN )"
echo "[install] package root: $SCRIPT_DIR"
echo "[install] repository: $REPO"

python3 - "$SCRIPT_DIR" "$REPO" "$APPLY" <<'PY'
import hashlib
import json
import os
import pathlib
import shutil
import sys
from datetime import datetime, timezone

package_root = pathlib.Path(sys.argv[1]).resolve()
repo = pathlib.Path(sys.argv[2]).resolve()
apply = sys.argv[3] == "1"
project_src = package_root / "project"
profile_src = package_root / "profile" / "config.yml"
profile_dst = pathlib.Path.home() / ".omp" / "profiles" / "factory" / "agent" / "config.yml"
factory_dir = repo / ".project-factory"
ledger_path = factory_dir / "install-ledger.json"
stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
backup_root = factory_dir / "install-backups" / stamp

protected = {
    "PROJECT_BRIEF.md",
    "docs/PROJECT_STATE.json",
    ".project-factory/quality-gates.json",
}

def digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def same(a: pathlib.Path, b: pathlib.Path) -> bool:
    return a.is_file() and b.is_file() and digest(a) == digest(b)

def rel_files(root: pathlib.Path):
    for path in sorted(root.rglob("*")):
        if path.is_file():
            yield path.relative_to(root).as_posix(), path

previous = None
if ledger_path.is_file():
    previous = json.loads(ledger_path.read_text(encoding="utf-8"))
previous_entries = {entry["path"]: entry for entry in (previous or {}).get("entries", [])}

plan = []
conflicts = []
preserved = []
for rel, src in rel_files(project_src):
    dst = repo / rel
    if rel in protected and dst.exists():
        preserved.append(rel)
        continue
    prior = previous_entries.get(rel)
    if dst.exists() and prior and dst.is_file() and digest(dst) != prior.get("installed_sha256"):
        conflicts.append(rel)
        continue
    if dst.exists() and same(src, dst):
        plan.append((rel, src, dst, "unchanged"))
    elif dst.exists():
        plan.append((rel, src, dst, "replace"))
    else:
        plan.append((rel, src, dst, "create"))

quality_src = package_root / "templates" / "QUALITY_GATES.json"
quality_rel = ".project-factory/quality-gates.json"
quality_dst = repo / quality_rel
if not quality_dst.exists():
    plan.append((quality_rel, quality_src, quality_dst, "create"))

print(f"[install] planned files: {len(plan)}")
for rel in preserved:
    print(f"[install] preserve project-owned file: {rel}")
for rel in conflicts:
    print(f"[install] CONFLICT modified since previous install; left untouched: {rel}")
if conflicts:
    print("[install] conflicts require manual owner review")

if not apply:
    print("[install] dry-run only. No files were changed. Re-run with --apply to install.")
    raise SystemExit(0)

factory_dir.mkdir(parents=True, exist_ok=True)
entries = []
for rel, src, dst, action in plan:
    if action == "unchanged":
        entries.append({"path": rel, "action": "created" if not previous_entries.get(rel) else previous_entries[rel].get("action", "created"), "backup": previous_entries.get(rel, {}).get("backup"), "installed_sha256": digest(src)})
        continue
    dst.parent.mkdir(parents=True, exist_ok=True)
    backup_rel = None
    original_action = "created"
    if dst.exists():
        original_action = "replaced"
        backup = backup_root / "repo" / rel
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(dst, backup)
        backup_rel = backup.relative_to(repo).as_posix()
    shutil.copy2(src, dst)
    entries.append({"path": rel, "action": original_action, "backup": backup_rel, "installed_sha256": digest(dst)})

profile_entry = {"path": str(profile_dst), "action": "created", "backup": None, "installed_sha256": None}
profile_dst.parent.mkdir(parents=True, exist_ok=True)
if profile_dst.exists():
    prior_profile = (previous or {}).get("profile")
    if prior_profile and digest(profile_dst) != prior_profile.get("installed_sha256"):
        raise SystemExit("ERROR: factory profile was modified after installation; refusing to overwrite")
    backup = backup_root / "profile" / "config.yml"
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(profile_dst, backup)
    profile_entry.update({"action": "replaced", "backup": backup.relative_to(repo).as_posix()})
shutil.copy2(profile_src, profile_dst)
profile_entry["installed_sha256"] = digest(profile_dst)

ledger = {
    "schema_version": 1,
    "installed_at": datetime.now(timezone.utc).isoformat(),
    "package_root": str(package_root),
    "entries": entries,
    "profile": profile_entry,
    "preserved": sorted(set(preserved)),
    "conflicts": sorted(set(conflicts)),
}
ledger_path.write_text(json.dumps(ledger, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"[install] ledger: {ledger_path}")
print("[install] no dependencies, MCP servers or plugins were installed")
if conflicts:
    raise SystemExit("ERROR: installation completed with conflicts; inspect ledger before use")
PY

echo "[install] next: ./verify.sh \"$REPO\""
