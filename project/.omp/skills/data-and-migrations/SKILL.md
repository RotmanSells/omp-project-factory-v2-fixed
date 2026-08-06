    ---
    name: data-and-migrations
    description: "Handle schemas, migrations and data ownership conservatively."
    ---
    # Purpose
    Handle schemas, migrations and data ownership conservatively.

    # Operating rules
    - document ownership, retention and rollback
- migrations require owner decision and explicit rollout notes
- avoid silent data rewrites or destructive cleanup
