# prepare-github


    ## Purpose

    Prepare local GitHub drafts only. No publication, no push, no merge, no application code changes.

    ## Prerequisites

    - state file exists
    - current stage/task can be determined from state or docs

    ## Read first

    - `.omp/RULES.md`
    - `docs/PROJECT_STATE.json`
    - current stage README
    - relevant task files
    - `.project-factory/github-outbox/`

    ## State checks

    - no project phase transition is required by default
    - if a documentation/process commit is desired, use `mission_commit` with mission type `prepare_github`

    ## Exact execution order

    1. Read current state and current stage/task context.
    2. Run `github-drafter`.
    3. Generate local Issue, PR and Milestone drafts only.
    4. Verify that only `.project-factory/github-outbox/**` changed unless docs explicitly require summary updates.
    5. Optionally `mission_commit` the outbox/process diff.

    ## Agents and order

    - `github-drafter`

    ## Allowed file changes

    - `.project-factory/github-outbox/**`
    - optional docs summaries required by the repo process

    ## Forbidden file changes

    - application code
    - push
    - merge
    - tag
    - mutating `gh` commands
    - publication of Issue/PR/Milestone drafts

    ## Ask the owner when

    - draft contents expose sensitive information
    - publication is requested, because publication is outside this command

    ## Quality gates

    - local-only outbox files
    - no mutating GitHub command in scripts or reports

    ## Stop conditions

    - requested action would publish or mutate GitHub
    - diff escapes outbox/doc scope

    ## Final report format

    - drafts created
    - files changed
    - verification run
    - warnings/blockers
    - next allowed mission

    ## No automatic next mission

    Do not publish anything automatically.

