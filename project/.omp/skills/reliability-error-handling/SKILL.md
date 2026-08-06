    ---
    name: reliability-error-handling
    description: "Design for failure handling and operator clarity."
    ---
    # Purpose
    Design for failure handling and operator clarity.

    # Operating rules
    - document retries, backoff, idempotency and failure modes
- prefer explicit errors over swallowed exceptions
- state how operators detect and recover from faults
