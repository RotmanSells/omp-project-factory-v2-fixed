    ---
    name: testing-strategy
    description: "Choose the narrowest useful tests that defend observable contracts."
    ---
    # Purpose
    Choose the narrowest useful tests that defend observable contracts.

    # Operating rules
    - match the changed contract with the narrowest convincing test level
- prefer focused unit or integration tests before expensive suites
- do not test incidental defaults or source text
