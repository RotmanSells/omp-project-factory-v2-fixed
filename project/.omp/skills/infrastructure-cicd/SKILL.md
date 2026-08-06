---
name: infrastructure-cicd
description: "Review infrastructure and CI/CD impact with rollback and blast radius in mind."
---
# Purpose
Review infrastructure and CI/CD impact with rollback and blast radius in mind.

# Operating rules
- separate build-time, deploy-time and runtime changes
- prefer reversible changes and explicit rollback steps
- infra changes need evidence for environment compatibility
