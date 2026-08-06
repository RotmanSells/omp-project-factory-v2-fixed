# Project Factory Rules

## Source of truth

- Approved documentation is the source of truth.
- `docs/PROJECT_STATE.json` is the canonical state file.
- `ROADMAP.md`, stage README files and approved task files define allowed scope.
- Contradiction between docs, state and code means stop, not guess.

## Mission boundaries

- One OMP session executes one mission.
- Do not start the next mission automatically.
- Main orchestrates; Main does not write application code.
- One writer at a time.
- One task at a time.

## Planning

- Stages must be vertical user-visible slices.
- Stage N+1 must not be detailed before Stage N is done.
- Only the nearest three tasks may be fully detailed.
- Every task must have explicit scope, non-scope, invariants, tests, docs and reviewer matrix.

## Implementation and Git

- Clean working tree is required before `RUN TASK` starts.
- Writer does not commit.
- Review happens on the uncommitted diff.
- One task = one logical commit.
- Task commit is allowed only through `task_commit`.
- Mission/process commits are allowed only through `mission_commit`.
- Protected branches are never committed to by package tools.
- Push, merge, tag and GitHub publication are forbidden.

## Quality

- TDD is mandatory for business rules, validation, auth, permissions, calculations, state transitions, payments and regression fixes.
- Test observable behavior, not implementation details.
- Final gates must be fresh for the current diff.
- Review reports must be fresh for the current diff.
- Sensitive work requires security review.
- Data-changing work requires data review.
- Performance-sensitive work requires performance review.
- Infrastructure work requires DevOps review.

## Critical change

When architecture, stage boundary, public contract, data model or security assumptions are threatened:

1. stop implementation;
2. report `[CRITICAL CHANGE]`;
3. show options and consequences;
4. wait for owner decision.

## Honesty

- Never claim PASS for an unrun command.
- Never claim review, E2E or manual verification without direct evidence.
- Separate warnings from failures.
- Report disagreements explicitly.
