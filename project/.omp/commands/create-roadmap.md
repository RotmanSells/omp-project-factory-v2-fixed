# create-roadmap


    ## Purpose

    Create or revise a roadmap of independent vertical stages from approved documentation only.

    ## Prerequisites

    - project phase is `architecture_approved`
    - no blocked owner decision remains open
    - documentation index and architecture docs exist

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

    ## State checks

    - transition project `architecture_approved -> roadmap_in_progress`
    - after roadmap approval transition `roadmap_in_progress -> roadmap_approved`
    - then transition `roadmap_approved -> implementation`

    ## Exact execution order

    1. Read approved documentation and ADRs.
    2. Run `roadmap-planner` to draft vertical stages with outcomes and DoD.
    3. Run `roadmap-critic` against verticality, sequencing, dependencies and risk.
    4. Escalate only material owner questions.
    5. Apply approved corrections through one fresh planner pass if needed.
    6. Write the final roadmap docs.
    7. Mark roadmap approved.
    8. Optionally `mission_commit` the documentation/process diff.

    ## Agents and order

    - `roadmap-planner`
    - `roadmap-critic`
    - optional `roadmap-planner` correction pass

    ## Allowed file changes

    - `docs/stages/ROADMAP.md`
    - `docs/**`
    - `.project-factory/**`

    ## Forbidden file changes

    - application code
    - future detailed task files beyond the nearest current stage work
    - GitHub publication

    ## Ask the owner when

    - stage ordering changes business priority
    - a stage boundary changes product commitment or release sequencing
    - a stage requires deferred legal/security/compliance decision

    ## Quality gates

    - stages must be vertical slices
    - every stage must have outcome, scope and Definition of Done
    - future stages must stay high level

    ## Stop conditions

    - blocking owner decision
    - unresolved roadmap critique that changes release structure
    - roadmap becomes horizontal or technology-layer based

    ## Final report format

    - roadmap decisions
    - stage list
    - files changed
    - state transitions
    - critique outcome
    - verification actually run
    - next allowed mission

    ## No automatic next mission

    Do not start stage planning in the same session.

