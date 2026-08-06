# Changelog

## 2.0.1 - 2026-08-06

- rebuilt package structure around the actually present project files
- added missing root artifacts: `CHANGELOG.md`, `REPAIR_REPORT.md`, `CHECKSUMS.sha256`
- expanded templates set to required brief/state/stage/task/ADR/module/GitHub templates
- added project docs skeleton and install-time project payload
- redesigned state machine to schema version 2 with separate project/stage/task status handling and history
- added guarded custom tools: `project_state`, `quality_gate`, `task_commit`, `mission_commit`, `git_inspect`
- removed `bash` from read-only reviewer agents and replaced it with `git_inspect`
- added implementation orchestrator agent and expanded all agent instructions
- expanded skills set and aligned `autoloadSkills`
- rewrote mission commands with prerequisites, stop conditions and exact sequencing
- rewrote install/audit/verify/uninstall scripts with dry-run, backups and package validation
- added Node-based local test harness for safety tools and package behavior
