#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import shutil
import stat
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def run(args: list[str], *, cwd: pathlib.Path = ROOT, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=check)


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def load_json(path: pathlib.Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"invalid JSON {path}: {exc}")


def release_files() -> list[str]:
    result = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith((".git/", ".work/", ".release/")) or rel == "omp-project-factory-v2-fixed.zip":
            continue
        result.append(rel)
    return result


def digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_frontmatter() -> None:
    skills: dict[str, pathlib.Path] = {}
    for path in (ROOT / "project/.omp/skills").glob("*/SKILL.md"):
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---\n"):
            fail(f"skill frontmatter is not at byte zero: {path}")
        end = text.find("\n---\n", 4)
        if end < 0:
            fail(f"unterminated skill frontmatter: {path}")
        metadata = text[4:end]
        name_match = re.search(r"^name:\s*[\"']?([^\"'\n]+)", metadata, re.M)
        desc_match = re.search(r"^description:\s*(.+)$", metadata, re.M)
        if not name_match or not desc_match:
            fail(f"skill name/description missing: {path}")
        name = name_match.group(1).strip()
        if name in skills:
            fail(f"duplicate skill name: {name}")
        skills[name] = path
    if not skills:
        fail("no discoverable skills")

    for path in (ROOT / "project/.omp/agents").glob("*.md"):
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---\n"):
            fail(f"agent frontmatter is not at byte zero: {path}")
        if "spawns: []" not in text or "blocking: true" not in text:
            fail(f"required agent frontmatter missing: {path}")
        match = re.search(r"autoloadSkills:\s*\[(.*?)\]", text, re.S)
        if not match:
            fail(f"autoloadSkills missing: {path}")
        for raw in match.group(1).split(","):
            name = raw.strip().strip('"').strip("'")
            if name and name not in skills:
                fail(f"broken autoloadSkills reference {name} in {path}")
    print(f"[verify] OMP-discoverable frontmatter: PASS ({len(skills)} skills)")


def verify_manifest() -> None:
    manifest = load_json(ROOT / "MANIFEST.json")
    files = release_files()
    expected = {
        "agents": len(list((ROOT / "project/.omp/agents").glob("*.md"))),
        "commands": len(list((ROOT / "project/.omp/commands").glob("*.md"))),
        "skills": len(list((ROOT / "project/.omp/skills").glob("*/SKILL.md"))),
        "tools": len(list((ROOT / "project/.omp/tools").glob("*.ts"))),
        "templates": len([p for p in (ROOT / "templates").glob("*") if p.is_file()]),
        "project_docs": len([p for p in (ROOT / "project/docs").rglob("*") if p.is_file()]),
        "tests": len([p for p in (ROOT / "tests").rglob("*") if p.is_file()]),
        "release_files": len(files),
    }
    if manifest.get("counts") != expected:
        fail(f"manifest counts mismatch: {manifest.get('counts')} != {expected}")
    if manifest.get("files") != files:
        fail("manifest file list mismatch")
    for rel, expected_hash in manifest.get("checksums", {}).items():
        actual = f"sha256:{digest(ROOT / rel)}"
        if actual != expected_hash:
            fail(f"manifest checksum mismatch: {rel}")
    entries = {}
    for line in (ROOT / "CHECKSUMS.sha256").read_text(encoding="utf-8").splitlines():
        if line.strip():
            value, rel = line.split("  ", 1)
            entries[rel] = value
    for rel in files:
        if rel == "CHECKSUMS.sha256":
            continue
        if entries.get(rel) != digest(ROOT / rel):
            fail(f"CHECKSUMS mismatch: {rel}")
    print("[verify] manifest and checksums: PASS")


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: verify-package.py /path/to/repository")
    repo = pathlib.Path(sys.argv[1]).resolve()
    if not repo.is_dir():
        fail(f"repository path does not exist: {repo}")

    for script in ["audit.sh", "install.sh", "verify.sh", "uninstall.sh"]:
        run(["bash", "-n", script])
        if not ((ROOT / script).stat().st_mode & stat.S_IXUSR):
            fail(f"script is not executable: {script}")
    print("[verify] shell syntax and executable permissions: PASS")

    for path in [ROOT / "MANIFEST.json", ROOT / "project/.omp/mcp.json", ROOT / "templates/PROJECT_STATE.json", ROOT / "templates/QUALITY_GATES.json", ROOT / "project/docs/PROJECT_STATE.json", repo / "docs/PROJECT_STATE.json", repo / ".project-factory/quality-gates.json", repo / ".omp/mcp.json", repo / ".project-factory/install-ledger.json"]:
        load_json(path)
    if load_json(ROOT / "project/.omp/mcp.json") != {"mcpServers": {}}:
        fail("project/.omp/mcp.json must remain empty")
    print("[verify] JSON, install ledger and empty MCP config: PASS")

    try:
        import yaml  # type: ignore
    except ImportError:
        print("[verify] WARNING: PyYAML unavailable; OMP runtime will validate YAML")
    else:
        for path in [ROOT / "profile/config.yml", ROOT / "project/.omp/config.yml", ROOT / "project/.omp/WATCHDOG.yml"]:
            yaml.safe_load(path.read_text(encoding="utf-8"))
        print("[verify] YAML parse: PASS")

    verify_frontmatter()
    required_commands = {"design-project.md", "create-roadmap.md", "plan-stage.md", "run-task.md", "close-stage.md", "prepare-github.md", "project-status.md"}
    commands = {p.name for p in (ROOT / "project/.omp/commands").glob("*.md")}
    if required_commands - commands:
        fail(f"missing commands: {sorted(required_commands - commands)}")
    required_tools = {"project_state.ts", "quality_gate.ts", "task_commit.ts", "mission_commit.ts", "git_inspect.ts", "review_report.ts"}
    tools = {p.name for p in (ROOT / "project/.omp/tools").glob("*.ts")}
    if required_tools - tools:
        fail(f"missing tools: {sorted(required_tools - tools)}")
    print("[verify] required commands and tools: PASS")

    verify_manifest()

    install_patterns = [r"\bnpm\s+install\b", r"\bpnpm\s+install\b", r"\byarn\s+install\b", r"\bbun\s+add\b", r"\bpip\s+install\b", r"\bpython3?\s+-m\s+pip\b", r"\bcargo\s+add\b", r"\bgo\s+get\b", r"\buv\s+add\b"]
    scripts = [ROOT / name for name in ["audit.sh", "install.sh", "verify.sh", "uninstall.sh"]]
    for path in scripts:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in install_patterns:
            if re.search(pattern, text):
                fail(f"dependency installation command found: {path}:{pattern}")
    mutation_patterns = [r"\bgh\s+issue\s+create\b", r"\bgh\s+pr\s+create\b", r"\bgh\s+pr\s+merge\b"]
    targets = scripts + sorted((ROOT / "project/.omp").rglob("*.ts")) + sorted((ROOT / "project/.omp/commands").glob("*.md")) + sorted((ROOT / "project/.omp/agents").glob("*.md")) + sorted((ROOT / "project/.omp/skills").glob("*/SKILL.md"))
    for path in targets:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in mutation_patterns:
            if re.search(pattern, text):
                fail(f"forbidden GitHub mutation found: {path}:{pattern}")
    print("[verify] dependency and GitHub mutation policy: PASS")

    node_major = int(run(["node", "-p", "Number(process.versions.node.split('.')[0])"]).stdout.strip())
    if node_major < 22:
        fail("Node 22+ is required")
    for tool in sorted((ROOT / "project/.omp/tools").glob("*.ts")):
        run(["node", "--experimental-strip-types", "--input-type=module", "-e", "const {pathToFileURL}=await import('node:url'); const {resolve}=await import('node:path'); await import(pathToFileURL(resolve(process.argv[1])).href);", str(tool)])
    print("[verify] TypeScript tool imports: PASS")

    result = run(["node", "tests/run-tests.mjs"])
    print(result.stdout.strip())
    print("[verify] local behavioral harness: PASS")

    omp = shutil.which("omp")
    if omp:
        print(f"[verify] omp version: {run([omp, '--version']).stdout.strip()}")
        run([omp, "config", "list", "--json"])
        model_result = run([omp, "--profile", "factory", "models"], check=False)
        if model_result.returncode != 0:
            print("[verify] WARNING: model discovery failed or credentials are absent")
    else:
        print("[verify] WARNING: omp not installed; runtime model checks skipped")
    print("[verify] complete")


if __name__ == "__main__":
    main()
