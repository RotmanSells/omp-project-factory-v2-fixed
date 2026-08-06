# prepare-github

## Purpose

Prepare local Issue, PR and Milestone drafts only. This mission never publishes, pushes, merges or tags.

## Preconditions

- state validates;
- current stage/task context can be determined;
- requested artifacts do not require exposing secrets or private data.

## Exact order

1. Read project state, roadmap, current stage README and relevant task contracts.
2. Run `github-drafter` to create local drafts under `.project-factory/github-outbox/**`.
3. Verify that drafts trace Stage -> Milestone, Task -> Issue and stage branch -> draft PR.
4. Verify no application code or unrelated docs changed.
5. Run `documentation-reviewer` on draft accuracy and record the verdict through `review_report` with `scope=mission`, `id=prepare_github`, role `documentation-reviewer`.
6. Run `quality_gate` with `scope=mission`, `id=prepare_github`; verdict must be `PASS`.
7. Optionally commit local outbox/process files through `mission_commit` with mission `prepare_github`.
8. Stop. Do not publish anything.

## Allowed changes

- `.project-factory/github-outbox/**`
- `.project-factory/reports/**`
- `.project-factory/reviews/**`

## Forbidden

- application code;
- `git push`, merge, rebase or tag;
- mutating `gh` or GitHub API commands;
- automatic Issue, PR or Milestone creation;
- secrets, tokens, private customer data or internal credentials in drafts.

## Required evidence

- fresh documentation-reviewer mission report tied to current diff;
- fresh mission quality report with verdict `PASS`;
- changed-file scope restricted to local outbox/evidence files.

## Final report

- drafts created;
- files changed;
- verification actually run;
- warnings about sensitive information;
- next allowed mission.
