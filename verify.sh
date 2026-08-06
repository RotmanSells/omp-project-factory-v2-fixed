#!/usr/bin/env bash
set -euo pipefail

usage() { echo "Usage: ./verify.sh /path/to/repository" >&2; }
REPO="${1:-}"
if [ -z "$REPO" ]; then usage; exit 2; fi
if [ ! -d "$REPO" ]; then echo "ERROR: repository path does not exist: $REPO" >&2; exit 2; fi
for runtime in python3 node git; do
  if ! command -v "$runtime" >/dev/null 2>&1; then echo "ERROR: $runtime is required" >&2; exit 2; fi
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
REPO="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$REPO")"

echo "[verify] package root: $SCRIPT_DIR"
echo "[verify] target repo: $REPO"

bash -n audit.sh install.sh verify.sh uninstall.sh
echo "[verify] shell syntax: PASS"

python3 - "$REPO" <<'PY'
import json, pathlib, sys
root = pathlib.Path('.')
for path in [root/'MANIFEST.json', root/'project/.omp/mcp.json', root/'templates/PROJECT_STATE.json', root/'templates/QUALITY_GATES.json', root/'project/docs/PROJECT_STATE.json']:
    json.load(path.open(encoding='utf-8'))
repo = pathlib.Path(sys.argv[1])
for path in [repo/'docs/PROJECT_STATE.json', repo/'.project-factory/quality-gates.json', repo/'.omp/mcp.json', repo/'.project-factory/install-ledger.json']:
    json.load(path.open(encoding='utf-8'))
print('[verify] JSON and install ledger parse: PASS')
PY

if python3 -c 'import yaml' >/dev/null 2>&1; then
  python3 - <<'PY'
import pathlib, yaml
for path in [pathlib.Path('profile/config.yml'), pathlib.Path('project/.omp/config.yml'), pathlib.Path('project/.omp/WATCHDOG.yml')]:
    yaml.safe_load(path.read_text(encoding='utf-8'))
print('[verify] package YAML parse: PASS')
PY
else
  echo "[verify] WARNING: PyYAML unavailable; package YAML parser check deferred to OMP runtime"
fi

python3 - <<'PY'
import pathlib, re
skill_root = pathlib.Path('project/.omp/skills')
skills = {}
for path in skill_root.glob('*/SKILL.md'):
    text = path.read_text(encoding='utf-8')
    if not text.startswith('---\n'):
        raise SystemExit(f'skill frontmatter is not at byte zero: {path}')
    end = text.find('\n---\n', 4)
    if end < 0:
        raise SystemExit(f'unterminated skill frontmatter: {path}')
    metadata = text[4:end]
    name = re.search(r'^name:\s*["\']?([^"\'\n]+)', metadata, re.M)
    description = re.search(r'^description:\s*(.+)$', metadata, re.M)
    if not name or not description:
        raise SystemExit(f'skill name/description missing: {path}')
    normalized = name.group(1).strip()
    if normalized in skills:
        raise SystemExit(f'duplicate skill name: {normalized}')
    skills[normalized] = path
if not skills:
    raise SystemExit('no discoverable skills found')

for path in pathlib.Path('project/.omp/agents').glob('*.md'):
    text = path.read_text(encoding='utf-8')
    if not text.startswith('---\n'):
        raise SystemExit(f'missing agent frontmatter at byte zero: {path}')
    if 'spawns: []' not in text or 'blocking: true' not in text:
        raise SystemExit(f'missing required agent frontmatter fields: {path}')
    m = re.search(r'autoloadSkills:\s*\[(.*?)\]', text, re.S)
    if not m:
        raise SystemExit(f'missing autoloadSkills: {path}')
    for name in [item.strip().strip('"\'') for item in m.group(1).split(',') if item.strip()]:
        if name not in skills:
            raise SystemExit(f'broken autoloadSkills reference {name} in {path}')
print(f'[verify] OMP-discoverable skill and agent frontmatter: PASS ({len(skills)} skills)')
PY

python3 - <<'PY'
import pathlib
required_commands = {'design-project.md','create-roadmap.md','plan-stage.md','run-task.md','close-stage.md','prepare-github.md','project-status.md'}
commands = {p.name for p in pathlib.Path('project/.omp/commands').glob('*.md')}
if required_commands - commands:
    raise SystemExit(f'missing commands: {sorted(required_commands-commands)}')
required_tools = {'project_state.ts','quality_gate.ts','task_commit.ts','mission_commit.ts','git_inspect.ts','review_report.ts'}
tools = {p.name for p in pathlib.Path('project/.omp/tools').glob('*.ts')}
if required_tools - tools:
    raise SystemExit(f'missing tools: {sorted(required_tools-tools)}')
print('[verify] required commands and tools: PASS')
PY

python3 - <<'PY'
import hashlib, json, pathlib
root = pathlib.Path('.')
manifest = json.load((root/'MANIFEST.json').open(encoding='utf-8'))
release_files=[]
for path in sorted(root.rglob('*')):
    if not path.is_file(): continue
    rel=path.relative_to(root).as_posix()
    if rel.startswith('.git/') or rel.startswith('.work/') or rel=='omp-project-factory-v2-fixed.zip': continue
    release_files.append(rel)
expected={
 'agents':len(list((root/'project/.omp/agents').glob('*.md'))),
 'commands':len(list((root/'project/.omp/commands').glob('*.md'))),
 'skills':len(list((root/'project/.omp/skills').glob('*/SKILL.md'))),
 'tools':len(list((root/'project/.omp/tools').glob('*.ts'))),
 'templates':len([p for p in (root/'templates').glob('*') if p.is_file()]),
 'project_docs':len([p for p in (root/'project/docs').rglob('*') if p.is_file()]),
 'tests':len([p for p in (root/'tests').rglob('*') if p.is_file()]),
 'release_files':len(release_files),
}
if manifest.get('counts')!=expected: raise SystemExit(f'manifest counts mismatch: {manifest.get("counts")} != {expected}')
if manifest.get('files')!=release_files: raise SystemExit('manifest file list mismatch')
for rel, expected_hash in manifest['checksums'].items():
    actual='sha256:'+hashlib.sha256((root/rel).read_bytes()).hexdigest()
    if actual!=expected_hash: raise SystemExit(f'manifest checksum mismatch: {rel}')
entries={}
for line in (root/'CHECKSUMS.sha256').read_text(encoding='utf-8').splitlines():
    if line.strip():
        digest, rel=line.split('  ',1); entries[rel]=digest
for rel in manifest['files']:
    if rel=='CHECKSUMS.sha256': continue
    actual=hashlib.sha256((root/rel).read_bytes()).hexdigest()
    if entries.get(rel)!=actual: raise SystemExit(f'CHECKSUMS mismatch: {rel}')
if json.load((root/'project/.omp/mcp.json').open(encoding='utf-8'))!={'mcpServers':{}}: raise SystemExit('mcp.json must remain empty')
print('[verify] manifest, checksums and empty MCP config: PASS')
PY

python3 - <<'PY'
import pathlib, stat
for rel in ['audit.sh','install.sh','verify.sh','uninstall.sh']:
    if not (pathlib.Path(rel).stat().st_mode & stat.S_IXUSR): raise SystemExit(f'not executable: {rel}')
print('[verify] executable permissions: PASS')
PY

NODE_MAJOR="$(node -p 'Number(process.versions.node.split(".")[0])')"
if [ "$NODE_MAJOR" -lt 22 ]; then echo "ERROR: Node 22+ is required for TypeScript strip-types validation" >&2; exit 2; fi
for tool in project/.omp/tools/*.ts; do
  node --experimental-strip-types --input-type=module -e "const { pathToFileURL } = await import('node:url'); const { resolve } = await import('node:path'); await import(pathToFileURL(resolve(process.argv[1])).href);" "$tool"
done
echo "[verify] TypeScript tool imports: PASS"

python3 - <<'PY'
import pathlib, re
scripts=[pathlib.Path(x) for x in ['audit.sh','install.sh','verify.sh','uninstall.sh']]
install_patterns=[r'\bnpm\s+install\b',r'\bpnpm\s+install\b',r'\byarn\s+install\b',r'\bbun\s+add\b',r'\bpip\s+install\b',r'\bpython3?\s+-m\s+pip\b',r'\bcargo\s+add\b',r'\bgo\s+get\b',r'\buv\s+add\b']
for path in scripts:
    text=path.read_text(encoding='utf-8',errors='ignore')
    for pattern in install_patterns:
        if re.search(pattern,text): raise SystemExit(f'dependency installation command found: {path}:{pattern}')
targets=scripts+sorted(pathlib.Path('project/.omp').rglob('*.ts'))+sorted(pathlib.Path('project/.omp/commands').glob('*.md'))+sorted(pathlib.Path('project/.omp/agents').glob('*.md'))+sorted(pathlib.Path('project/.omp/skills').glob('*/SKILL.md'))
for path in targets:
    text=path.read_text(encoding='utf-8',errors='ignore')
    for pattern in [r'\bgh\s+issue\s+create\b',r'\bgh\s+pr\s+create\b',r'\bgh\s+pr\s+merge\b']:
        if re.search(pattern,text): raise SystemExit(f'forbidden GitHub mutation found: {path}:{pattern}')
print('[verify] dependency and GitHub mutation policy: PASS')
PY

node tests/run-tests.mjs
echo "[verify] local behavioral harness: PASS"

if command -v omp >/dev/null 2>&1; then
  echo "[verify] omp version: $(omp --version)"
  omp config list --json >/dev/null
  echo "[verify] omp config parsing: PASS"
  if ! omp --profile factory models; then echo "[verify] WARNING: model discovery failed or credentials are absent"; fi
else
  echo "[verify] WARNING: omp not installed; runtime model checks skipped"
fi

echo "[verify] complete"
