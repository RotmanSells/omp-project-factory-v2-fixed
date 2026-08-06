# close-stage


    ## Purpose

    Close the active stage after all current-stage tasks are done and stage-level evidence is fresh.

    ## Prerequisites

    - current stage status is `active`
    - all stage tasks are `done`
    - branch is correct for the stage
    - working tree is clean before closeout starts

    ## Read first

    - `.omp/RULES.md`
    - `docs/PROJECT_STATE.json`
    - stage README
    - roadmap file
    - stage task files
    - observability, testing and release docs

    ## State checks

    - transition stage `active -> closing`
    - after evidence passes transition `closing -> done`

    ## Exact execution order

    1. Validate that all current-stage tasks are done.
    2. Transition stage to `closing`.
    3. Run stage/integration quality gates.
    4. Confirm the main E2E scenario.
    5. Confirm docs consistency, rollback notes, observability and demo script.
    6. Run conditional specialists if stage scope requires them.
    7. If gaps remain, create current-stage follow-up task drafts and stop without closing the stage.
    8. Transition stage to `done`.
    9. Update roadmap/readme/state docs.
    10. Optionally `mission_commit` docs/process changes.

    ## Agents and order

    - optional `documentation-writer`
    - `documentation-reviewer`
    - conditional specialist reviewers
    - optional `github-drafter` for local milestone summary

    ## Allowed file changes

    - stage README
    - roadmap docs
    - release/observability/testing docs
    - `.project-factory/**`
    - GitHub outbox drafts

    ## Forbidden file changes

    - application code unless explicitly required by an approved follow-up task
    - planning next stage in detail
    - GitHub publication

    ## Ask the owner when

    - stage closeout uncovers a release decision
    - main E2E fails and requires re-slicing the stage
    - unresolved production risk remains

    ## Quality gates

    - all stage tasks done
    - fresh integration evidence
    - main E2E confirmed
    - docs and demo are consistent
    - conditional security/load evidence where required

    ## Stop conditions

    - any current-stage task incomplete
    - E2E not confirmed
    - unresolved high-severity risk
    - stage would need follow-up work before being demo-complete

    ## Final report format

    - stage closeout result
    - evidence run
    - files changed
    - state transitions
    - warnings/blockers
    - next allowed mission

    ## No automatic next mission

    Do not start the next `/plan-stage` in the same session.

