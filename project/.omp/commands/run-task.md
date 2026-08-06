# run-task


    ## Purpose

    Implement exactly one approved task with one writer, fresh gates, fresh reviews and one guarded commit.

    ## Prerequisites

    - target task exists and is approved
    - project phase is `implementation`
    - current stage is `planned` or `active`
    - working tree is clean before task start
    - current branch is non-main and matches the active stage

    ## Read first

    - `.omp/RULES.md`
    - `.omp/APPEND_SYSTEM.md`
    - `docs/PROJECT_STATE.json`
    - current stage README
    - approved task file
    - relevant module README docs
    - related source files and tests

    ## State checks

    - transition task `approved -> in_progress`
    - if stage is `planned`, transition stage `planned -> active`
    - before commit transition task `in_progress -> in_review -> ready_to_commit`
    - final `ready_to_commit -> done` is performed only by `task_commit`

    ## Exact execution order

    1. Confirm clean tree and protected-branch avoidance.
    2. Run `implementation-orchestrator` for preflight and task-risk checklist.
    3. Transition task to `in_progress`.
    4. Run `developer` with exact scope, invariants and allowed files.
    5. Run `test-engineer` only when test work is required or the developer report says so.
    6. Run `quality_gate` with `scope=task` and task id.
    7. Run `reviewer`.
    8. Run conditional specialists from the task contract.
    9. If fixes are confirmed, launch a fresh writer and repeat affected reviews and gates.
    10. Transition task to `in_review`, then `ready_to_commit`.
    11. Run `task_commit`.
    12. Report SHA, fresh gate path, fresh review paths and warnings.

    ## Agents and order

    - `implementation-orchestrator`
    - `developer`
    - optional `test-engineer`
    - `reviewer`
    - conditional `security-reviewer`
    - conditional `data-reviewer`
    - conditional `performance-reviewer`
    - conditional `devops-reviewer`

    ## Allowed file changes

    - only files listed in the approved task contract
    - task docs, stage README, module README and related report files required by the task contract

    ## Forbidden file changes

    - files outside approved task scope
    - Git metadata by hand
    - dependency installation
    - migrations/system changes without owner decision
    - next task docs beyond required handoff updates

    ## Ask the owner when

    - public contract, data model or architecture would change
    - migration or dependency change becomes necessary
    - a critical ambiguity blocks safe implementation

    ## Quality gates

    - TDD where required by the task contract
    - focused tests for the changed contract
    - fresh task quality report
    - fresh reviewer reports tied to current diff hash
    - expected commit message matches the approved task contract

    ## Stop conditions

    - dirty tree before task start
    - stale review or stale quality report
    - unexpected changed file
    - unresolved reviewer finding
    - architecture conflict

    ## Final report format

    - implementation summary
    - files changed
    - verification actually run
    - reviewer verdicts
    - commit SHA
    - state transitions
    - warnings/blockers
    - next allowed mission

    ## No automatic next mission

    Do not start the next task in the same session.

