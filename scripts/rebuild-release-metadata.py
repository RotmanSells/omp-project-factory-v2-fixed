#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "MANIFEST.json"
CHECKSUMS = ROOT / "CHECKSUMS.sha256"
EXCLUDED_PREFIXES = (".git/", ".work/", ".release/")
EXCLUDED_NAMES = {"omp-project-factory-v2-fixed.zip"}


def release_files() -> list[str]:
    result: list[str] = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel in EXCLUDED_NAMES or rel.startswith(EXCLUDED_PREFIXES):
            continue
        result.append(rel)
    return result


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def paths(pattern: str) -> list[str]:
    return sorted(path.relative_to(ROOT).as_posix() for path in ROOT.glob(pattern) if path.is_file())


def build_manifest(files: list[str]) -> dict:
    agents = paths("project/.omp/agents/*.md")
    commands = paths("project/.omp/commands/*.md")
    skills = paths("project/.omp/skills/*/SKILL.md")
    tools = paths("project/.omp/tools/*.ts")
    templates = paths("templates/*")
    docs = sorted(path.relative_to(ROOT).as_posix() for path in (ROOT / "project/docs").rglob("*") if path.is_file())
    tests = sorted(path.relative_to(ROOT).as_posix() for path in (ROOT / "tests").rglob("*") if path.is_file())
    checksum_scope = [rel for rel in files if rel not in {"MANIFEST.json", "CHECKSUMS.sha256"}]
    return {
        "schema_version": 2,
        "name": "omp-project-factory-v2-fixed",
        "package_version": "2.1.0",
        "generated_by": "scripts/rebuild-release-metadata.py",
        "zip_name": "omp-project-factory-v2-fixed.zip",
        "zip_sha256": None,
        "validation": {
            "status": "generated",
            "verified_by": "verify.sh + tests/run-tests.mjs + GitHub Actions",
            "zip_reextracted": False,
            "zip_sha256_note": "Archive SHA-256 is reported externally after final ZIP creation to avoid a self-referential archive hash.",
        },
        "counts": {
            "agents": len(agents),
            "commands": len(commands),
            "skills": len(skills),
            "tools": len(tools),
            "templates": len(templates),
            "project_docs": len(docs),
            "tests": len(tests),
            "release_files": len(files),
        },
        "structure": {
            "agents": agents,
            "commands": commands,
            "skills": skills,
            "tools": tools,
            "templates": templates,
        },
        "files": files,
        "checksums": {rel: f"sha256:{sha256(ROOT / rel)}" for rel in checksum_scope},
        "checksum_scope": "manifest checksums exclude MANIFEST.json and CHECKSUMS.sha256; CHECKSUMS.sha256 covers every release file except itself",
    }


def main() -> None:
    # Both generated files already exist in the repository and therefore belong in the stable file list.
    files = release_files()
    manifest = build_manifest(files)
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    files = release_files()
    lines = [f"{sha256(ROOT / rel)}  {rel}" for rel in files if rel != "CHECKSUMS.sha256"]
    CHECKSUMS.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(manifest["counts"], sort_keys=True))


if __name__ == "__main__":
    main()
