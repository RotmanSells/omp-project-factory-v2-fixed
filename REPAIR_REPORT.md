# Repair Report

## Исходное фактическое состояние открытого проекта

Аудит выполнялся по открытому каталогу, а не по внешнему ZIP. На момент старта были подтверждены:

- root scripts: `audit.sh`, `install.sh`, `verify.sh`, `uninstall.sh`
- root docs: `README_RU.md`, `MANIFEST.json` и несколько вспомогательных `.md`
- `profile/config.yml`
- `project/.omp/commands/*.md`
- `project/.omp/agents/*.md`
- `project/.omp/skills/*/SKILL.md`
- `project/.omp/tools/*.ts`
- `templates/*`

Фактические counts до ремонта:

- agents: 16
- commands: 7
- skills: 26
- tools: 3
- templates: 8

## Что отсутствовало или было неполным

- не было `CHANGELOG.md`
- не было `REPAIR_REPORT.md`
- не было `CHECKSUMS.sha256`
- не было `project/AGENTS.md`
- не было полного docs skeleton внутри `project/docs/`
- не было `.project-factory/reports/`, `.project-factory/reviews/`, `.project-factory/github-outbox/` как install payload
- не хватало templates для GitHub issue/pr/milestone drafts
- корневой `MANIFEST.json` содержал только marketing counts без file list и checksums
- state machine была плоской и противоречивой
- отсутствовали `mission_commit` и `git_inspect`
- read-only reviewers имели лишний `bash`
- commands и agent instructions были слишком короткими для автономного исполнения

## Исправленные архитектурные противоречия

- плоская state machine заменена на schema v2 с раздельными `project.phase`, `current_stage.status`, `current_task.status`
- добавлен history trail с `actor`, `scope`, `from`, `to`, `reason`, `branch`, `head`, `timestamp`
- переход в `blocked_owner_decision` отделён от обычного progress path
- возврат из blocked выполняется только через явный `owner_override`
- `RUN TASK` теперь согласован с `planned -> active -> closing -> done`
- документационные миссии получили отдельный `mission_commit`, чтобы не злоупотреблять `task_commit`

## Новая state machine

- project: `brief -> design_in_progress -> architecture_owner_review -> architecture_approved -> roadmap_in_progress -> roadmap_approved -> implementation -> completed`
- stage: `planning -> planned -> active -> closing -> done`
- task: `draft -> owner_review -> approved -> in_progress -> in_review -> ready_to_commit -> done`
- дополнительный status/phase: `blocked_owner_decision`

`project_state` блокирует запрещённые переходы и пишет history atomically.

## Безопасность commit tools

### `task_commit`

Перед commit выполняется полный preflight:

- protected branch block
- active stage check
- `ready_to_commit` task check
- approved contract hash check
- allowed paths читаются из task contract, а не из аргумента модели
- stale quality report detection через `diff_hash`
- stale review detection через `diff_hash`
- required review matrix читается из task contract
- conditional specialist reviews required when task contract их указывает
- commit message сверяется с `expected_commit`
- `git diff --check` обязателен
- state не мутируется до успешного commit

### `mission_commit`

- работает только на non-main branch
- разрешён только для mission types `design`, `roadmap`, `plan_stage`, `close_stage`, `prepare_github`
- сам определяет allowlist paths по mission policy
- блокирует application code и shell/GitHub mutation outside policy
- не выполняет push/merge/tag

## Защита от stale reports

`quality_gate` и review reports пишут:

- branch
- HEAD
- base commit
- `diff_hash`
- timestamps

`task_commit` и `mission_commit` сравнивают report `diff_hash` с текущим diff. Любое изменение после review или gate делает report stale.

## Ограничения reviewer roles

Read-only reviewers переведены на набор tools без `write/edit/bash`:

- `read`
- `grep`
- `glob`
- `lsp`
- `git_inspect`

Это касается `reviewer`, `security-reviewer`, `data-reviewer`, `performance-reviewer`, `devops-reviewer`, `documentation-reviewer`, `roadmap-critic`, `task-critic`, `architecture-critic`.

## Commit для документационных миссий

Старый Git-тупик снят через `mission_commit`. Он предназначен для:

- `DESIGN`
- `ROADMAP`
- `PLAN STAGE`
- `CLOSE STAGE`
- `PREPARE GITHUB`

Он разрешает только documentation/process/outbox paths по policy и не трогает application code.

## Результаты проверок

Подтверждены фактические прогоны: `bash -n audit.sh install.sh verify.sh uninstall.sh`, `node tests/run-tests.mjs`, `audit.sh <control-repo>`, `install.sh <control-repo>` dry-run, `install.sh --apply <control-repo>`, `verify.sh <control-repo>`, `uninstall.sh --apply <control-repo>`, сборка `omp-project-factory-v2-fixed.zip`, контрольная распаковка ZIP и сверка `MANIFEST.json` + `CHECKSUMS.sha256`. Финальный SHA-256 ZIP фиксируется внешне в deliverable summary, а не внутри package-файлов, потому что встраивание хеша архива в содержимое самого архива делает хеш самоссылочным и меняет результат.

## Точные ограничения проверки

В текущей среде реально доступны:

- `omp/17.2.9`
- `omp config list --json`
- `omp --profile factory models`
- `bun`
- `node`
- `python3`
- `git`

В этой среде `omp --profile factory models` вернул отсутствие настроенных моделей. Поэтому model availability не подтверждена runtime’ом; package оставляет централизованные aliases и требует owner-side model assignment. Отдельно: финальный SHA-256 ZIP нельзя честно зафиксировать внутри самого архива без самоссылочного изменения архива; поэтому он сообщается внешне в deliverable summary.

## Оставшиеся риски

- OMP mission discovery не имеет удобного non-interactive API, поэтому commands/agents/skills discovery подтверждается статически и частично конфигурационно.
- Определение “чужих pre-existing изменений внутри allowed paths” в `task_commit` остаётся best-effort и опирается на clean-tree preflight в начале task и history state transition.
- Конкретные quality gates для non-Node stacks остаются проектной настройкой после DESIGN.
