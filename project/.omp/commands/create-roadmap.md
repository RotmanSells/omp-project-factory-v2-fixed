# create-roadmap

## Purpose
Create a roadmap of independent vertical stages from approved architecture only. Do not write application code or detailed future tasks.

## Prerequisites
- project phase is `architecture_approved`
- no owner decision is blocked
- approved requirements, architecture, security and ADR documents exist
- working branch is non-protected

## Read first
- `.omp/RULES.md`
- `.omp/APPEND_SYSTEM.md`
- `docs/00-INDEX.md`
- `docs/01-PRODUCT.md`
- `docs/02-REQUIREMENTS.md`
- `docs/03-NON-FUNCTIONAL.md`
- `docs/04-ARCHITECTURE.md`
- `docs/07-SECURITY.md`
- `docs/PROJECT_STATE.json`
- `docs/adr/**`

## State checks
- `architecture_approved -> roadmap_in_progress`
- after explicit owner acceptance: `roadmap_in_progress -> roadmap_approved`
- after the roadmap mission commit: `roadmap_approved -> implementation`

## Exact execution order
1. Read only approved product and architecture sources.
2. Run `roadmap-planner` to draft vertical, demonstrable stages.
3. Each stage must include outcome, user journey, dependencies, scope, non-scope, components, data/API/security impact, tests, main E2E, risks, demonstration and Definition of Done.
4. Run `roadmap-critic` independently.
5. Show material disagreements and consequences to the owner; do not force artificial agreement.
6. Apply one approved correction pass.
7. Transition to `roadmap_approved` only after explicit owner acceptance.
8. Run `quality_gate` with `scope=mission`, `id=roadmap`.
9. Run `documentation-reviewer`; it must store `mission-roadmap--documentation-reviewer.json` through `review_report` using task id `mission-roadmap`.
10. If the diff changes, rerun the gate and documentation review.
11. Run `mission_commit` with `mission=roadmap`.
12. Transition project to `implementation` and stop.

## Planning rules
- stages are vertical slices, not separate database/API/UI layers
- every stage ends in a demonstrable working user outcome
- the whole roadmap is high-level
- no detailed task contracts are created here
- Stage N+1 is not detailed before Stage N is done

## Allowed changes
- `docs/stages/ROADMAP.md`
- stage overview documents
- related approved documentation corrections
- `docs/PROJECT_STATE.json`
- `.project-factory/reports/**`
- `.project-factory/reviews/**`

## Forbidden
- application code
- dependency installation
- detailed task files
- GitHub publication, push, merge or tag

## Stop and ask owner when
- stage order changes business priority
- a boundary changes a product or release commitment
- security, privacy, compliance, cost or vendor lock-in remains unresolved
- critic and planner materially disagree

## Final report
- owner decisions
- vertical stage list
- files changed
- state transitions
- quality report path
- documentation review path
- mission commit SHA
- blockers/warnings
- next allowed mission: `/plan-stage <id>` in a new session

Do not start stage planning in this session.
