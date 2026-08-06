# plan-stage


    ## Purpose

    Plan the current stage only: full short map plus exactly three nearest detailed tasks.

    ## Prerequisites

    - project phase is `implementation`
    - target stage is current or first unstarted stage
    - previous stage is `done` or absent

    ## Read first

    - `.omp/RULES.md`
    - `docs/stages/ROADMAP.md`
    - stage README for the target stage
    - architecture and security docs
    - `docs/PROJECT_STATE.json`

    ## State checks

    - create or transition current stage to `planning`
    - after approval transition stage `planning -> planned`
    - optionally set `current_task` to the first approved task in `approved` status

    ## Exact execution order

    1. Read roadmap, current code, docs and relevant git history.
    2. Check architecture drift.
    3. Transition stage to `planning`.
    4. Run `task-planner` for the stage map and exactly three detailed tasks.
    5. Run `task-critic` on scope, DoD, tests, docs and reviewer matrix.
    6. Escalate owner questions only if they change scope or release meaning.
    7. Apply one correction pass if needed.
    8. Transition stage to `planned`.
    9. Optionally `mission_commit` docs/process changes.

    ## Agents and order

    - `task-planner`
    - `task-critic`
    - optional `task-planner` correction pass

    ## Allowed file changes

    - `docs/stages/**`
    - task files for current stage only
    - `docs/**`
    - `.project-factory/**`

    ## Forbidden file changes

    - application code
    - detailed tasks for Stage N+1
    - dependency or system mutation

    ## Ask the owner when

    - scope split changes customer-visible outcome
    - security/data/workflow decisions are missing
    - the current stage should be re-sliced

    ## Quality gates

    - maximum three detailed tasks
    - every task includes scope, non-scope, invariants, docs, tests, reviewers, expected commit
    - no architecture drift is hidden

    ## Stop conditions

    - blocking owner decision
    - stage is horizontal instead of vertical
    - more than three detailed tasks would be required

    ## Final report format

    - stage outcome
    - task map
    - first three detailed tasks
    - critique outcome
    - files changed
    - state transitions
    - next allowed mission

    ## No automatic next mission

    Do not start `/run-task` in the same session.

