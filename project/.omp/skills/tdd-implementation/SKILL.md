    ---
    name: tdd-implementation
    description: "Use TDD where behavior is risky, security-sensitive or regression-prone."
    ---
    # Purpose
    Use TDD where behavior is risky, security-sensitive or regression-prone.

    # Operating rules
    - mandatory for business rules, calculations, validation, auth, permissions, state transitions and regression fixes
- test public behavior first, then implement the smallest green change
- visual static polish does not require ritual test-first work
