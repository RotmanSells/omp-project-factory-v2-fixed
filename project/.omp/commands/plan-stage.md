# plan-stage

## Purpose

Plan one current vertical stage: keep a short map of the whole stage and fully specify exactly the nearest three tasks.

## Preconditions

- project phase is `implementation`;
- previous stage is `done` or absent;
- target stage is the current or first unstarted stage;
- no unresolved owner block exists.

## Exact order

1. Read roadmap, approved architecture, current code, relevant history and state.
2. Start a new stage at `planning`, or validate the current planning stage.
3. Run `task-planner` to create the complete short stage map and exactly three detailed task contracts.
4. Every detailed task must progress `draft -> owner_review -> approved` and include business outcome, scope, non-scope, invariants, contracts, allowed paths, expected commit, tests, docs, risks and reviewer matrix.
5. Run `task-critic` independently against verticality, size, sequencing, DoD and architecture consistency.
6. Escalate only decisions that change product outcome, architecture, security, data, migration, operating cost or release meaning.
7. Apply one fresh planner correction pass where needed.
8. Run `documentation-reviewer` on the resulting planning diff.
9. Record its verdict through `review_report` with `scope=mission`, `id=plan_stage`, role `documentation-reviewer`.
10. Run `quality_gate` with `scope=mission`, `id=plan_stage`; verdict must be `PASS`.
11. Transition stage `planning -> planned`.
12. Optionally register the first owner-approved task as `approved`; do not start it.
13. Commit only through `mission_commit` with mission `plan_stage`.
14. Stop. Do not start `/run-task` in this session.

## Rules

- later stage tasks remain short placeholders;
- Stage N+1 is not detailed before Stage N is done;
- 2500-3000 changed lines is a warning ceiling, not a target;
- one reviewer must be able to understand a task diff as one logical change;
- no application code, dependency installation or system mutation.

## Required evidence

- fresh task-critic result;
- fresh documentation-reviewer mission report tied to current diff;
- fresh mission quality report with verdict `PASS`.

## Final report

- stage outcome and complete short task map;
- exactly three detailed approved-or-review task contracts;
- critique and review outcomes;
- files changed and state transitions;
- blockers/warnings;
- next allowed mission.
