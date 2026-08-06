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
if ! command -v node >/dev/null 2>&1; then
  echo "ERROR: node is required" >&2
  exit 2
fi

ROOT_DIR="$(python3 -c 'import os; print(os.path.realpath("."))')"
REPO="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$REPO")"

echo "[verify] package root: $ROOT_DIR"
echo "[verify] target repo: $REPO"

bash -n audit.sh
bash -n install.sh
bash -n verify.sh
bash -n uninstall.sh
echo "[verify] shell syntax: PASS"

python3 - "$REPO" <<'PY'
import json, pathlib, sys
root = pathlib.Path('.')
json_files = [root / 'MANIFEST.json', root / 'project/.omp/mcp.json', root / 'templates/PROJECT_STATE.json', root / 'templates/QUALITY_GATES.json', root / 'project/docs/PROJECT_STATE.json']
for path in json_files:
    json.load(path.open(encoding='utf-8'))
print('[verify] package JSON parse: PASS')
repo = pathlib.Path(sys.argv[1])
repo_json = [repo / 'docs/PROJECT_STATE.json', repo / '.project-factory/quality-gates.json', repo / '.omp/mcp.json']
for path in repo_json:
    json.load(path.open(encoding='utf-8'))
print('[verify] repo JSON parse: PASS')
PY

python3 - <<'PY'
import pathlib, yaml
for path in [pathlib.Path('profile/config.yml'), pathlib.Path('project/.omp/config.yml'), pathlib.Path('project/.omp/WATCHDOG.yml')]:
    yaml.safe_load(path.read_text(encoding='utf-8'))
print('[verify] YAML parse: PASS')
PY

python3 - <<'PY'
import pathlib, re
skills = {p.parent.name for p in pathlib.Path('project/.omp/skills').glob('*/SKILL.md')}
if not skills:
    raise SystemExit('no skills found')
for path in pathlib.Path('project/.omp/agents').glob('*.md'):
    text = path.read_text(encoding='utf-8')
    if not text.startswith('---\n'):
        raise SystemExit(f'missing frontmatter in {path}')
    if 'spawns: []' not in text or 'blocking: true' not in text:
        raise SystemExit(f'missing required frontmatter fields in {path}')
    m = re.search(r'autoloadSkills:\s*\[(.*?)\]', text, re.S)
    if not m:
        raise SystemExit(f'missing autoloadSkills in {path}')
    names = [item.strip() for item in m.group(1).split(',') if item.strip()]
    for name in names:
        if name not in skills:
            raise SystemExit(f'broken autoloadSkills reference {name} in {path}')
print('[verify] agent frontmatter and autoloadSkills: PASS')
PY

python3 - <<'PY'
import pathlib
required = [
  'design-project.md', 'create-roadmap.md', 'plan-stage.md', 'run-task.md',
  'close-stage.md', 'prepare-github.md', 'project-status.md'
]
commands = {p.name for p in pathlib.Path('project/.omp/commands').glob('*.md')}
missing = [name for name in required if name not in commands]
if missing:
    raise SystemExit(f'missing commands: {missing}')
required_tools = {'project_state.ts', 'quality_gate.ts', 'task_commit.ts', 'mission_commit.ts', 'git_inspect.ts'}
tools = {p.name for p in pathlib.Path('project/.omp/tools').glob('*.ts')}
missing_tools = sorted(required_tools - tools)
if missing_tools:
    raise SystemExit(f'missing tools: {missing_tools}')
print('[verify] commands and tools present: PASS')
PY

python3 - <<'PY'
import json, pathlib
root = pathlib.Path('.')
manifest = json.load((root / 'MANIFEST.json').open(encoding='utf-8'))
expected = {
    'agents': len(list((root / 'project/.omp/agents').glob('*.md'))),
    'commands': len(list((root / 'project/.omp/commands').glob('*.md'))),
    'skills': len(list((root / 'project/.omp/skills').glob('*/SKILL.md'))),
    'tools': len(list((root / 'project/.omp/tools').glob('*.ts'))),
    'templates': len(list((root / 'templates').glob('*'))),
    'project_docs': len([p for p in (root / 'project/docs').rglob('*') if p.is_file()]),
    'tests': len([p for p in (root / 'tests').rglob('*') if p.is_file()]),
}
release_files = []
for path in sorted(root.rglob('*')):
    if not path.is_file():
        continue
    rel = path.relative_to(root).as_posix()
    if rel.startswith('.git/') or rel.startswith('.work/') or rel == 'omp-project-factory-v2-fixed.zip':
        continue
    release_files.append(rel)
expected['release_files'] = len(release_files)
if manifest.get('counts') != expected:
    raise SystemExit(f'manifest counts mismatch: {manifest.get("counts")} != {expected}')
if manifest.get('files') != release_files:
    raise SystemExit('manifest file list mismatch')
if json.load((root / 'project/.omp/mcp.json').open(encoding='utf-8')) != {'mcpServers': {}}:
    raise SystemExit('project/.omp/mcp.json must remain empty')
print('[verify] manifest counts, file list and mcp.json: PASS')
PY

python3 - <<'PY'
import hashlib, json, pathlib
root = pathlib.Path('.')
manifest = json.load((root / 'MANIFEST.json').open(encoding='utf-8'))
for rel, expected in manifest['checksums'].items():
    actual = 'sha256:' + hashlib.sha256((root / rel).read_bytes()).hexdigest()
    if actual != expected:
        raise SystemExit(f'manifest checksum mismatch: {rel}')
checksum_file = root / 'CHECKSUMS.sha256'
if not checksum_file.is_file():
    raise SystemExit('missing CHECKSUMS.sha256')
entries = {}
for line in checksum_file.read_text(encoding='utf-8').splitlines():
    if not line.strip():
        continue
    digest, rel = line.split('  ', 1)
    entries[rel] = digest
for rel in manifest['files']:
    if rel == 'CHECKSUMS.sha256':
        continue
    actual = hashlib.sha256((root / rel).read_bytes()).hexdigest()
    if entries.get(rel) != actual:
        raise SystemExit(f'CHECKSUMS mismatch: {rel}')
print('[verify] manifest checksums and CHECKSUMS.sha256: PASS')
PY

python3 - <<'PY'
import os, pathlib, stat
for rel in ['audit.sh', 'install.sh', 'verify.sh', 'uninstall.sh']:
    mode = (pathlib.Path(rel).stat().st_mode)
    if not (mode & stat.S_IXUSR):
        raise SystemExit(f'not executable: {rel}')
print('[verify] executable permissions: PASS')
PY

for tool in project/.omp/tools/*.ts; do
  node --experimental-strip-types --input-type=module -e "const { pathToFileURL } = await import('node:url'); const { resolve } = await import('node:path'); await import(pathToFileURL(resolve(process.argv[1])).href); process.stdout.write('[verify] TS import PASS: ' + process.argv[1] + '\n')" "$tool"
done

python3 - <<'PY'
import pathlib, re
targets = [pathlib.Path('audit.sh'), pathlib.Path('install.sh'), pathlib.Path('verify.sh'), pathlib.Path('uninstall.sh')]
patterns = [
    r'\bnpm\s+install\b', r'\bpnpm\s+install\b', r'\byarn\s+install\b', r'\bbun\s+add\b',
    r'\bpip\s+install\b', r'\bcargo\s+add\b', r'\bgo\s+get\b', r'\buv\s+add\b'
]
violations = []
for path in targets:
    text = path.read_text(encoding='utf-8', errors='ignore')
    for pattern in patterns:
        if re.search(pattern, text):
            violations.append(f'{path}:{pattern}')
if violations:
    raise SystemExit('dependency installation command found: ' + '; '.join(violations))
print('[verify] package scripts avoid dependency installation: PASS')
PY

python3 - <<'PY'
import pathlib, re
bad = []
patterns = [r'\bgh\s+issue\s+create\b', r'\bgh\s+pr\s+create\b', r'\bgh\s+pr\s+merge\b']
targets = [pathlib.Path('audit.sh'), pathlib.Path('install.sh'), pathlib.Path('verify.sh'), pathlib.Path('uninstall.sh')]
targets += sorted(pathlib.Path('project/.omp/tools').rglob('*.ts'))
targets += sorted(pathlib.Path('project/.omp/commands').glob('*.md'))
targets += sorted(pathlib.Path('project/.omp/agents').glob('*.md'))
targets += sorted(pathlib.Path('project/.omp/skills').glob('*/SKILL.md'))
for path in targets:
    text = path.read_text(encoding='utf-8', errors='ignore')
    for pattern in patterns:
        if re.search(pattern, text):
            bad.append((str(path), pattern))
if bad:
    raise SystemExit('forbidden mutating GitHub command found: ' + '; '.join(f'{p}:{pat}' for p, pat in bad[:10]))
print('[verify] forbidden mutating GitHub commands: PASS')
PY

node tests/run-tests.mjs
echo "[verify] local test harness: PASS"

if command -v omp >/dev/null 2>&1; then
  echo "[verify] omp version: $(omp --version)"
  omp config list --json >/dev/null
  echo "[verify] omp config list --json: PASS"
  if ! omp --profile factory models; then
    echo "[verify] WARNING: omp models discovery failed"
  fi
else
  echo "[verify] WARNING: omp not installed; runtime checks skipped"
fi

echo "[verify] complete"
