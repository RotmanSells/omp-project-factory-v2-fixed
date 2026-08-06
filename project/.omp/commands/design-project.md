# design-project


    ## Purpose

    Run the DESIGN mission without writing application code.

    ## Prerequisites

    - `docs/PROJECT_STATE.json` exists and validates.
    - Project phase is `brief` or `blocked_owner_decision` resumed by explicit owner override.
    - `PROJECT_BRIEF.md` exists.
    - No active implementation task is in progress.

    ## Read first

    - `.omp/RULES.md`
    - `.omp/APPEND_SYSTEM.md`
    - `.omp/WATCHDOG.md`
    - `PROJECT_BRIEF.md`
    - `docs/00-INDEX.md`
    - `docs/PROJECT_STATE.json`
    - relevant ADR files if they already exist

    ## State checks

    - validate state schema version 2 with `project_state`
    - transition project `brief -> design_in_progress`
    - later transition `design_in_progress -> architecture_owner_review`
    - after explicit owner approval transition `architecture_owner_review -> architecture_approved`

    ## Exact execution order

    1. Restate the product, contradictions and unknowns.
    2. Ask 5-7 highest-impact owner questions.
    3. Stop if blocking questions remain unanswered.
    4. Run `stack-researcher` for current evidence and decision matrix.
    5. Run `architecture-critic` on the proposed architecture and stack.
    6. Show substantial disagreements to the owner.
    7. Stop until owner decisions are explicit.
    8. Transition project to `architecture_owner_review`.
    9. After approval, run `documentation-writer` with exact allowed files.
    10. Run `documentation-reviewer` against produced docs.
    11. If gaps are confirmed, run one more `documentation-writer` pass and re-review.
    12. Transition project to `architecture_approved` and record owner decision summary.
    13. Optionally use `mission_commit` for documentation/process-only changes.

    ## Agents and order

    - `stack-researcher`
    - `architecture-critic`
    - `documentation-writer`
    - `documentation-reviewer`

    Only one agent runs at a time.

    ## Allowed file changes

    - `PROJECT_BRIEF.md`
    - `docs/**`
    - `.project-factory/**`

    ## Forbidden file changes

    - application code
    - dependency manifests
    - lockfiles
    - `package.json`, `go.mod`, `Cargo.toml`, `pyproject.toml` unless owner explicitly approved system change
    - `.omp/tools/**`

    ## Ask the owner when

    - product meaning changes
    - stack choice changes cost, security or lock-in
    - architecture disagreement changes boundaries or ops model
    - compliance, privacy or migration decisions are unresolved

    ## Quality gates

    - docs review must be fresh for the current diff
    - no claimed research without sources
    - no architecture approval without explicit owner decision

    ## Stop conditions

    - unanswered blocking owner question
    - unresolved architecture disagreement
    - docs review still reports material gap after two writer/review cycles
    - any proposed change escapes documentation/process scope

    ## Final report format

    - decisions
    - files changed
    - state transitions
    - reviewer outcome
    - verification actually run
    - blockers/warnings
    - next allowed mission

    ## No automatic next mission

    Do not start ROADMAP in the same session.

