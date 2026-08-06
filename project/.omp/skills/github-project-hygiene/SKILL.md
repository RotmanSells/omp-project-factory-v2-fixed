    ---
    name: github-project-hygiene
    description: "Prepare clean local GitHub artifacts without mutating GitHub state."
    ---
    # Purpose
    Prepare clean local GitHub artifacts without mutating GitHub state.

    # Operating rules
    - draft locally only
- no push, merge, tag or publication
- outbox content must map clearly to stage/task state
