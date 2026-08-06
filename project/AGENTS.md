# Project AGENTS

This repository is an OMP Project Factory package, not an application repository.

## Core rules

- Treat `project/.omp/RULES.md` as the immutable process rules.
- Treat `project/.omp/APPEND_SYSTEM.md` as the Main orchestration contract.
- Commands under `project/.omp/commands/*.md` are the supported mission entrypoints.
- Custom tools under `project/.omp/tools/*.ts` are part of the safety boundary.
- `project/.omp/mcp.json` must stay empty in core package.
- Do not install dependencies, MCP servers or plugins from package scripts.
- Do not enable worktree isolation by default.
- Do not publish GitHub changes from this package.

## Layout

- `project/.omp/` — commands, agents, skills, tools and watchdog.
- `project/docs/` — documentation skeleton for the target repository.
- `project/.project-factory/` — reports, reviews and GitHub drafts.

## Validation

Run `./verify.sh` after changing package files. The package is only valid when the local static checks and Node test harness pass.
