    ---
    name: stack-rule-authoring
    description: "Adapt quality gates and process rules to the chosen stack without weakening safety."
    ---
    # Purpose
    Adapt quality gates and process rules to the chosen stack without weakening safety.

    # Operating rules
    - map formatter, lint, type/static check and tests to real project commands
- do not invent commands that the repository cannot run
- prefer exact allowlists over open-ended shells
