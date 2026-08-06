# project-status


    ## Purpose

    Produce a read-only status report for the factory-managed repository.

    ## Read first

    - `docs/PROJECT_STATE.json`
    - stage README
    - current task file if present
    - `.project-factory/reports/`
    - `.project-factory/reviews/`

    ## Exact execution order

    1. Read state with `project_state` in status mode.
    2. Read Git branch, HEAD and dirty status through `git_inspect`.
    3. Summarize current phase, stage, task, latest gate/report freshness and blockers.
    4. State the next allowed mission only.

    ## Forbidden actions

    - no file writes
    - no state transition
    - no commit
    - no review fabrication

    ## Report format

    - project phase
    - current stage
    - current task
    - branch and HEAD
    - worktree status
    - latest quality reports
    - latest review reports
    - blockers/warnings
    - next allowed mission

