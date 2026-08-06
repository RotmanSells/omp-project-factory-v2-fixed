# design-project

## Purpose

Run DESIGN only: clarify the product, research current options, resolve material disagreements with the owner, and produce approved governing documentation. Do not write application code.

## Preconditions

- `PROJECT_BRIEF.md` exists.
- `docs/PROJECT_STATE.json` validates.
- Project phase is `brief`, or a prior owner block has been explicitly resumed.
- Work is on a non-protected branch, normally `stage/00-design`.

## Read first

- `.omp/RULES.md`
- `.omp/APPEND_SYSTEM.md`
- `.omp/WATCHDOG.md`
- `PROJECT_BRIEF.md`
- `docs/00-INDEX.md`
- `docs/PROJECT_STATE.json`
- existing ADRs

## Exact order

1. Validate state and transition `brief -> design_in_progress`.
2. Restate the product, users, journeys, constraints, contradictions and unknowns.
3. Ask 5-7 highest-impact owner questions per round; stop while a blocking answer is missing.
4. Run `stack-researcher` with current primary-source evidence and a decision matrix.
5. Produce the proposed architecture and run `architecture-critic` independently.
6. Show material disagreements as options, consequences and a recommendation. Do not force artificial consensus.
7. Stop for explicit owner decisions where product meaning, cost, security, compliance, migration or lock-in changes.
8. Transition `design_in_progress -> architecture_owner_review`.
9. After explicit approval, run `documentation-writer` for the approved docs and stack-specific `AGENTS.md` rules.
10. Run `documentation-reviewer` against the current diff.
11. Record its verdict through `review_report` with `scope=mission`, `id=design`, and role `documentation-reviewer`.
12. If findings are confirmed, run one fresh writer pass, then repeat documentation review and `review_report` for the new diff.
13. Run `quality_gate` with `scope=mission`, `id=design`; verdict must be `PASS`.
14. Transition `architecture_owner_review -> architecture_approved`, recording the owner decision summary and architecture version.
15. Commit documentation/process changes only through `mission_commit` with mission `design`.
16. Stop. Do not start ROADMAP in this session.

## Allowed changes

- `PROJECT_BRIEF.md`
- `docs/**`
- `.project-factory/**`
- stack-specific `AGENTS.md`

## Forbidden

- application code
- dependency installation
- migrations or system mutation
- fabricated research, tests, review or approval
- starting ROADMAP automatically

## Required evidence

- explicit owner decisions for material disputes
- fresh `documentation-reviewer` mission report tied to current `HEAD` and `diff_hash`
- fresh mission quality report with verdict `PASS`

## Final report

- decisions and unresolved questions
- files changed
- state transitions
- evidence actually produced
- warnings/blockers
- next allowed mission
