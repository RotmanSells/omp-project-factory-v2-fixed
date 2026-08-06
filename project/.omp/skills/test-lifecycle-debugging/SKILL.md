    ---
    name: test-lifecycle-debugging
    description: "Debug flaky or lifecycle-heavy tests causally, not by brute force."
    ---
    # Purpose
    Debug flaky or lifecycle-heavy tests causally, not by brute force.

    # Operating rules
    - reproduce first with the smallest suite
- one hypothesis at a time, maximum two failed hypotheses before replanning
- no sleeps, force exits or weakened assertions without causal proof
