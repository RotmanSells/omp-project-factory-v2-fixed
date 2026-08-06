# close-stage

## Purpose

Close the active stage only when its promised user-visible outcome is demonstrable and all stage evidence is fresh.

## Preconditions

- project phase is `implementation`;
- current stage is `active`;
- all current-stage tasks are `done`;
- current task is absent or `done`;
- branch matches `stage/<stage-id>-*`;
- working tree is clean before closeout work starts.

## Exact order

1. Validate state, task completion and branch.
2. Transition stage `active -> closing`.
3. Run stage/integration quality gates and the stage's main E2E scenario.
4. Run conditional security, data, performance or DevOps reviewers when stage risk requires them; record every verdict through `review_report` with `scope=mission`, `id=close_stage` and the exact reviewer role.
5. Confirm documentation, rollback, observability, demo script and known limitations.
6. Run `documentation-reviewer` on the closeout diff and record it through `review_report` with `scope=mission`, `id=close_stage`.
7. If the promised stage outcome still needs code, create current-stage follow-up task drafts and stop without marking the stage done.
8. Run `quality_gate` with `scope=mission`, `id=close_stage`; verdict must be `PASS`.
9. Update roadmap and stage README, then transition `closing -> done`.
10. Commit documentation/process changes only through `mission_commit` with mission `close_stage`.
11. Stop. Only a new session may plan the next stage.

## Forbidden

- application-code fixes hidden inside closeout;
- detailed planning of the next stage;
- skipping failed E2E, reviews or quality gates;
- GitHub publication, push or merge.

## Required evidence

- all stage tasks completed;
- fresh stage/integration report with `PASS`;
- confirmed main E2E;
- fresh documentation review;
- applicable specialist reviews tied to current diff.

## Final report

- stage outcome and demonstration result;
- gates and reviews actually run;
- files changed and state transitions;
- known limitations and rollback notes;
- blockers/warnings;
- next allowed mission.
