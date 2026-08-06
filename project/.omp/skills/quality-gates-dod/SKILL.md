---
name: quality-gates-dod
description: "Unify task/stage quality gates and Definition of Done."
---
# Purpose
Unify task/stage quality gates and Definition of Done.

# Operating rules
- task completion requires fresh formatter/lint/type checks, focused tests, docs and review evidence where configured
- stage completion requires integration, main E2E, docs consistency and conditional security/load evidence
- SKIP or NOT_CONFIGURED is never the same as PASS
