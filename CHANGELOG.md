# Changelog

## 2.1.0 - 2026-08-06

- fixed OMP skill discovery by moving all `SKILL.md` frontmatter to byte zero
- added `review_report` guarded tool and reviewer-specific structured evidence
- fixed sequential task and stage lifecycle so completed work can advance to the next task/stage
- restricted owner override to the exact pre-block state and added runtime enum validation
- made `task_commit` enforce stage branch, started HEAD, approved contract, fresh PASS gates, fresh role-bound reviews and rollback on commit failure
- made `mission_commit` enforce mission state, fresh PASS gate and fresh documentation review
- hardened quality-gate command validation, package-manager scripts and repository-path/symlink containment
- replaced destructive install/uninstall behavior with preservation, installation ledger, backups and reversible quarantine
- added tests for multiple tasks/stages, stale evidence, review provenance, installer preservation and path escapes
- added GitHub Actions verification and deterministic release metadata generation
- aligned DESIGN, ROADMAP, PLAN STAGE, RUN TASK, CLOSE STAGE and PREPARE GITHUB with the approved owner workflow
- Project Atlas intentionally remains out of scope

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
