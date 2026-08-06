from pathlib import Path
import textwrap

ROOT = Path('.')


def w(path: str, content: str) -> None:
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(content).lstrip('\n'), encoding='utf-8')


def skill_doc(name: str, description: str, bullets: list[str]) -> str:
    bullet_text = '\n'.join(f'- {b}' for b in bullets)
    return f'''\
    ---
    name: {name}
    description: "{description}"
    ---
    # Purpose
    {description}

    # Operating rules
    {bullet_text}
    '''


def agent_doc(name: str, description: str, tools: list[str], model: str, skills: list[str], body: str) -> str:
    tools_text = '[' + ', '.join(tools) + ']'
    skills_text = '[' + ', '.join(skills) + ']'
    return f'''\
    ---
    name: {name}
    description: "{description}"
    tools: {tools_text}
    spawns: []
    model: "{model}"
    thinking-level: high
    blocking: true
    autoloadSkills: {skills_text}
    ---
    {body}
    '''


def command_doc(title: str, body: str) -> str:
    return f'''\
    # {title}

    {body}
    '''


README = r'''
# OMP Project Factory v2 Fixed

OMP Project Factory v2 Fixed — пакет процесса для Oh My Pi, который навязывает безопасный mission-driven workflow поверх обычного Git-репозитория. Это не application runtime и не dependency bundle. Пакет устанавливает профиль, project commands, project agents, skills, custom tools, templates и safety scripts.

## Что такое Factory v2

Factory v2 разделяет разработку на отдельные миссии:

1. `DESIGN`
2. `ROADMAP`
3. `PLAN STAGE`
4. `RUN TASK`
5. `CLOSE STAGE`
6. `PREPARE GITHUB`

Каждая миссия имеет отдельные preconditions, allowed files, state transitions, reviewer sequence и stop conditions. Main работает как оркестратор. Main не пишет application code.

## Архитектура миссий

- `DESIGN` — brief, owner questions, web research, stack decision matrix, architecture critique, owner decisions, documentation, documentation review.
- `ROADMAP` — только утверждённая документация, vertical slices, outcome и Definition of Done по stage, roadmap critique.
- `PLAN STAGE` — короткая карта всего текущего stage и подробно только три ближайшие задачи.
- `RUN TASK` — одна approved task, один writer, clean tree до старта, TDD там, где обязательно, focused tests, reviewer, conditional specialists, final gates, один guarded commit.
- `CLOSE STAGE` — integration, main E2E, conditional security/load, docs, closeout и разблокировка следующего stage.
- `PREPARE GITHUB` — только локальные Issue/PR/Milestone drafts, без публикации, push или merge.

## Ограничения

- без worktree по умолчанию;
- один shared working directory;
- одновременно пишет только один агент;
- одна task — один основной writer;
- Main не пишет application code;
- clean working tree перед `RUN TASK`;
- writer не выполняет commit;
- reviewer проверяет незакоммиченный diff;
- одна task = один логический commit;
- commit только через guarded custom tool;
- stage работает в отдельной non-main branch;
- запрещены автоматические push, merge, tag и GitHub publication;
- core package не устанавливает dependencies;
- core package не устанавливает MCP;
- core package не устанавливает plugins;
- установка dependencies, migrations, системные изменения, MCP и plugins требуют owner decision;
- Stage N+1 нельзя подробно планировать до закрытия Stage N;
- подробно планируются только три ближайшие задачи;
- архитектурное противоречие останавливает реализацию;
- нельзя заявлять PASS, review, E2E или manual result без фактической проверки.

## Структура пакета

```text
omp-project-factory-v2-fixed/
├── README_RU.md
├── CHANGELOG.md
├── REPAIR_REPORT.md
├── MANIFEST.json
├── CHECKSUMS.sha256
├── audit.sh
├── install.sh
├── verify.sh
├── uninstall.sh
├── tests/
├── profile/
├── templates/
└── project/
```

В `project/` лежит то, что копируется в целевой репозиторий: `AGENTS.md`, docs skeleton, `.project-factory/`, `.omp/commands/`, `.omp/agents/`, `.omp/skills/`, `.omp/tools/`.

## Установка

```bash
unzip omp-project-factory-v2-fixed.zip
cd omp-project-factory-v2-fixed

chmod +x audit.sh install.sh verify.sh uninstall.sh

./audit.sh /path/to/repository
./install.sh --apply /path/to/repository
./verify.sh /path/to/repository

cd /path/to/repository
omp --profile factory
```

## Audit

`audit.sh` работает read-only и не создаёт файлов. Он проверяет:

- наличие OMP;
- версию OMP;
- что путь существует и является Git repo;
- branch/status;
- наличие existing `.omp` и profile config;
- file conflicts;
- доступность обязательных runtimes;
- наличие конфликтующих rules/config;
- доступные OMP config keys.

## Verify

`verify.sh` выполняет:

- JSON validation;
- YAML validation;
- frontmatter validation для agents и skills;
- проверку broken `autoloadSkills`;
- наличие commands, agents, skills, tools и templates;
- `bash -n` для shell scripts;
- Node test harness для state machine и commit tools;
- static import check TypeScript tools через `node --experimental-strip-types`;
- manifest/count verification;
- executable permissions;
- проверку пустого `mcp.json`;
- поиск mutating GitHub commands;
- проверку отсутствия dependency installation в package scripts.

Если `omp` установлен, `verify.sh` дополнительно запускает:

- `omp --version`
- `omp config list --json`
- `omp --profile factory models`

Если модели не настроены, это фиксируется как `WARNING`, а не как `PASS`.

## Первый запуск

1. Заполнить `PROJECT_BRIEF.md`.
2. Создать `stage/00-design` или другую non-main branch.
3. Новая сессия: `/design-project`.
4. Новая сессия: `/create-roadmap`.
5. Новая сессия: `/plan-stage 01`.
6. Для каждой task новая сессия: `/run-task 01-001`.
7. После выполнения stage: `/close-stage 01`.
8. Для локальных GitHub drafts: `/prepare-github`.

## Правила веток

- `main` и `master` защищены.
- Stage работает в отдельной ветке вида `stage/<id>-<slug>`.
- `task_commit` и `mission_commit` отказываются работать на protected branch.
- Push, merge и tag не выполняются пакетом.

## DESIGN

`/design-project`:
- стартует только из `brief` или после owner override;
- переводит project в `design_in_progress`;
- проводит question rounds только по blocking decisions;
- запускает `stack-researcher`, затем `architecture-critic`, затем `documentation-writer`, затем `documentation-reviewer`;
- не начинает roadmap автоматически;
- фиксирует history state transitions.

## ROADMAP

`/create-roadmap`:
- стартует только из `architecture_approved`;
- переводит project в `roadmap_in_progress`;
- использует `roadmap-planner`, затем `roadmap-critic`;
- не детализирует будущие stages;
- завершает `roadmap_approved`, затем возвращает проект в `implementation`.

## PLAN STAGE

`/plan-stage`:
- работает только для текущего stage;
- переводит stage `planning -> planned`;
- использует `task-planner` и `task-critic`;
- создаёт короткую карту stage и ровно три ближайшие detailed tasks;
- не начинает coding.

## RUN TASK

`/run-task`:
- требует approved task и clean tree;
- первая task переводит stage `planned -> active`;
- запускает `implementation-orchestrator` для preflight, затем `developer`, опционально `test-engineer`, затем `reviewer` и conditional specialists;
- запускает `quality_gate`;
- завершает только через `task_commit`;
- не начинает следующую task автоматически.

## CLOSE STAGE

`/close-stage`:
- доступен только из `active` stage;
- переводит stage `active -> closing -> done`;
- требует integration suite, main E2E, docs consistency и conditional security/load checks;
- может использовать `mission_commit` для documentation/process commit;
- только после `done` разрешает следующий `/plan-stage`.

## PREPARE GITHUB

`/prepare-github`:
- не публикует изменения;
- не делает push, merge или tag;
- использует `github-drafter`;
- пишет только локальные drafts в `.project-factory/github-outbox/`;
- при необходимости фиксируется через `mission_commit` как documentation/process change.

## Model verification

Профиль использует только aliases через `modelRoles`. Текущая сборка не вшивает реальные provider-specific model IDs, потому что в среде проверки `omp --profile factory models` вернул `No models available. Set API keys in environment variables.`

Перед использованием назначьте модели под ваши provider credentials и проверьте:

```bash
omp --profile factory models
```

## Отсутствие dependencies, MCP и plugins

Пакет:
- не устанавливает `npm`, `pnpm`, `bun`, `pip`, `cargo`, `go` dependencies;
- не устанавливает MCP servers;
- не устанавливает plugins.

`project/.omp/mcp.json` остаётся пустым:

```json
{
  "mcpServers": {}
}
```

## Запрет `--yolo`

Не запускайте OMP с `--yolo`.

## Troubleshooting

- `task_commit` отказывает на `main/master` — создайте `stage/*` branch.
- `task_commit` считает report stale — diff изменился после review/gate; перезапустите reviewers/gates.
- `quality_gate` вернул `NOT_CONFIGURED` — адаптируйте `.project-factory/quality-gates.json` под ваш stack.
- `omp --profile factory models` не показывает модели — настройте provider credentials.
- `verify.sh` ругается на `autoloadSkills` — agent frontmatter ссылается на несуществующий skill.

## Uninstall

```bash
./uninstall.sh --apply /path/to/repository
```

Uninstall удаляет только установленный orchestration layer и profile config. Project docs и application code не удаляются.

## Известные ограничения

- OMP CLI не даёт удобного non-interactive listing для project command discovery, поэтому runtime discovery подтверждается статически по структуре файлов и частично через `omp config list --json`.
- Если task contract менялся после approval, нужен повторный owner approval и обновление `approved_contract_sha256`.
- `quality-gates.json` поставляется как безопасный шаблон. Для конкретного проекта его нужно адаптировать под стек после DESIGN.

## Что было проверено фактически

Эта сборка валидируется локально через:
- shell syntax checks;
- JSON/YAML parsing;
- static import/syntax check TypeScript tools;
- unit/integration tests для state machine, `quality_gate`, `task_commit`, `mission_commit` и `git_inspect`;
- build/re-extract контроль итогового ZIP;
- manifest/checksum verification.

Runtime execution inside a real interactive OMP mission подтверждается только частично: `omp --version`, `omp config list --json`, `omp --profile factory models`. В этой среде models discovery показал отсутствие настроенных моделей.
'''

CHANGELOG = r'''
# Changelog

## 2.0.1 - 2026-08-06

- rebuilt package structure around the actually present project files
- added missing root artifacts: `CHANGELOG.md`, `REPAIR_REPORT.md`, `CHECKSUMS.sha256`
- expanded templates set to required brief/state/stage/task/ADR/module/GitHub templates
- added project docs skeleton and install-time project payload
- redesigned state machine to schema version 2 with separate project/stage/task status handling and history
- added guarded custom tools: `project_state`, `quality_gate`, `task_commit`, `mission_commit`, `git_inspect`
- removed `bash` from read-only reviewer agents and replaced it with `git_inspect`
- added implementation orchestrator agent and expanded all agent instructions
- expanded skills set and aligned `autoloadSkills`
- rewrote mission commands with prerequisites, stop conditions and exact sequencing
- rewrote install/audit/verify/uninstall scripts with dry-run, backups and package validation
- added Node-based local test harness for safety tools and package behavior
'''

REPAIR_REPORT = r'''
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

Фактические результаты validation заполняются после запуска `verify.sh`, test harness и контрольной пересборки ZIP. Итоговые counts, checksums и runtime notes записываются в `MANIFEST.json` и итоговый раздел ниже.

## Точные ограничения проверки

В текущей среде реально доступны:

- `omp/17.2.9`
- `omp config list --json`
- `omp --profile factory models`
- `bun`
- `node`
- `python3`
- `git`

В этой среде `omp --profile factory models` вернул отсутствие настроенных моделей. Поэтому model availability не подтверждена runtime’ом; package оставляет централизованные aliases и требует owner-side model assignment.

## Оставшиеся риски

- OMP mission discovery не имеет удобного non-interactive API, поэтому commands/agents/skills discovery подтверждается статически и частично конфигурационно.
- Определение “чужих pre-existing изменений внутри allowed paths” в `task_commit` остаётся best-effort и опирается на clean-tree preflight в начале task и history state transition.
- Конкретные quality gates для non-Node stacks остаются проектной настройкой после DESIGN.
'''

ROOT_EXTRA = {
    'ARCHITECTURE_RU.md': '''
        # Архитектура пакета

        `OMP Project Factory v2 Fixed` состоит из четырёх слоёв:

        - profile config;
        - project payload (`project/.omp`, `project/docs`, `project/.project-factory`);
        - custom tools;
        - validation harness.

        Подробности и mission workflow описаны в `README_RU.md` и `REPAIR_REPORT.md`.
    ''',
    'CURRENT_LIMITATIONS_RU.md': '''
        # Известные ограничения

        - Для реального запуска нужны настроенные OMP provider credentials.
        - `quality-gates.json` требует адаптации под выбранный project stack.
        - Пакет сознательно не публикует GitHub artifacts и не делает push.
        - Worktree isolation не включён по умолчанию.
    ''',
    'MCP_PLUGIN_POLICY_RU.md': '''
        # MCP и plugins policy

        - Core package не устанавливает MCP.
        - Core package не устанавливает plugins.
        - `project/.omp/mcp.json` остаётся пустым.
        - Любое подключение MCP/plugins требует отдельного owner decision и должно быть отражено в docs.
    ''',
    'MODEL_MAPPING_RU.md': '''
        # Model mapping policy

        Модели задаются централизованно через `modelRoles` в `profile/config.yml` и `project/.omp/config.yml`.

        Agent files используют только aliases:

        - `@architect`
        - `@researcher`
        - `@critic`
        - `@developer`
        - `@tester`
        - `@reviewer`
        - `@security`
        - `@fast_worker`
    '''
}

PROFILE_CONFIG = r'''
modelRoles:
  default: your-provider/your-default-model
  architect: your-provider/your-architect-model
  researcher: your-provider/your-research-model
  critic: your-provider/your-critic-model
  developer: your-provider/your-developer-model
  tester: your-provider/your-tester-model
  reviewer: your-provider/your-reviewer-model
  security: your-provider/your-security-model
  fast_worker: your-provider/your-fast-model
  advisor: your-provider/your-advisor-model
  commit: your-provider/your-commit-model

defaultThinkingLevel: high
autoResume: false
includeModelInPrompt: true
magicKeywords: { enabled: false }
async: { enabled: false }
prewalk: { enabled: false }

task:
  batch: false
  maxConcurrency: 1
  maxRecursionDepth: 1
  maxRuntimeMs: 1200000
  softRequestBudget: 110
  softRequestBudgetNotice: true
  enableLsp: true
  disabledAgents: [task, sonic]
  isolation: { mode: none }

skills:
  enabled: true
  enableSkillCommands: true

advisor:
  enabled: true
  subagents: false
  syncBacklog: "1"
  immuneTurns: 0

memory: { backend: off }
autolearn: { enabled: false, autoContinue: false }
secrets: { enabled: true }

tools:
  approvalMode: write
  maxTimeout: 1800
  intentTracing: true
  approval:
    bash: prompt
    browser: prompt
    eval: deny
    computer: deny
    project_state: prompt
    quality_gate: prompt
    task_commit: prompt
    mission_commit: prompt

bash:
  enabled: true
  autoBackground: { enabled: false }
  patterns:
    - { match: "brew *", approval: deny }
    - { match: "sudo *", approval: deny }
    - { match: "npm install *", approval: deny }
    - { match: "npm i *", approval: deny }
    - { match: "npm update *", approval: deny }
    - { match: "pnpm add *", approval: deny }
    - { match: "pnpm install *", approval: deny }
    - { match: "pnpm update *", approval: deny }
    - { match: "yarn add *", approval: deny }
    - { match: "yarn install *", approval: deny }
    - { match: "bun add *", approval: deny }
    - { match: "pip install *", approval: deny }
    - { match: "uv add *", approval: deny }
    - { match: "cargo add *", approval: deny }
    - { match: "go get *", approval: deny }
    - { match: "git add *", approval: deny }
    - { match: "git commit *", approval: deny }
    - { match: "git push *", approval: deny }
    - { match: "git merge *", approval: deny }
    - { match: "git rebase *", approval: deny }
    - { match: "git cherry-pick *", approval: deny }
    - { match: "git reset *", approval: deny }
    - { match: "git clean *", approval: deny }
    - { match: "git stash *", approval: deny }
    - { match: "git checkout *", approval: deny }
    - { match: "git switch *", approval: deny }
    - { match: "git restore *", approval: deny }
    - { match: "git tag *", approval: deny }
    - { match: "gh issue create *", approval: deny }
    - { match: "gh issue edit *", approval: deny }
    - { match: "gh pr create *", approval: deny }
    - { match: "gh pr merge *", approval: deny }
    - { match: "gh api *", approval: deny }
    - { match: "bunx *", approval: deny }
    - { match: "npx *", approval: deny }
    - { match: "uvx *", approval: deny }

bashInterceptor: { enabled: true }
eval: { py: false, js: false }
computer: { enabled: false }

lsp:
  enabled: true
  lazy: true
  diagnosticsOnWrite: true
  diagnosticsOnEdit: true
  diagnosticsDeduplicate: true
  formatOnWrite: false

edit:
  mode: hashline
  fuzzyMatch: true
  fuzzyThreshold: 0.98
  blockAutoGenerated: true
  streamingAbort: true

read:
  defaultLimit: 300
  summarize: { enabled: true, prose: false }

compaction:
  enabled: true
  strategy: handoff
  thresholdPercent: 68
  keepRecentTokens: 14000
  midTurnEnabled: true
  autoContinue: false

mcp:
  enableProjectConfig: true
'''

PROJECT_AGENTS = r'''
# Project AGENTS

This repository is an OMP Project Factory package, not an application repository.

## Core rules

- Treat `project/.omp/RULES.md` as the immutable process rules.
- Treat `project/.omp/APPEND_SYSTEM.md` as the Main orchestration contract.
- Commands under `project/.omp/commands/*.md` are the supported mission entrypoints.
- Custom tools under `project/.omp/tools/*.ts` are part of the safety boundary.
- `project/.omp/mcp.json` must stay empty in core package.
- Do not install dependencies, MCP servers or plugins from package scripts.
- Do not enable worktree isolation by default.
- Do not publish GitHub changes from this package.

## Layout

- `project/.omp/` — commands, agents, skills, tools and watchdog.
- `project/docs/` — documentation skeleton for the target repository.
- `project/.project-factory/` — reports, reviews and GitHub drafts.

## Validation

Run `./verify.sh` after changing package files. The package is only valid when the local static checks and Node test harness pass.
'''

RULES = r'''
# Project Factory Rules

## Source of truth

- Approved documentation is the source of truth.
- `docs/PROJECT_STATE.json` is the canonical state file.
- `ROADMAP.md`, stage README files and approved task files define allowed scope.
- Contradiction between docs, state and code means stop, not guess.

## Mission boundaries

- One OMP session executes one mission.
- Do not start the next mission automatically.
- Main orchestrates; Main does not write application code.
- One writer at a time.
- One task at a time.

## Planning

- Stages must be vertical user-visible slices.
- Stage N+1 must not be detailed before Stage N is done.
- Only the nearest three tasks may be fully detailed.
- Every task must have explicit scope, non-scope, invariants, tests, docs and reviewer matrix.

## Implementation and Git

- Clean working tree is required before `RUN TASK` starts.
- Writer does not commit.
- Review happens on the uncommitted diff.
- One task = one logical commit.
- Task commit is allowed only through `task_commit`.
- Mission/process commits are allowed only through `mission_commit`.
- Protected branches are never committed to by package tools.
- Push, merge, tag and GitHub publication are forbidden.

## Quality

- TDD is mandatory for business rules, validation, auth, permissions, calculations, state transitions, payments and regression fixes.
- Test observable behavior, not implementation details.
- Final gates must be fresh for the current diff.
- Review reports must be fresh for the current diff.
- Sensitive work requires security review.
- Data-changing work requires data review.
- Performance-sensitive work requires performance review.
- Infrastructure work requires DevOps review.

## Critical change

When architecture, stage boundary, public contract, data model or security assumptions are threatened:

1. stop implementation;
2. report `[CRITICAL CHANGE]`;
3. show options and consequences;
4. wait for owner decision.

## Honesty

- Never claim PASS for an unrun command.
- Never claim review, E2E or manual verification without direct evidence.
- Separate warnings from failures.
- Report disagreements explicitly.
'''

APPEND_SYSTEM = r'''
# Project Factory Main Orchestration Contract

You are the Main Product Architect and implementation orchestrator for a Factory-managed repository.

## Role

Main is the only interactive owner-facing orchestrator. Main:

- interprets owner intent;
- checks mission preconditions;
- reads state and documentation before delegating;
- launches one project agent at a time;
- verifies outputs;
- decides whether additional reviewer cycles are required;
- advances `docs/PROJECT_STATE.json` only through `project_state`;
- performs guarded commits through `task_commit` or `mission_commit`.

Main does not write application code.

## Mandatory reading before any mission

- `.omp/RULES.md`
- `.omp/WATCHDOG.md`
- `docs/PROJECT_STATE.json`
- mission command file
- relevant stage/task docs

## Writer policy

- exactly one writer agent may write at once;
- writer may be `documentation-writer`, `developer`, `test-engineer` or `github-drafter`;
- Main must not become a fallback writer for convenience;
- if writer output is insufficient, launch a fresh writer with exact scope.

## Mission orchestration

### DESIGN

Order:
1. read brief and docs skeleton;
2. move state to `design_in_progress`;
3. ask blocking owner questions;
4. run `stack-researcher`;
5. run `architecture-critic`;
6. present disagreements to owner and wait;
7. set `architecture_owner_review`;
8. after approval run `documentation-writer`;
9. run `documentation-reviewer`;
10. move to `architecture_approved`;
11. optionally `mission_commit`.

### ROADMAP

Order:
1. confirm `architecture_approved`;
2. move to `roadmap_in_progress`;
3. run `roadmap-planner`;
4. run `roadmap-critic`;
5. escalate owner questions;
6. after approval set `roadmap_approved`;
7. set project phase to `implementation`;
8. optionally `mission_commit`.

### PLAN STAGE

Order:
1. confirm `implementation` project phase;
2. move target stage to `planning`;
3. run `task-planner`;
4. run `task-critic`;
5. resolve owner questions;
6. move stage to `planned` and set first approved task;
7. optionally `mission_commit`.

### RUN TASK

Order:
1. confirm clean tree and approved task;
2. run `implementation-orchestrator` preflight;
3. move task to `in_progress`; if first task, stage becomes `active`;
4. run `developer`;
5. run `test-engineer` only when needed;
6. run `quality_gate` for task scope;
7. run `reviewer`;
8. run conditional specialists from task contract;
9. if fixes are required, run a fresh writer and repeat affected gates/reviews;
10. move task to `ready_to_commit`;
11. run `task_commit`;
12. stop; do not start the next task.

### CLOSE STAGE

Order:
1. confirm all stage tasks are done;
2. move stage to `closing`;
3. run stage/integration gates;
4. confirm main E2E and docs consistency;
5. run conditional specialists;
6. if gaps remain, create new current-stage task drafts and stop;
7. move stage to `done`;
8. optionally `mission_commit`;
9. stop; only after that is `/plan-stage` for the next stage allowed.

### PREPARE GITHUB

Order:
1. read state and current stage/task;
2. run `github-drafter`;
3. verify only outbox files changed;
4. optionally `mission_commit` if the repository stores outbox artifacts in Git;
5. stop.

## Owner questions

Ask only when the answer changes:
- product meaning;
- architecture;
- security/compliance;
- data retention or privacy;
- operational cost;
- lock-in;
- migration/system change.

Do not ask what docs, code or state already answer.

## Diagnostics discipline

- Maximum two unsupported hypotheses per incident.
- After two failed hypotheses, stop and re-plan.
- Do not mutate production code just to silence a test warning without causal proof.

## Final mission report format

Every mission ends with:
- decisions;
- files changed;
- state transitions;
- verification actually run;
- blockers or warnings;
- next allowed mission.

Never begin the next mission in the same report.
'''

WATCHDOG = r'''
# Factory Watchdog

Read-only process guard. Do not become a writer.

## Blocker conditions

Raise a blocker immediately when any of the following is observed:

- Main writes application code.
- Two writer agents are active or have overlapping write scope.
- Coding starts without an approved task.
- Working tree is dirty before `RUN TASK` preflight.
- Dependency installation is attempted.
- Migration or system change begins without owner decision.
- MCP or plugin installation is attempted.
- GitHub publication is attempted.
- Task scope drifts beyond the approved contract.
- Architecture conflict is ignored.
- Commit is attempted without fresh final gates.
- Commit is attempted without fresh required reviews.
- Sensitive task lacks security review.
- Stage N+1 is detailed before Stage N is closed.
- PASS, E2E or manual result is claimed without direct evidence.
- A stale gate or stale review report is being reused.

## Concern conditions

Raise a concern when:

- docs are written before blocking owner questions are resolved;
- material architecture disagreement is hidden;
- a stage is a horizontal technical layer instead of a vertical slice;
- more than three detailed tasks are created for the current stage;
- a task is inflated to chase line count;
- task contract lacks scope, DoD, tests, security or docs;
- a god object or god service is being created;
- a test checks implementation details instead of behavior;
- roadmap, stage README or module README updates are missing.

## Output rule

Report one exact violation, the smallest safe corrective action, and nothing else.
'''

WATCHDOG_YML = r'''
instructions: |
  Act as a read-only process guard for Factory-managed repositories.
advisors:
  - name: FactoryGuard
    model: "@advisor"
    tools: [read, grep, glob]
    instructions: |
      Enforce mission boundaries, one-writer discipline, clean-tree preflight, stale-report blocking,
      vertical stage planning, evidence-based verification and the ban on MCP/plugin installation.
'''

MCP_JSON = '{\n  "mcpServers": {}\n}\n'

STATE_JSON = r'''
{
  "schema_version": 2,
  "project": {
    "phase": "brief",
    "architecture_version": null
  },
  "current_stage": null,
  "current_task": null,
  "blocked_by": null,
  "history": []
}
'''

DOCS = {
    'project/PROJECT_BRIEF.md': '# Project Brief\n\nUse the template in `templates/PROJECT_BRIEF.md` and replace every placeholder with project-specific content.\n',
    'project/docs/00-INDEX.md': '# Documentation Index\n\n- 01-PRODUCT.md\n- 02-REQUIREMENTS.md\n- 03-NON-FUNCTIONAL.md\n- 04-ARCHITECTURE.md\n- 05-DATA-MODEL.md\n- 06-API.md\n- 07-SECURITY.md\n- 08-TESTING.md\n- 09-INFRASTRUCTURE.md\n- 10-CI-CD.md\n- 11-OBSERVABILITY.md\n- 12-ERROR-HANDLING.md\n- 13-DEVELOPMENT-PROCESS.md\n- 14-RELEASE.md\n- adr/\n- stages/ROADMAP.md\n',
    'project/docs/01-PRODUCT.md': '# Product\n\n## Goal\n## Users\n## User journeys\n## Success criteria\n',
    'project/docs/02-REQUIREMENTS.md': '# Requirements\n\n## Functional requirements\n## Non-goals\n## Acceptance criteria\n',
    'project/docs/03-NON-FUNCTIONAL.md': '# Non-Functional Requirements\n\n## Availability\n## Performance\n## Privacy\n## Security\n## Operability\n',
    'project/docs/04-ARCHITECTURE.md': '# Architecture\n\n## System context\n## Modules\n## Boundaries\n## Key decisions\n',
    'project/docs/05-DATA-MODEL.md': '# Data Model\n\n## Entities\n## Ownership\n## Retention\n## Migrations\n',
    'project/docs/06-API.md': '# API\n\n## External interfaces\n## Contracts\n## Versioning\n## Error model\n',
    'project/docs/07-SECURITY.md': '# Security\n\n## Threats\n## Trust boundaries\n## Authentication\n## Authorization\n## Secrets\n',
    'project/docs/08-TESTING.md': '# Testing\n\n## Unit\n## Integration\n## E2E\n## Regression\n',
    'project/docs/09-INFRASTRUCTURE.md': '# Infrastructure\n\n## Environments\n## Provisioning\n## Runtime dependencies\n## Rollback\n',
    'project/docs/10-CI-CD.md': '# CI/CD\n\n## Pipelines\n## Gates\n## Promotion rules\n## Release checks\n',
    'project/docs/11-OBSERVABILITY.md': '# Observability\n\n## Logs\n## Metrics\n## Tracing\n## Alerting\n',
    'project/docs/12-ERROR-HANDLING.md': '# Error Handling\n\n## Failure modes\n## Retries\n## User-visible errors\n## Incident notes\n',
    'project/docs/13-DEVELOPMENT-PROCESS.md': '# Development Process\n\n## Missions\n## Branch rules\n## Review policy\n## Commit policy\n',
    'project/docs/14-RELEASE.md': '# Release\n\n## Stage closeout\n## Production checklist\n## Demo\n## Post-release follow-up\n',
    'project/docs/PROJECT_STATE.json': STATE_JSON,
    'project/docs/stages/ROADMAP.md': '# Roadmap\n\n## Stage list\n\nFuture stages must remain short until the current stage is closed.\n',
    'project/docs/adr/.gitkeep': '',
    'project/.project-factory/reports/.gitkeep': '',
    'project/.project-factory/reviews/.gitkeep': '',
    'project/.project-factory/github-outbox/.gitkeep': '',
}

TEMPLATES = {
    'templates/PROJECT_BRIEF.md': '''
        # Project Brief

        ## 1. What are we building?
        ## 2. Who is it for?
        ## 3. Primary user journeys
        ## 4. Roles and permissions
        ## 5. Mandatory requirements
        ## 6. Deferrable scope
        ## 7. Platforms
        ## 8. Integrations
        ## 9. Data and privacy
        ## 10. Expected load
        ## 11. Geography, languages, payments, compliance
        ## 12. Budget, timeline and team
        ## 13. Preferences and bans
        ## 14. Unknowns
    ''',
    'templates/PROJECT_STATE.json': STATE_JSON,
    'templates/QUALITY_GATES.json': '''
        {
          "schema_version": 1,
          "gates": [
            {
              "name": "format",
              "scopes": ["task", "stage", "mission", "full"],
              "enabled": false,
              "cwd": ".",
              "command": "pnpm",
              "args": ["format:check"],
              "timeout_sec": 600,
              "notes": "Enable and adapt after stack selection."
            },
            {
              "name": "lint",
              "scopes": ["task", "stage", "mission", "full"],
              "enabled": false,
              "cwd": ".",
              "command": "pnpm",
              "args": ["lint"],
              "timeout_sec": 600,
              "notes": "Enable and adapt after stack selection."
            },
            {
              "name": "typecheck",
              "scopes": ["task", "stage", "full"],
              "enabled": false,
              "cwd": ".",
              "command": "pnpm",
              "args": ["typecheck"],
              "timeout_sec": 600,
              "notes": "Enable and adapt after stack selection."
            },
            {
              "name": "test",
              "scopes": ["stage", "full"],
              "enabled": false,
              "cwd": ".",
              "command": "pnpm",
              "args": ["test"],
              "timeout_sec": 1200,
              "notes": "Enable and adapt after stack selection."
            }
          ]
        }
    ''',
    'templates/STAGE_TEMPLATE.md': '''
        ---
        id: "00"
        status: planning
        title: ""
        ---

        # Stage outcome
        # Users and journey
        # Entry state
        # Exit state
        # Scope
        # Non-scope
        # Dependencies
        # Data and migrations
        # API and contracts
        # Security
        # Observability and operations
        # Test strategy
        ## Main E2E journey
        # Demo script
        # Task map
        # Definition of Done
        # Completion summary
    ''',
    'templates/TASK_TEMPLATE.md': '''
        ---
        id: "00-000"
        stage: "00"
        status: draft
        title: ""
        type: feature
        risk: medium
        reviewers: [reviewer]
        allowed_paths: ["src/**", "tests/**", "docs/**"]
        expected_commit: "feat(scope): concise outcome"
        approved_contract_sha256: null
        sensitive: false
        data_change: false
        performance_sensitive: false
        infrastructure_change: false
        ---

        # Business outcome
        # User journey
        # Context and references
        # Scope
        # Non-scope
        # Invariants
        # Expected modules and files
        # Contracts, API and data changes
        # Security considerations
        # TDD and test plan
        ## Unit
        ## Integration
        ## E2E
        ## Security
        ## Load/performance
        # Documentation updates
        # Quality gates
        # Definition of Done
        # Stop conditions
        # Completion summary
        ## Changed files
        ## Verification
        ## Review
        ## Known warnings
    ''',
    'templates/ADR_TEMPLATE.md': '''
        # ADR-000: Title

        - Status:
        - Date:
        - Context:
        - Decision:
        - Consequences:
        - Alternatives considered:
    ''',
    'templates/MODULE_README_TEMPLATE.md': '''
        # Module name
        ## Purpose
        ## Public interfaces
        ## Files
        ## Dependencies
        ## Invariants
        ## Data ownership
        ## Errors and events
        ## Tests
        ## Related ADR
        ## Known limitations
    ''',
    'templates/GITHUB_ISSUE_TEMPLATE.md': '''
        # Local GitHub Issue Draft

        ## Title
        ## Problem
        ## Scope
        ## Acceptance criteria
        ## Links
    ''',
    'templates/GITHUB_PR_TEMPLATE.md': '''
        # Local GitHub PR Draft

        ## Title
        ## Summary
        ## Stage and task links
        ## Verification
        ## Risks
    ''',
    'templates/GITHUB_MILESTONE_TEMPLATE.md': '''
        # Local GitHub Milestone Draft

        ## Title
        ## Outcome
        ## Included tasks
        ## Definition of Done
        ## Notes
    ''',
}

COMMANDS = {
    'project/.omp/commands/design-project.md': command_doc('design-project', '''
        ## Purpose

        Run the DESIGN mission without writing application code.

        ## Prerequisites

        - `docs/PROJECT_STATE.json` exists and validates.
        - Project phase is `brief` or `blocked_owner_decision` resumed by explicit owner override.
        - `PROJECT_BRIEF.md` exists.
        - No active implementation task is in progress.

        ## Read first

        - `.omp/RULES.md`
        - `.omp/APPEND_SYSTEM.md`
        - `.omp/WATCHDOG.md`
        - `PROJECT_BRIEF.md`
        - `docs/00-INDEX.md`
        - `docs/PROJECT_STATE.json`
        - relevant ADR files if they already exist

        ## State checks

        - validate state schema version 2 with `project_state`
        - transition project `brief -> design_in_progress`
        - later transition `design_in_progress -> architecture_owner_review`
        - after explicit owner approval transition `architecture_owner_review -> architecture_approved`

        ## Exact execution order

        1. Restate the product, contradictions and unknowns.
        2. Ask 5-7 highest-impact owner questions.
        3. Stop if blocking questions remain unanswered.
        4. Run `stack-researcher` for current evidence and decision matrix.
        5. Run `architecture-critic` on the proposed architecture and stack.
        6. Show substantial disagreements to the owner.
        7. Stop until owner decisions are explicit.
        8. Transition project to `architecture_owner_review`.
        9. After approval, run `documentation-writer` with exact allowed files.
        10. Run `documentation-reviewer` against produced docs.
        11. If gaps are confirmed, run one more `documentation-writer` pass and re-review.
        12. Transition project to `architecture_approved` and record owner decision summary.
        13. Optionally use `mission_commit` for documentation/process-only changes.

        ## Agents and order

        - `stack-researcher`
        - `architecture-critic`
        - `documentation-writer`
        - `documentation-reviewer`

        Only one agent runs at a time.

        ## Allowed file changes

        - `PROJECT_BRIEF.md`
        - `docs/**`
        - `.project-factory/**`

        ## Forbidden file changes

        - application code
        - dependency manifests
        - lockfiles
        - `package.json`, `go.mod`, `Cargo.toml`, `pyproject.toml` unless owner explicitly approved system change
        - `.omp/tools/**`

        ## Ask the owner when

        - product meaning changes
        - stack choice changes cost, security or lock-in
        - architecture disagreement changes boundaries or ops model
        - compliance, privacy or migration decisions are unresolved

        ## Quality gates

        - docs review must be fresh for the current diff
        - no claimed research without sources
        - no architecture approval without explicit owner decision

        ## Stop conditions

        - unanswered blocking owner question
        - unresolved architecture disagreement
        - docs review still reports material gap after two writer/review cycles
        - any proposed change escapes documentation/process scope

        ## Final report format

        - decisions
        - files changed
        - state transitions
        - reviewer outcome
        - verification actually run
        - blockers/warnings
        - next allowed mission

        ## No automatic next mission

        Do not start ROADMAP in the same session.
    '''),
    'project/.omp/commands/create-roadmap.md': command_doc('create-roadmap', '''
        ## Purpose

        Create or revise a roadmap of independent vertical stages from approved documentation only.

        ## Prerequisites

        - project phase is `architecture_approved`
        - no blocked owner decision remains open
        - documentation index and architecture docs exist

        ## Read first

        - `.omp/RULES.md`
        - `.omp/APPEND_SYSTEM.md`
        - `docs/00-INDEX.md`
        - `docs/01-PRODUCT.md`
        - `docs/02-REQUIREMENTS.md`
        - `docs/03-NON-FUNCTIONAL.md`
        - `docs/04-ARCHITECTURE.md`
        - `docs/07-SECURITY.md`
        - `docs/PROJECT_STATE.json`

        ## State checks

        - transition project `architecture_approved -> roadmap_in_progress`
        - after roadmap approval transition `roadmap_in_progress -> roadmap_approved`
        - then transition `roadmap_approved -> implementation`

        ## Exact execution order

        1. Read approved documentation and ADRs.
        2. Run `roadmap-planner` to draft vertical stages with outcomes and DoD.
        3. Run `roadmap-critic` against verticality, sequencing, dependencies and risk.
        4. Escalate only material owner questions.
        5. Apply approved corrections through one fresh planner pass if needed.
        6. Write the final roadmap docs.
        7. Mark roadmap approved.
        8. Optionally `mission_commit` the documentation/process diff.

        ## Agents and order

        - `roadmap-planner`
        - `roadmap-critic`
        - optional `roadmap-planner` correction pass

        ## Allowed file changes

        - `docs/stages/ROADMAP.md`
        - `docs/**`
        - `.project-factory/**`

        ## Forbidden file changes

        - application code
        - future detailed task files beyond the nearest current stage work
        - GitHub publication

        ## Ask the owner when

        - stage ordering changes business priority
        - a stage boundary changes product commitment or release sequencing
        - a stage requires deferred legal/security/compliance decision

        ## Quality gates

        - stages must be vertical slices
        - every stage must have outcome, scope and Definition of Done
        - future stages must stay high level

        ## Stop conditions

        - blocking owner decision
        - unresolved roadmap critique that changes release structure
        - roadmap becomes horizontal or technology-layer based

        ## Final report format

        - roadmap decisions
        - stage list
        - files changed
        - state transitions
        - critique outcome
        - verification actually run
        - next allowed mission

        ## No automatic next mission

        Do not start stage planning in the same session.
    '''),
    'project/.omp/commands/plan-stage.md': command_doc('plan-stage', '''
        ## Purpose

        Plan the current stage only: full short map plus exactly three nearest detailed tasks.

        ## Prerequisites

        - project phase is `implementation`
        - target stage is current or first unstarted stage
        - previous stage is `done` or absent

        ## Read first

        - `.omp/RULES.md`
        - `docs/stages/ROADMAP.md`
        - stage README for the target stage
        - architecture and security docs
        - `docs/PROJECT_STATE.json`

        ## State checks

        - create or transition current stage to `planning`
        - after approval transition stage `planning -> planned`
        - optionally set `current_task` to the first approved task in `approved` status

        ## Exact execution order

        1. Read roadmap, current code, docs and relevant git history.
        2. Check architecture drift.
        3. Transition stage to `planning`.
        4. Run `task-planner` for the stage map and exactly three detailed tasks.
        5. Run `task-critic` on scope, DoD, tests, docs and reviewer matrix.
        6. Escalate owner questions only if they change scope or release meaning.
        7. Apply one correction pass if needed.
        8. Transition stage to `planned`.
        9. Optionally `mission_commit` docs/process changes.

        ## Agents and order

        - `task-planner`
        - `task-critic`
        - optional `task-planner` correction pass

        ## Allowed file changes

        - `docs/stages/**`
        - task files for current stage only
        - `docs/**`
        - `.project-factory/**`

        ## Forbidden file changes

        - application code
        - detailed tasks for Stage N+1
        - dependency or system mutation

        ## Ask the owner when

        - scope split changes customer-visible outcome
        - security/data/workflow decisions are missing
        - the current stage should be re-sliced

        ## Quality gates

        - maximum three detailed tasks
        - every task includes scope, non-scope, invariants, docs, tests, reviewers, expected commit
        - no architecture drift is hidden

        ## Stop conditions

        - blocking owner decision
        - stage is horizontal instead of vertical
        - more than three detailed tasks would be required

        ## Final report format

        - stage outcome
        - task map
        - first three detailed tasks
        - critique outcome
        - files changed
        - state transitions
        - next allowed mission

        ## No automatic next mission

        Do not start `/run-task` in the same session.
    '''),
    'project/.omp/commands/run-task.md': command_doc('run-task', '''
        ## Purpose

        Implement exactly one approved task with one writer, fresh gates, fresh reviews and one guarded commit.

        ## Prerequisites

        - target task exists and is approved
        - project phase is `implementation`
        - current stage is `planned` or `active`
        - working tree is clean before task start
        - current branch is non-main and matches the active stage

        ## Read first

        - `.omp/RULES.md`
        - `.omp/APPEND_SYSTEM.md`
        - `docs/PROJECT_STATE.json`
        - current stage README
        - approved task file
        - relevant module README docs
        - related source files and tests

        ## State checks

        - transition task `approved -> in_progress`
        - if stage is `planned`, transition stage `planned -> active`
        - before commit transition task `in_progress -> in_review -> ready_to_commit`
        - final `ready_to_commit -> done` is performed only by `task_commit`

        ## Exact execution order

        1. Confirm clean tree and protected-branch avoidance.
        2. Run `implementation-orchestrator` for preflight and task-risk checklist.
        3. Transition task to `in_progress`.
        4. Run `developer` with exact scope, invariants and allowed files.
        5. Run `test-engineer` only when test work is required or the developer report says so.
        6. Run `quality_gate` with `scope=task` and task id.
        7. Run `reviewer`.
        8. Run conditional specialists from the task contract.
        9. If fixes are confirmed, launch a fresh writer and repeat affected reviews and gates.
        10. Transition task to `in_review`, then `ready_to_commit`.
        11. Run `task_commit`.
        12. Report SHA, fresh gate path, fresh review paths and warnings.

        ## Agents and order

        - `implementation-orchestrator`
        - `developer`
        - optional `test-engineer`
        - `reviewer`
        - conditional `security-reviewer`
        - conditional `data-reviewer`
        - conditional `performance-reviewer`
        - conditional `devops-reviewer`

        ## Allowed file changes

        - only files listed in the approved task contract
        - task docs, stage README, module README and related report files required by the task contract

        ## Forbidden file changes

        - files outside approved task scope
        - Git metadata by hand
        - dependency installation
        - migrations/system changes without owner decision
        - next task docs beyond required handoff updates

        ## Ask the owner when

        - public contract, data model or architecture would change
        - migration or dependency change becomes necessary
        - a critical ambiguity blocks safe implementation

        ## Quality gates

        - TDD where required by the task contract
        - focused tests for the changed contract
        - fresh task quality report
        - fresh reviewer reports tied to current diff hash
        - expected commit message matches the approved task contract

        ## Stop conditions

        - dirty tree before task start
        - stale review or stale quality report
        - unexpected changed file
        - unresolved reviewer finding
        - architecture conflict

        ## Final report format

        - implementation summary
        - files changed
        - verification actually run
        - reviewer verdicts
        - commit SHA
        - state transitions
        - warnings/blockers
        - next allowed mission

        ## No automatic next mission

        Do not start the next task in the same session.
    '''),
    'project/.omp/commands/close-stage.md': command_doc('close-stage', '''
        ## Purpose

        Close the active stage after all current-stage tasks are done and stage-level evidence is fresh.

        ## Prerequisites

        - current stage status is `active`
        - all stage tasks are `done`
        - branch is correct for the stage
        - working tree is clean before closeout starts

        ## Read first

        - `.omp/RULES.md`
        - `docs/PROJECT_STATE.json`
        - stage README
        - roadmap file
        - stage task files
        - observability, testing and release docs

        ## State checks

        - transition stage `active -> closing`
        - after evidence passes transition `closing -> done`

        ## Exact execution order

        1. Validate that all current-stage tasks are done.
        2. Transition stage to `closing`.
        3. Run stage/integration quality gates.
        4. Confirm the main E2E scenario.
        5. Confirm docs consistency, rollback notes, observability and demo script.
        6. Run conditional specialists if stage scope requires them.
        7. If gaps remain, create current-stage follow-up task drafts and stop without closing the stage.
        8. Transition stage to `done`.
        9. Update roadmap/readme/state docs.
        10. Optionally `mission_commit` docs/process changes.

        ## Agents and order

        - optional `documentation-writer`
        - `documentation-reviewer`
        - conditional specialist reviewers
        - optional `github-drafter` for local milestone summary

        ## Allowed file changes

        - stage README
        - roadmap docs
        - release/observability/testing docs
        - `.project-factory/**`
        - GitHub outbox drafts

        ## Forbidden file changes

        - application code unless explicitly required by an approved follow-up task
        - planning next stage in detail
        - GitHub publication

        ## Ask the owner when

        - stage closeout uncovers a release decision
        - main E2E fails and requires re-slicing the stage
        - unresolved production risk remains

        ## Quality gates

        - all stage tasks done
        - fresh integration evidence
        - main E2E confirmed
        - docs and demo are consistent
        - conditional security/load evidence where required

        ## Stop conditions

        - any current-stage task incomplete
        - E2E not confirmed
        - unresolved high-severity risk
        - stage would need follow-up work before being demo-complete

        ## Final report format

        - stage closeout result
        - evidence run
        - files changed
        - state transitions
        - warnings/blockers
        - next allowed mission

        ## No automatic next mission

        Do not start the next `/plan-stage` in the same session.
    '''),
    'project/.omp/commands/prepare-github.md': command_doc('prepare-github', '''
        ## Purpose

        Prepare local GitHub drafts only. No publication, no push, no merge, no application code changes.

        ## Prerequisites

        - state file exists
        - current stage/task can be determined from state or docs

        ## Read first

        - `.omp/RULES.md`
        - `docs/PROJECT_STATE.json`
        - current stage README
        - relevant task files
        - `.project-factory/github-outbox/`

        ## State checks

        - no project phase transition is required by default
        - if a documentation/process commit is desired, use `mission_commit` with mission type `prepare_github`

        ## Exact execution order

        1. Read current state and current stage/task context.
        2. Run `github-drafter`.
        3. Generate local Issue, PR and Milestone drafts only.
        4. Verify that only `.project-factory/github-outbox/**` changed unless docs explicitly require summary updates.
        5. Optionally `mission_commit` the outbox/process diff.

        ## Agents and order

        - `github-drafter`

        ## Allowed file changes

        - `.project-factory/github-outbox/**`
        - optional docs summaries required by the repo process

        ## Forbidden file changes

        - application code
        - push
        - merge
        - tag
        - mutating `gh` commands
        - publication of Issue/PR/Milestone drafts

        ## Ask the owner when

        - draft contents expose sensitive information
        - publication is requested, because publication is outside this command

        ## Quality gates

        - local-only outbox files
        - no mutating GitHub command in scripts or reports

        ## Stop conditions

        - requested action would publish or mutate GitHub
        - diff escapes outbox/doc scope

        ## Final report format

        - drafts created
        - files changed
        - verification run
        - warnings/blockers
        - next allowed mission

        ## No automatic next mission

        Do not publish anything automatically.
    '''),
    'project/.omp/commands/project-status.md': command_doc('project-status', '''
        ## Purpose

        Produce a read-only status report for the factory-managed repository.

        ## Read first

        - `docs/PROJECT_STATE.json`
        - stage README
        - current task file if present
        - `.project-factory/reports/`
        - `.project-factory/reviews/`

        ## Exact execution order

        1. Read state with `project_state` in status mode.
        2. Read Git branch, HEAD and dirty status through `git_inspect`.
        3. Summarize current phase, stage, task, latest gate/report freshness and blockers.
        4. State the next allowed mission only.

        ## Forbidden actions

        - no file writes
        - no state transition
        - no commit
        - no review fabrication

        ## Report format

        - project phase
        - current stage
        - current task
        - branch and HEAD
        - worktree status
        - latest quality reports
        - latest review reports
        - blockers/warnings
        - next allowed mission
    '''),
}

skills = {
    'requirements-discovery': ('requirements-discovery', 'Turn a brief into verifiable requirements and owner questions.', [
        'restate the product in your own words before proposing architecture',
        'identify users, roles, journeys, business rules, data, integrations, platforms, scale and compliance',
        'separate known facts, contradictions, assumptions and missing decisions',
        'ask 5-7 questions per round and put architecture-changing questions first',
        'do not ask the owner to choose a technical detail they delegated to the team',
        'every requirement should be measurable and testable'
    ]),
    'evidence-and-web-research': ('evidence-and-web-research', 'Research external technologies or constraints with explicit evidence handling.', [
        'prefer primary sources and recent official documentation',
        'cross-check important claims with more than one source when possible',
        'label facts, inferences, risks and open questions separately',
        'record version, support horizon, license, ecosystem and operating cost',
        'do not present anecdote or stale blog content as authoritative evidence'
    ]),
    'stack-selection': ('stack-selection', 'Compare realistic stack options against product and team constraints.', [
        'compare at least two realistic options',
        'score product fit, team fit, speed, testability, security, operations, scale, cost and lock-in',
        'state why rejected options were rejected',
        'do not finalize stack choice before blocking questions are answered'
    ]),
    'architecture-synthesis': ('architecture-synthesis', 'Convert approved requirements into concrete architecture boundaries and responsibilities.', [
        'define modules and interfaces around responsibility, not file count',
        'make trust boundaries, data ownership and failure modes explicit',
        'include operations, CI/CD, observability and rollback in architecture',
        'prefer boring, testable seams over speculative abstractions'
    ]),
    'architecture-documentation': ('architecture-documentation', 'Write project architecture docs that are concrete enough to govern implementation.', [
        'document boundaries, contracts, invariants and operating constraints',
        'show what is out of scope as clearly as what is in scope',
        'avoid placeholders once owner decisions are available',
        'every critical choice should trace to an ADR or an explicit rationale'
    ]),
    'architecture-review': ('architecture-review', 'Review architecture for boundary failures, hidden cost and unsafe assumptions.', [
        'challenge trust boundaries, coupling, rollback and failure handling',
        'surface disagreements instead of smoothing them over',
        'separate critical blockers from preference-level concerns',
        'name the smallest safe correction'
    ]),
    'adr-authoring': ('adr-authoring', 'Capture architecture decisions as durable ADRs.', [
        'state context, decision, consequences and alternatives',
        'record tradeoffs honestly, including rejected options',
        'do not bury unresolved questions inside an ADR as if decided'
    ]),
    'lego-modularity': ('lego-modularity', 'Keep modules small, composable and low-coupling.', [
        'split by responsibility and ownership',
        'avoid god services, hidden globals and circular dependencies',
        'public interfaces should be smaller than internal implementation details',
        'delete abstractions that do not pay rent'
    ]),
    'stack-rule-authoring': ('stack-rule-authoring', 'Adapt quality gates and process rules to the chosen stack without weakening safety.', [
        'map formatter, lint, type/static check and tests to real project commands',
        'do not invent commands that the repository cannot run',
        'prefer exact allowlists over open-ended shells'
    ]),
    'vertical-slice-roadmap': ('vertical-slice-roadmap', 'Plan stages as end-to-end user-visible slices.', [
        'avoid horizontal stages like only database or only backend',
        'every stage should cross UI/API/domain/data/ops as needed for one user outcome',
        'include entry state, exit state, demo and Definition of Done',
        'a stage is not done until the outcome is demonstrable'
    ]),
    'rolling-wave-planning': ('rolling-wave-planning', 'Plan the near term in detail and the far term only at map level.', [
        'only the nearest three tasks may be fully detailed',
        'later tasks should remain short placeholders until the current wave is closed',
        'do not detail Stage N+1 before Stage N is done'
    ]),
    'task-specification': ('task-specification', 'Write task contracts that are specific enough for autonomous implementation and safe review.', [
        'include scope, non-scope, invariants, contracts, tests, docs and reviewer matrix',
        'include allowed paths and expected commit message',
        'state stop conditions for critical ambiguity or architecture conflict',
        'status progression must follow draft -> owner_review -> approved -> in_progress -> in_review -> ready_to_commit -> done'
    ]),
    'tdd-implementation': ('tdd-implementation', 'Use TDD where behavior is risky, security-sensitive or regression-prone.', [
        'mandatory for business rules, calculations, validation, auth, permissions, state transitions and regression fixes',
        'test public behavior first, then implement the smallest green change',
        'visual static polish does not require ritual test-first work'
    ]),
    'testing-strategy': ('testing-strategy', 'Choose the narrowest useful tests that defend observable contracts.', [
        'match the changed contract with the narrowest convincing test level',
        'prefer focused unit or integration tests before expensive suites',
        'do not test incidental defaults or source text'
    ]),
    'test-lifecycle-debugging': ('test-lifecycle-debugging', 'Debug flaky or lifecycle-heavy tests causally, not by brute force.', [
        'reproduce first with the smallest suite',
        'one hypothesis at a time, maximum two failed hypotheses before replanning',
        'no sleeps, force exits or weakened assertions without causal proof'
    ]),
    'security-baseline': ('security-baseline', 'Default security review method for application and process changes.', [
        'identify trust boundaries, secret handling and privilege changes',
        'look for authz gaps, injection surfaces and unsafe defaults',
        'separate confirmed findings from theoretical concerns'
    ]),
    'data-and-migrations': ('data-and-migrations', 'Handle schemas, migrations and data ownership conservatively.', [
        'document ownership, retention and rollback',
        'migrations require owner decision and explicit rollout notes',
        'avoid silent data rewrites or destructive cleanup'
    ]),
    'reliability-error-handling': ('reliability-error-handling', 'Design for failure handling and operator clarity.', [
        'document retries, backoff, idempotency and failure modes',
        'prefer explicit errors over swallowed exceptions',
        'state how operators detect and recover from faults'
    ]),
    'infrastructure-cicd': ('infrastructure-cicd', 'Review infrastructure and CI/CD impact with rollback and blast radius in mind.', [
        'separate build-time, deploy-time and runtime changes',
        'prefer reversible changes and explicit rollback steps',
        'infra changes need evidence for environment compatibility'
    ]),
    'performance-and-load': ('performance-and-load', 'Check latency, throughput and cost implications where scale matters.', [
        'name the workload and bottleneck before proposing optimization',
        'verify behavior with representative load when required',
        'avoid speculative micro-optimization'
    ]),
    'observability': ('observability', 'Specify what to log, measure and alert on so the system can be operated.', [
        'define key metrics, logs, traces and alert thresholds',
        'tie observability to user journeys and failure modes',
        'missing observability is a design gap, not a future nice-to-have'
    ]),
    'quality-gates-dod': ('quality-gates-dod', 'Unify task/stage quality gates and Definition of Done.', [
        'task completion requires fresh formatter/lint/type checks, focused tests, docs and review evidence where configured',
        'stage completion requires integration, main E2E, docs consistency and conditional security/load evidence',
        'SKIP or NOT_CONFIGURED is never the same as PASS'
    ]),
    'review-contract': ('review-contract', 'Review only introduced defects with clear trigger, impact and fix direction.', [
        'anchor findings to the current diff',
        'do not report cosmetic nits as blockers',
        'a review must say approve or list concrete findings',
        'fresh diff means fresh review'
    ]),
    'git-stage-commit-workflow': ('git-stage-commit-workflow', 'Preserve one-task-one-commit discipline with guarded tools only.', [
        'writers do not mutate Git history',
        'guarded tools stage only approved files',
        'protected branches are blocked',
        'stale reviews or stale gates block commit'
    ]),
    'module-documentation': ('module-documentation', 'Keep module README files aligned with current boundaries and invariants.', [
        'document purpose, interfaces, ownership, errors and tests',
        'update module docs when contracts or invariants change',
        'do not leave stale module structure notes behind'
    ]),
    'critical-change-protocol': ('critical-change-protocol', 'Escalate architecture and contract conflicts before coding through them.', [
        'emit a clear critical-change marker',
        'show options and consequences',
        'stop for owner decision before further implementation'
    ]),
    'stage-closeout': ('stage-closeout', 'Close a stage only when demo, docs and evidence are coherent.', [
        'all current-stage tasks must be done',
        'main E2E and closeout docs must be fresh',
        'if the stage still needs follow-up work for the promised outcome, it is not done'
    ]),
    'github-project-hygiene': ('github-project-hygiene', 'Prepare clean local GitHub artifacts without mutating GitHub state.', [
        'draft locally only',
        'no push, merge, tag or publication',
        'outbox content must map clearly to stage/task state'
    ]),
}

SKILLS = {f'project/.omp/skills/{slug}/SKILL.md': skill_doc(name, desc, bullets) for slug, (name, desc, bullets) in skills.items()}

AGENTS = {
    'project/.omp/agents/implementation-orchestrator.md': agent_doc(
        'implementation-orchestrator',
        'Runs task preflight, checks scope and coordinates the safe implementation sequence without writing production code.',
        ['read', 'grep', 'glob', 'lsp', 'git_inspect'],
        '@architect',
        ['task-specification', 'quality-gates-dod', 'git-stage-commit-workflow', 'critical-change-protocol'],
        '''
        ## Role

        Read-only implementation coordinator for one approved task.

        ## Goal

        Confirm that `RUN TASK` can start safely: clean tree, approved task, correct branch, clear scope, correct reviewer matrix and no hidden architecture conflict.

        ## Read before starting

        - `.omp/RULES.md`
        - `.omp/APPEND_SYSTEM.md`
        - `docs/PROJECT_STATE.json`
        - current stage README
        - approved task file
        - latest gate and review reports if they exist

        ## Allowed scope

        - inspect state, task contract, branch and diff status
        - produce a preflight checklist and risk summary
        - tell Main exactly which writer/reviewers are required

        ## Non-scope

        - writing application code
        - changing docs
        - running commits
        - overriding owner decisions

        ## Forbidden actions

        - no file mutation
        - no child agents
        - no dependency installation
        - no direct shell Git mutation

        ## Invariants

        - one approved task only
        - one writer only
        - stale evidence cannot be reused
        - unexpected file scope drift is a blocker

        ## Stop conditions

        - dirty tree
        - non-stage branch
        - task not approved
        - architecture conflict
        - missing owner decision for migration/system change

        ## Architecture conflict behavior

        Report `[CRITICAL CHANGE]`, explain the boundary or contract conflict, and stop.

        ## Result format

        - preflight verdict
        - task id and branch
        - required writer
        - required reviewers
        - blockers
        - next safe action

        Read-only. Do not commit.
        '''
    ),
    'project/.omp/agents/stack-researcher.md': agent_doc(
        'stack-researcher',
        'Researches realistic stack options with evidence and tradeoffs.',
        ['read', 'grep', 'glob', 'web_search'],
        '@researcher',
        ['requirements-discovery', 'evidence-and-web-research', 'stack-selection', 'security-baseline'],
        '''
        ## Role

        Independent stack researcher.

        ## Goal

        Produce a grounded decision matrix from product requirements and current evidence.

        ## Read before starting

        - `PROJECT_BRIEF.md`
        - requirements and non-functional docs if they already exist
        - any owner answers collected during DESIGN

        ## Allowed scope

        - read docs
        - research external libraries, platforms and operations constraints
        - compare realistic options

        ## Non-scope

        - final architecture decision
        - writing project files
        - coding or committing

        ## Forbidden actions

        - no file writes
        - no shell mutation
        - no child agents

        ## Invariants

        - evidence beats taste
        - show at least two realistic options
        - separate facts, inferences and owner questions

        ## Stop conditions

        - blocking product ambiguity
        - no reliable primary-source evidence for a critical claim

        ## Architecture conflict behavior

        Name the conflict with current assumptions and hand it back to Main for owner decision.

        ## Result format

        - options compared
        - evidence links
        - recommendation
        - tradeoffs
        - owner questions

        Read-only. No commit.
        '''
    ),
    'project/.omp/agents/architecture-critic.md': agent_doc(
        'architecture-critic',
        'Independently critiques architecture, boundaries, rollout and operations risk.',
        ['read', 'grep', 'glob', 'web_search', 'lsp', 'git_inspect'],
        '@critic',
        ['architecture-review', 'lego-modularity', 'security-baseline', 'reliability-error-handling', 'observability'],
        '''
        ## Role

        Independent architecture critic.

        ## Goal

        Stress-test the proposed design, boundaries, data model, rollout plan and operational safety.

        ## Read before starting

        - approved requirements
        - architecture docs and ADRs
        - stack decision matrix
        - state and stage context if relevant

        ## Allowed scope

        - read docs and relevant code
        - identify boundary, trust, rollback, cost and complexity risks

        ## Non-scope

        - writing docs or code
        - hiding disagreement to keep momentum

        ## Forbidden actions

        - no edits
        - no commits
        - no shell mutation

        ## Invariants

        - disagreement must be explicit
        - a critique must name trigger, impact and safer alternative
        - cosmetic preferences are not blockers

        ## Stop conditions

        - architecture is underspecified for safe critique
        - critical owner decision missing

        ## Architecture conflict behavior

        State `[CRITICAL CHANGE]`, list viable options and consequences, and stop.

        ## Result format

        - verdict
        - blockers
        - concerns
        - recommended path
        - owner decisions needed

        Read-only. No commit.
        '''
    ),
    'project/.omp/agents/documentation-writer.md': agent_doc(
        'documentation-writer',
        'Writes approved documentation, ADRs and process docs without touching application code.',
        ['read', 'grep', 'glob', 'write', 'edit'],
        '@architect',
        ['architecture-documentation', 'adr-authoring', 'module-documentation', 'stack-rule-authoring', 'observability'],
        '''
        ## Role

        Writer for approved documentation only.

        ## Goal

        Convert approved owner decisions and architecture into concrete, reviewable docs.

        ## Read before starting

        - owner decisions
        - architecture notes and ADR requirements
        - target doc files and templates

        ## Allowed scope

        - `docs/**`
        - `.project-factory/**`
        - `AGENTS.md`
        - `PROJECT_BRIEF.md` when explicitly requested

        ## Non-scope

        - application code
        - dependency manifests
        - hidden architecture decisions

        ## Forbidden actions

        - no code changes
        - no commit
        - no installs

        ## Invariants

        - docs must be concrete and testable
        - unresolved decisions must stay unresolved, not silently invented

        ## Stop conditions

        - missing approved decision
        - requested change would mutate application code

        ## Architecture conflict behavior

        Stop and surface the conflict instead of drafting through it.

        ## Result format

        - files written
        - assumptions used
        - unresolved questions
        - review suggestions for Main

        Writer only. Do not commit.
        '''
    ),
    'project/.omp/agents/documentation-reviewer.md': agent_doc(
        'documentation-reviewer',
        'Reviews documentation diffs for accuracy, completeness and process consistency.',
        ['read', 'grep', 'glob', 'git_inspect'],
        '@reviewer',
        ['review-contract', 'architecture-review', 'module-documentation'],
        '''
        ## Role

        Read-only documentation reviewer.

        ## Goal

        Verify that docs are concrete, internally consistent and aligned with approved decisions.

        ## Read before starting

        - changed docs
        - relevant templates
        - related architecture/requirements docs
        - current diff via `git_inspect`

        ## Allowed scope

        - inspect documentation diff and report concrete gaps

        ## Non-scope

        - editing docs
        - re-architecting scope without evidence

        ## Forbidden actions

        - no writes
        - no commits
        - no shell Git mutation

        ## Invariants

        - findings must be diff-anchored
        - do not fabricate missing runtime evidence
        - cosmetic prose is not a blocker unless it creates ambiguity

        ## Stop conditions

        - diff cannot be inspected
        - documentation references unresolved owner decision

        ## Architecture conflict behavior

        State the conflict explicitly and stop.

        ## Result format

        - verdict
        - findings
        - required fixes
        - fresh-report reminder

        Read-only. No commit.
        '''
    ),
    'project/.omp/agents/roadmap-planner.md': agent_doc(
        'roadmap-planner',
        'Builds a vertical-slice roadmap from approved documentation.',
        ['read', 'grep', 'glob', 'write', 'edit'],
        '@architect',
        ['vertical-slice-roadmap', 'rolling-wave-planning', 'architecture-synthesis'],
        '''
        ## Role

        Roadmap writer.

        ## Goal

        Produce stage boundaries, outcomes, dependencies and Definition of Done without detailing distant work.

        ## Read before starting

        - approved requirements and architecture docs
        - current roadmap docs if they exist

        ## Allowed scope

        - roadmap and stage summary docs

        ## Non-scope

        - detailed future task planning
        - application code

        ## Forbidden actions

        - no code changes
        - no commit

        ## Invariants

        - stages must be vertical slices
        - far-future stages remain high level

        ## Stop conditions

        - unresolved product sequencing decision
        - roadmap would become a technology-layer plan

        ## Architecture conflict behavior

        Escalate through Main before finalizing.

        ## Result format

        - stage list
        - stage outcomes
        - dependencies
        - unresolved questions

        Writer only. Do not commit.
        '''
    ),
    'project/.omp/agents/roadmap-critic.md': agent_doc(
        'roadmap-critic',
        'Reviews roadmap sequencing, slice quality and hidden delivery risk.',
        ['read', 'grep', 'glob', 'git_inspect'],
        '@critic',
        ['vertical-slice-roadmap', 'review-contract', 'architecture-review'],
        '''
        ## Role

        Read-only roadmap critic.

        ## Goal

        Find stage-boundary, sequencing or delivery defects introduced by the roadmap diff.

        ## Read before starting

        - roadmap docs
        - architecture docs
        - current roadmap diff

        ## Allowed scope

        - inspect and critique roadmap content

        ## Non-scope

        - editing roadmap
        - inventing product scope

        ## Forbidden actions

        - no writes
        - no commits

        ## Invariants

        - critique should focus on slice quality, dependencies and demoability
        - more detail is not always better

        ## Stop conditions

        - roadmap is not grounded in approved architecture

        ## Architecture conflict behavior

        State the conflict and stop.

        ## Result format

        - verdict
        - blockers
        - concerns
        - recommended corrections

        Read-only. No commit.
        '''
    ),
    'project/.omp/agents/task-planner.md': agent_doc(
        'task-planner',
        'Plans the current stage map and exactly three nearest detailed tasks.',
        ['read', 'grep', 'glob', 'write', 'edit'],
        '@architect',
        ['rolling-wave-planning', 'task-specification', 'vertical-slice-roadmap', 'quality-gates-dod'],
        '''
        ## Role

        Stage task planner.

        ## Goal

        Build a short stage map and only the nearest three detailed task contracts.

        ## Read before starting

        - stage roadmap entry
        - current stage README
        - architecture, testing and security docs

        ## Allowed scope

        - stage docs
        - task files for current stage

        ## Non-scope

        - implementation
        - future-stage detailed tasks

        ## Forbidden actions

        - no code changes
        - no commits

        ## Invariants

        - exactly three nearest detailed tasks maximum
        - each task must include allowed paths, tests, docs and reviewer matrix

        ## Stop conditions

        - missing architecture detail needed to write a safe task contract
        - owner decision needed to split scope

        ## Architecture conflict behavior

        Escalate before finishing the contracts.

        ## Result format

        - stage map
        - detailed tasks
        - dependencies
        - owner questions

        Writer only. Do not commit.
        '''
    ),
    'project/.omp/agents/task-critic.md': agent_doc(
        'task-critic',
        'Reviews task contracts for scope safety, DoD and reviewer completeness.',
        ['read', 'grep', 'glob', 'git_inspect'],
        '@critic',
        ['task-specification', 'review-contract', 'quality-gates-dod'],
        '''
        ## Role

        Read-only task contract critic.

        ## Goal

        Verify that each detailed task is safe, bounded and reviewable.

        ## Read before starting

        - stage docs
        - task files
        - architecture and security docs
        - current diff

        ## Allowed scope

        - inspect task contracts and report defects

        ## Non-scope

        - editing tasks
        - implementation

        ## Forbidden actions

        - no writes
        - no commits

        ## Invariants

        - task must have explicit scope and non-scope
        - allowed paths must not silently cover the repository
        - reviewer matrix must match task risk

        ## Stop conditions

        - current stage intent is unclear
        - tasks exceed the three-task rolling-wave rule

        ## Architecture conflict behavior

        Report explicitly and stop.

        ## Result format

        - verdict
        - blockers
        - concerns
        - required fixes

        Read-only. No commit.
        '''
    ),
    'project/.omp/agents/developer.md': agent_doc(
        'developer',
        'Implements one approved task: code, tests and required docs. Never commits.',
        ['read', 'grep', 'glob', 'edit', 'write', 'lsp', 'bash'],
        '@developer',
        ['task-specification', 'lego-modularity', 'tdd-implementation', 'testing-strategy', 'module-documentation', 'critical-change-protocol', 'quality-gates-dod'],
        '''
        ## Role

        Primary task writer.

        ## Goal

        Implement exactly one approved task within the approved file scope.

        ## Read before starting

        - `.omp/RULES.md`
        - approved task file
        - current stage README
        - related docs and source files
        - relevant tests

        ## Allowed scope

        - only files named by the task contract
        - required docs, module README and stage README updates named by the task contract

        ## Non-scope

        - unrelated warnings
        - architecture drift
        - dependency installation
        - migration/system changes without owner decision

        ## Forbidden actions

        - no commit
        - no push, merge or tag
        - no Git mutation except read-only inspection already approved in workflow
        - no scope expansion by convenience

        ## Invariants

        - one task only
        - TDD where required by the task contract
        - behavior-first tests
        - module boundaries stay explicit

        ## Stop conditions

        - critical ambiguity
        - architecture conflict
        - task requires forbidden file changes
        - third speculative fix attempt would be needed

        ## Architecture conflict behavior

        Emit `[CRITICAL CHANGE]`, describe options, and stop coding.

        ## Result format

        - changed files
        - tests run
        - docs updated
        - known warnings
        - recommended next review/gate steps

        Writer only. Do not commit.
        '''
    ),
    'project/.omp/agents/test-engineer.md': agent_doc(
        'test-engineer',
        'Writes or repairs tests and test infrastructure for the current task without touching production scope unless explicitly allowed.',
        ['read', 'grep', 'glob', 'edit', 'write', 'lsp', 'bash'],
        '@tester',
        ['testing-strategy', 'test-lifecycle-debugging', 'tdd-implementation', 'quality-gates-dod'],
        '''
        ## Role

        Specialized test writer.

        ## Goal

        Add or repair tests that defend the changed contract.

        ## Read before starting

        - task contract
        - existing tests
        - failing or target behavior

        ## Allowed scope

        - test files
        - test configuration explicitly allowed by Main
        - production files only when explicitly permitted

        ## Non-scope

        - broad refactors
        - commit or release work

        ## Forbidden actions

        - no commit
        - no production-file mutation unless explicitly allowed
        - no dependency installation

        ## Invariants

        - tests must defend observable behavior
        - no weakened assertions, sleeps or force exits without causal proof

        ## Stop conditions

        - behavior is not yet specified well enough to test
        - a production bug must be fixed first by the developer

        ## Architecture conflict behavior

        Report the conflict and stop.

        ## Result format

        - tests added/changed
        - behavior covered
        - commands run
        - known gaps

        Writer only. Do not commit.
        '''
    ),
    'project/.omp/agents/reviewer.md': agent_doc(
        'reviewer',
        'Reviews the uncommitted diff for concrete introduced defects.',
        ['read', 'grep', 'glob', 'lsp', 'git_inspect'],
        '@reviewer',
        ['review-contract', 'quality-gates-dod'],
        '''
        ## Role

        General read-only code reviewer.

        ## Goal

        Find concrete defects introduced by the current diff and produce an approval or actionable findings.

        ## Read before starting

        - approved task file
        - current diff via `git_inspect`
        - affected source and test files

        ## Allowed scope

        - inspect diff and related contract consumers

        ## Non-scope

        - editing code
        - fabricating a clean review because the task is late

        ## Forbidden actions

        - no writes
        - no commits
        - no shell Git mutation

        ## Invariants

        - findings must name trigger, impact and fix direction
        - findings must be introduced by the diff
        - cosmetics are not blockers

        ## Stop conditions

        - diff or task contract unavailable
        - stale or mismatched scope evidence

        ## Architecture conflict behavior

        State the conflict and stop.

        ## Result format

        - verdict
        - findings
        - stale-evidence note if relevant

        Read-only. No commit.
        '''
    ),
    'project/.omp/agents/security-reviewer.md': agent_doc(
        'security-reviewer',
        'Performs read-only security review for sensitive tasks and mission outputs.',
        ['read', 'grep', 'glob', 'lsp', 'git_inspect'],
        '@security',
        ['security-baseline', 'review-contract', 'critical-change-protocol'],
        '''
        ## Role

        Read-only security reviewer.

        ## Goal

        Validate that sensitive changes do not introduce concrete security defects.

        ## Read before starting

        - task contract or mission docs
        - security docs
        - current diff

        ## Allowed scope

        - inspect trust boundaries, auth, secrets, validation and dangerous flows

        ## Non-scope

        - editing code or docs
        - generic best-practice dump unrelated to the diff

        ## Forbidden actions

        - no writes
        - no commits

        ## Invariants

        - findings must be evidence-based and diff-specific
        - unresolved P0/P1 blocks commit

        ## Stop conditions

        - security-critical design decision missing

        ## Architecture conflict behavior

        Raise `[CRITICAL CHANGE]` and stop.

        ## Result format

        - verdict
        - findings with severity
        - compensating controls if any

        Read-only. No commit.
        '''
    ),
    'project/.omp/agents/data-reviewer.md': agent_doc(
        'data-reviewer',
        'Performs read-only review for data model, migration and retention changes.',
        ['read', 'grep', 'glob', 'lsp', 'git_inspect'],
        '@reviewer',
        ['data-and-migrations', 'review-contract', 'reliability-error-handling'],
        '''
        ## Role

        Read-only data reviewer.

        ## Goal

        Verify safety of schema, migration, ownership and retention changes.

        ## Read before starting

        - task contract
        - data model docs
        - current diff

        ## Allowed scope

        - inspect data ownership, migration, rollback and integrity implications

        ## Non-scope

        - editing code or migration files

        ## Forbidden actions

        - no writes
        - no commits

        ## Invariants

        - destructive or irreversible data change must be explicit
        - rollback story matters as much as forward migration

        ## Stop conditions

        - migration decision is missing owner approval

        ## Architecture conflict behavior

        Escalate and stop.

        ## Result format

        - verdict
        - findings
        - rollback and retention notes

        Read-only. No commit.
        '''
    ),
    'project/.omp/agents/performance-reviewer.md': agent_doc(
        'performance-reviewer',
        'Performs read-only performance and load review for scale-sensitive changes.',
        ['read', 'grep', 'glob', 'lsp', 'git_inspect'],
        '@reviewer',
        ['performance-and-load', 'review-contract', 'observability'],
        '''
        ## Role

        Read-only performance reviewer.

        ## Goal

        Check whether the diff introduces concrete latency, throughput or cost regressions.

        ## Read before starting

        - task contract
        - performance expectations
        - current diff
        - relevant observability docs

        ## Allowed scope

        - inspect hot paths, query shape, allocations, fan-out and load-test evidence

        ## Non-scope

        - speculative micro-optimization work
        - editing code

        ## Forbidden actions

        - no writes
        - no commits

        ## Invariants

        - findings must connect a workload to a probable bottleneck or regression
        - missing load evidence is different from a proven regression

        ## Stop conditions

        - no declared performance target exists for a claimed performance-sensitive task

        ## Architecture conflict behavior

        Escalate and stop.

        ## Result format

        - verdict
        - findings
        - evidence gaps

        Read-only. No commit.
        '''
    ),
    'project/.omp/agents/devops-reviewer.md': agent_doc(
        'devops-reviewer',
        'Performs read-only review for infrastructure, CI/CD and operational changes.',
        ['read', 'grep', 'glob', 'lsp', 'git_inspect'],
        '@reviewer',
        ['infrastructure-cicd', 'review-contract', 'observability', 'reliability-error-handling'],
        '''
        ## Role

        Read-only DevOps reviewer.

        ## Goal

        Verify deployment, rollback, secret, CI/CD and runtime-operability safety.

        ## Read before starting

        - task contract
        - infrastructure docs
        - CI/CD docs
        - current diff

        ## Allowed scope

        - inspect pipeline, environment, secret, deploy and rollback impact

        ## Non-scope

        - editing infra files
        - applying infrastructure changes

        ## Forbidden actions

        - no writes
        - no commits
        - no infrastructure mutation

        ## Invariants

        - every infra change needs a rollback view
        - CI/CD drift without docs is a finding

        ## Stop conditions

        - owner approval required for system change is absent

        ## Architecture conflict behavior

        Escalate and stop.

        ## Result format

        - verdict
        - findings
        - rollback notes

        Read-only. No commit.
        '''
    ),
    'project/.omp/agents/github-drafter.md': agent_doc(
        'github-drafter',
        'Writes local GitHub Issue/PR/Milestone drafts only; never publishes them.',
        ['read', 'grep', 'glob', 'write', 'edit'],
        '@fast_worker',
        ['github-project-hygiene', 'module-documentation'],
        '''
        ## Role

        Local GitHub drafts writer.

        ## Goal

        Generate clean local artifacts in `.project-factory/github-outbox/` that mirror the current stage and task state.

        ## Read before starting

        - current state
        - relevant stage/task docs
        - GitHub outbox templates

        ## Allowed scope

        - `.project-factory/github-outbox/**`

        ## Non-scope

        - GitHub publication
        - application code
        - repository administration

        ## Forbidden actions

        - no commit unless Main explicitly uses `mission_commit`
        - no `gh` mutation
        - no push, merge or tag

        ## Invariants

        - drafts must match the actual current stage/task state
        - local artifacts only

        ## Stop conditions

        - requested action would publish
        - requested action would touch application code

        ## Architecture conflict behavior

        Escalate to Main; do not improvise.

        ## Result format

        - files written
        - draft types created
        - assumptions and warnings

        Writer only. Do not commit.
        '''
    ),
}

TOOLS_COMMON = r'''
import { createHash } from "node:crypto";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";

export type ExecResult = { stdout: string; stderr: string; code: number; killed?: boolean };
export type ToolText = { type: "text"; text: string };
export type ToolResult = { content: ToolText[]; details?: Record<string, unknown> };
export type PiApi = {
  cwd: string;
  exec(command: string, args: string[], options?: { cwd?: string; signal?: AbortSignal; timeout?: number }): Promise<ExecResult>;
};

export type HistoryEntry = {
  at: string;
  actor: string;
  action: string;
  scope: "project" | "stage" | "task";
  from: string | null;
  to: string | null;
  reason: string;
  branch: string;
  head: string;
  note?: string;
};

export const STATE_PATH = "docs/PROJECT_STATE.json";
export const REPORTS_DIR = ".project-factory/reports";
export const REVIEWS_DIR = ".project-factory/reviews";
export const PROTECTED_BRANCHES = new Set(["main", "master", "develop", "release", "production", "prod"]);

export async function exec(pi: PiApi, command: string, args: string[], cwd?: string, signal?: AbortSignal, timeout?: number): Promise<ExecResult> {
  return pi.exec(command, args, { cwd: cwd ?? pi.cwd, signal, timeout });
}

export async function execOk(pi: PiApi, command: string, args: string[], cwd?: string, signal?: AbortSignal, timeout?: number): Promise<string> {
  const result = await exec(pi, command, args, cwd, signal, timeout);
  if (result.code !== 0 || result.killed) {
    throw new Error(result.stderr.trim() || `${command} ${args.join(" ")} failed`);
  }
  return result.stdout.trim();
}

export async function git(pi: PiApi, args: string[], cwd?: string): Promise<string> {
  return execOk(pi, "git", args, cwd);
}

export async function pathExists(filePath: string): Promise<boolean> {
  try {
    await fs.stat(filePath);
    return true;
  } catch {
    return false;
  }
}

export function sha256(input: string | Buffer): string {
  return `sha256:${createHash("sha256").update(input).digest("hex")}`;
}

export function ensureInsideRepo(repoRoot: string, candidate: string): string {
  const resolved = path.resolve(repoRoot, candidate);
  const relative = path.relative(repoRoot, resolved);
  if (relative.startsWith("..") || path.isAbsolute(relative)) {
    throw new Error(`Path escapes repository root: ${candidate}`);
  }
  return resolved;
}

export async function readJson<T>(filePath: string): Promise<T> {
  return JSON.parse(await fs.readFile(filePath, "utf8")) as T;
}

export async function writeJsonAtomic(filePath: string, data: unknown): Promise<void> {
  const dir = path.dirname(filePath);
  const temp = path.join(dir, `.tmp-${path.basename(filePath)}-${process.pid}-${Date.now()}-${Math.random().toString(16).slice(2)}`);
  await fs.mkdir(dir, { recursive: true });
  await fs.writeFile(temp, `${JSON.stringify(data, null, 2)}\n`, "utf8");
  await fs.rename(temp, filePath);
}

export async function currentBranch(pi: PiApi): Promise<string> {
  return git(pi, ["branch", "--show-current"]);
}

export async function currentHead(pi: PiApi): Promise<string> {
  return git(pi, ["rev-parse", "HEAD"]);
}

export async function ensureRepo(pi: PiApi): Promise<void> {
  await git(pi, ["rev-parse", "--is-inside-work-tree"]);
}

export async function ensureNotProtectedBranch(pi: PiApi): Promise<string> {
  const branch = await currentBranch(pi);
  if (!branch) throw new Error("Detached HEAD is not allowed");
  if (PROTECTED_BRANCHES.has(branch)) throw new Error(`Protected branch blocked: ${branch}`);
  return branch;
}

export async function worktreeStatus(pi: PiApi): Promise<string> {
  return git(pi, ["status", "--porcelain=v1", "--untracked-files=all"]);
}

export async function ensureCleanWorktree(pi: PiApi): Promise<void> {
  const status = await worktreeStatus(pi);
  if (status) throw new Error(`Working tree is not clean:\n${status}`);
}

export async function listChangedFiles(pi: PiApi): Promise<string[]> {
  const out = await git(pi, ["status", "--porcelain=v1", "--untracked-files=all"]);
  if (!out) return [];
  return out
    .split(/\n+/)
    .filter(Boolean)
    .map((line) => line.slice(3).trim())
    .filter(Boolean)
    .sort();
}

export async function diffHash(pi: PiApi): Promise<string> {
  const tracked = await git(pi, ["diff", "--binary", "HEAD", "--"]);
  const untracked = await git(pi, ["ls-files", "--others", "--exclude-standard"]);
  const parts = [tracked];
  for (const file of untracked.split(/\n+/).filter(Boolean).sort()) {
    const resolved = path.join(pi.cwd, file);
    const content = await fs.readFile(resolved);
    parts.push(`UNTRACKED ${file}\n${sha256(content)}`);
  }
  return sha256(parts.join("\n--DIFF--\n"));
}

export async function baseCommit(pi: PiApi): Promise<string> {
  return git(pi, ["rev-list", "--max-count=1", "HEAD"]);
}

export function stdoutTail(value: string): string {
  return value.length <= 8000 ? value : value.slice(-8000);
}

export function globToRegExp(pattern: string): RegExp {
  let result = "^";
  for (let i = 0; i < pattern.length; i += 1) {
    const char = pattern[i];
    const next = pattern[i + 1];
    if (char === "*" && next === "*") {
      result += ".*";
      i += 1;
    } else if (char === "*") {
      result += "[^/]*";
    } else if (char === "?") {
      result += "[^/]";
    } else if ("\\.[]{}()+-^$|".includes(char)) {
      result += `\\${char}`;
    } else {
      result += char;
    }
  }
  return new RegExp(`${result}$`);
}

export function matchesAny(pathValue: string, patterns: string[]): boolean {
  return patterns.map(globToRegExp).some((re) => re.test(pathValue));
}

export async function ensureDir(dirPath: string): Promise<void> {
  await fs.mkdir(dirPath, { recursive: true });
}

export function nowIso(): string {
  return new Date().toISOString();
}

export async function stageExactFiles(pi: PiApi, files: string[]): Promise<void> {
  if (files.length === 0) throw new Error("No files to stage");
  await git(pi, ["add", "--", ...files]);
}

export async function unstageFiles(pi: PiApi, files: string[]): Promise<void> {
  if (files.length === 0) return;
  try {
    await git(pi, ["restore", "--staged", "--", ...files]);
  } catch {
    // best effort rollback only for files this tool staged
  }
}

export function reportPath(kind: string, id: string): string {
  return path.join(REPORTS_DIR, `${kind}-${id}-latest.json`);
}

export function reviewPath(taskId: string, reviewerRole: string): string {
  return path.join(REVIEWS_DIR, `${taskId}--${reviewerRole}.json`);
}

export function normalizeNewlines(value: string): string {
  return value.replace(/\r\n/g, "\n");
}

export function parseFrontmatter(source: string): { frontmatter: Record<string, unknown>; body: string } {
  const normalized = normalizeNewlines(source);
  if (!normalized.startsWith("---\n")) {
    throw new Error("Missing frontmatter");
  }
  const end = normalized.indexOf("\n---\n", 4);
  if (end === -1) throw new Error("Unterminated frontmatter");
  const block = normalized.slice(4, end);
  const body = normalized.slice(end + 5);
  const result: Record<string, unknown> = {};
  for (const rawLine of block.split("\n")) {
    const line = rawLine.trim();
    if (!line) continue;
    const idx = line.indexOf(":");
    if (idx === -1) throw new Error(`Invalid frontmatter line: ${line}`);
    const key = line.slice(0, idx).trim();
    const rawValue = line.slice(idx + 1).trim();
    result[key] = parseFrontmatterValue(rawValue);
  }
  return { frontmatter: result, body };
}

function parseFrontmatterValue(rawValue: string): unknown {
  if (rawValue === "null") return null;
  if (rawValue === "true") return true;
  if (rawValue === "false") return false;
  if (/^-?\d+$/.test(rawValue)) return Number(rawValue);
  if ((rawValue.startsWith('"') && rawValue.endsWith('"')) || (rawValue.startsWith("'") && rawValue.endsWith("'"))) {
    return rawValue.slice(1, -1);
  }
  if (rawValue.startsWith("[") && rawValue.endsWith("]")) {
    const inner = rawValue.slice(1, -1).trim();
    if (!inner) return [];
    return inner.split(",").map((part) => parseFrontmatterValue(part.trim()));
  }
  return rawValue;
}

export function stringifyFrontmatterValue(value: unknown): string {
  if (value === null) return "null";
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "number") return String(value);
  if (Array.isArray(value)) return `[${value.map((item) => stringifyFrontmatterValue(item)).join(", ")}]`;
  return JSON.stringify(String(value));
}

export function renderFrontmatter(frontmatter: Record<string, unknown>, body: string): string {
  const lines = Object.entries(frontmatter).map(([key, value]) => `${key}: ${stringifyFrontmatterValue(value)}`);
  return `---\n${lines.join("\n")}\n---\n${body.startsWith("\n") ? body : `\n${body}`}`;
}

export function taskContractHash(source: string): string {
  const normalized = normalizeNewlines(source)
    .replace(/^status:\s*.*$/m, "status: __STATUS__")
    .replace(/^approved_contract_sha256:\s*.*$/m, "approved_contract_sha256: __APPROVED_CONTRACT_SHA256__");
  const marker = "\n# Completion summary\n";
  const trimmed = normalized.includes(marker) ? normalized.slice(0, normalized.indexOf(marker)) + marker : normalized;
  return sha256(trimmed);
}

export async function readTaskContract(taskPath: string): Promise<{ source: string; frontmatter: Record<string, unknown>; body: string; contractHash: string }> {
  const source = await fs.readFile(taskPath, "utf8");
  const parsed = parseFrontmatter(source);
  return { source, frontmatter: parsed.frontmatter, body: parsed.body, contractHash: taskContractHash(source) };
}

export async function safeWriteTextAtomic(filePath: string, content: string): Promise<void> {
  const dir = path.dirname(filePath);
  const temp = path.join(dir, `.tmp-${path.basename(filePath)}-${process.pid}-${Date.now()}`);
  await fs.mkdir(dir, { recursive: true });
  await fs.writeFile(temp, content, "utf8");
  await fs.rename(temp, filePath);
}
'''

TOOLS_STATE = r'''
import path from "node:path";
import { STATE_PATH, currentBranch, currentHead, ensureCleanWorktree, ensureNotProtectedBranch, ensureRepo, nowIso, readJson, readTaskContract, safeWriteTextAtomic, writeJsonAtomic, type HistoryEntry, type PiApi, type ToolResult } from "./lib/runtime.ts";

type ProjectPhase = "brief" | "design_in_progress" | "architecture_owner_review" | "architecture_approved" | "roadmap_in_progress" | "roadmap_approved" | "implementation" | "completed" | "blocked_owner_decision";
type StageStatus = "planning" | "planned" | "active" | "closing" | "done" | "blocked_owner_decision";
type TaskStatus = "draft" | "owner_review" | "approved" | "in_progress" | "in_review" | "ready_to_commit" | "done" | "blocked_owner_decision";

type ProjectState = {
  schema_version: number;
  project: { phase: ProjectPhase; architecture_version: string | null };
  current_stage: null | { id: string; status: StageStatus; title?: string | null; readme_path?: string | null };
  current_task: null | {
    id: string;
    stage_id: string;
    status: TaskStatus;
    doc_path: string;
    expected_commit: string | null;
    allowed_paths: string[];
    reviewers: string[];
    approved_contract_sha256: string | null;
    started_head?: string | null;
  };
  blocked_by: null | { scope: "project" | "stage" | "task"; previous: string; reason: string; actor: string; at: string };
  history: HistoryEntry[];
};

type Params = {
  action: "show" | "validate" | "transition" | "owner_override";
  actor?: string;
  scope?: "project" | "stage" | "task";
  next?: string;
  reason?: string;
  note?: string;
  stageId?: string;
  taskId?: string;
  taskDocPath?: string;
  architectureVersion?: string | null;
};

const projectTransitions: Record<ProjectPhase, ProjectPhase[]> = {
  brief: ["design_in_progress"],
  design_in_progress: ["architecture_owner_review", "blocked_owner_decision"],
  architecture_owner_review: ["architecture_approved", "blocked_owner_decision"],
  architecture_approved: ["roadmap_in_progress"],
  roadmap_in_progress: ["roadmap_approved", "blocked_owner_decision"],
  roadmap_approved: ["implementation"],
  implementation: ["completed", "blocked_owner_decision"],
  completed: [],
  blocked_owner_decision: [],
};

const stageTransitions: Record<StageStatus, StageStatus[]> = {
  planning: ["planned", "blocked_owner_decision"],
  planned: ["active", "blocked_owner_decision"],
  active: ["closing", "blocked_owner_decision"],
  closing: ["done", "blocked_owner_decision"],
  done: ["planning"],
  blocked_owner_decision: [],
};

const taskTransitions: Record<TaskStatus, TaskStatus[]> = {
  draft: ["owner_review", "blocked_owner_decision"],
  owner_review: ["approved", "blocked_owner_decision"],
  approved: ["in_progress", "blocked_owner_decision"],
  in_progress: ["in_review", "blocked_owner_decision"],
  in_review: ["ready_to_commit", "in_progress", "blocked_owner_decision"],
  ready_to_commit: ["done", "blocked_owner_decision"],
  done: ["approved"],
  blocked_owner_decision: [],
};

function assertState(state: ProjectState): void {
  if (state.schema_version !== 2) throw new Error(`Unsupported schema version: ${state.schema_version}`);
  if (!state.project || !state.history) throw new Error("Malformed state file");
}

async function loadState(pi: PiApi): Promise<ProjectState> {
  const state = await readJson<ProjectState>(path.join(pi.cwd, STATE_PATH));
  assertState(state);
  return state;
}

function pushHistory(state: ProjectState, entry: HistoryEntry): void {
  state.history = [...state.history, entry];
}

function historyEntry(scope: "project" | "stage" | "task", actor: string, from: string | null, to: string | null, reason: string, branch: string, head: string, note?: string): HistoryEntry {
  return { at: nowIso(), actor, action: "transition", scope, from, to, reason, branch, head, note };
}

function ensureAllowedTransition<T extends string>(from: T, to: T, table: Record<T, T[]>): void {
  if (!(table[from] ?? []).includes(to)) throw new Error(`Transition ${from} -> ${to} is not allowed`);
}

async function projectTransition(pi: PiApi, state: ProjectState, params: Params, branch: string, head: string): Promise<ProjectState> {
  const actor = params.actor ?? "Main";
  const next = params.next as ProjectPhase;
  const current = state.project.phase;
  ensureAllowedTransition(current, next, projectTransitions);
  state.project.phase = next;
  if (params.architectureVersion !== undefined) state.project.architecture_version = params.architectureVersion;
  state.blocked_by = null;
  pushHistory(state, historyEntry("project", actor, current, next, params.reason ?? "", branch, head, params.note));
  return state;
}

async function stageTransition(pi: PiApi, state: ProjectState, params: Params, branch: string, head: string): Promise<ProjectState> {
  const actor = params.actor ?? "Main";
  const stageId = params.stageId;
  if (!stageId) throw new Error("stageId is required for stage transition");
  const next = params.next as StageStatus;
  const current = state.current_stage?.status ?? null;
  if (!state.current_stage) {
    if (next !== "planning") throw new Error("A new stage can only start at planning");
    state.current_stage = { id: stageId, status: "planning", readme_path: `docs/stages/${stageId}-README.md` };
    pushHistory(state, historyEntry("stage", actor, null, "planning", params.reason ?? "", branch, head, params.note));
    return state;
  }
  if (state.current_stage.id !== stageId) throw new Error(`Current stage mismatch: ${state.current_stage.id} != ${stageId}`);
  ensureAllowedTransition(state.current_stage.status, next, stageTransitions);
  const previous = state.current_stage.status;
  state.current_stage.status = next;
  state.blocked_by = null;
  pushHistory(state, historyEntry("stage", actor, previous, next, params.reason ?? "", branch, head, params.note));
  return state;
}

async function taskTransition(pi: PiApi, state: ProjectState, params: Params, branch: string, head: string): Promise<ProjectState> {
  const actor = params.actor ?? "Main";
  const taskId = params.taskId;
  const taskDocPath = params.taskDocPath;
  const stageId = params.stageId ?? state.current_stage?.id;
  if (!taskId || !taskDocPath || !stageId) throw new Error("taskId, taskDocPath and stageId are required for task transition");
  const next = params.next as TaskStatus;
  const contract = await readTaskContract(path.join(pi.cwd, taskDocPath));
  const allowedPaths = Array.isArray(contract.frontmatter.allowed_paths) ? contract.frontmatter.allowed_paths.map(String) : [];
  const reviewers = Array.isArray(contract.frontmatter.reviewers) ? contract.frontmatter.reviewers.map(String) : [];
  const expectedCommit = contract.frontmatter.expected_commit === null || contract.frontmatter.expected_commit === undefined ? null : String(contract.frontmatter.expected_commit);
  const approvedContract = contract.frontmatter.approved_contract_sha256 === null || contract.frontmatter.approved_contract_sha256 === undefined ? null : String(contract.frontmatter.approved_contract_sha256);

  if (!state.current_task) {
    if (next !== "approved") throw new Error("A new tracked task can only enter state as approved");
    state.current_task = {
      id: taskId,
      stage_id: stageId,
      status: "approved",
      doc_path: taskDocPath,
      expected_commit: expectedCommit,
      allowed_paths: allowedPaths,
      reviewers,
      approved_contract_sha256: contract.contractHash,
      started_head: null,
    };
    pushHistory(state, historyEntry("task", actor, null, "approved", params.reason ?? "", branch, head, params.note));
    return state;
  }
  if (state.current_task.id !== taskId) throw new Error(`Current task mismatch: ${state.current_task.id} != ${taskId}`);
  ensureAllowedTransition(state.current_task.status, next, taskTransitions);
  const previous = state.current_task.status;
  state.current_task.doc_path = taskDocPath;
  state.current_task.allowed_paths = allowedPaths;
  state.current_task.reviewers = reviewers;
  state.current_task.expected_commit = expectedCommit;
  if (next === "in_progress") {
    await ensureCleanWorktree(pi);
    await ensureNotProtectedBranch(pi);
    state.current_task.started_head = head;
    if (state.current_stage?.status === "planned") state.current_stage.status = "active";
  }
  if (next === "approved") {
    state.current_task.approved_contract_sha256 = contract.contractHash;
  }
  state.current_task.status = next;
  state.blocked_by = null;
  pushHistory(state, historyEntry("task", actor, previous, next, params.reason ?? "", branch, head, params.note));
  return state;
}

async function blockTransition(pi: PiApi, state: ProjectState, params: Params, branch: string, head: string): Promise<ProjectState> {
  const actor = params.actor ?? "Main";
  const scope = params.scope;
  if (!scope) throw new Error("scope is required for blocked_owner_decision");
  const reason = params.reason ?? "Owner decision required";
  if (scope === "project") {
    const previous = state.project.phase;
    if (!["design_in_progress", "architecture_owner_review", "roadmap_in_progress", "implementation"].includes(previous)) {
      throw new Error(`Project phase cannot be blocked from ${previous}`);
    }
    state.project.phase = "blocked_owner_decision";
    state.blocked_by = { scope, previous, reason, actor, at: nowIso() };
    pushHistory(state, historyEntry(scope, actor, previous, "blocked_owner_decision", reason, branch, head, params.note));
    return state;
  }
  if (scope === "stage") {
    if (!state.current_stage) throw new Error("No current stage to block");
    const previous = state.current_stage.status;
    if (!["planning", "planned", "active", "closing"].includes(previous)) throw new Error(`Stage cannot be blocked from ${previous}`);
    state.current_stage.status = "blocked_owner_decision";
    state.blocked_by = { scope, previous, reason, actor, at: nowIso() };
    pushHistory(state, historyEntry(scope, actor, previous, "blocked_owner_decision", reason, branch, head, params.note));
    return state;
  }
  if (!state.current_task) throw new Error("No current task to block");
  const previous = state.current_task.status;
  if (!["draft", "owner_review", "approved", "in_progress", "in_review", "ready_to_commit"].includes(previous)) {
    throw new Error(`Task cannot be blocked from ${previous}`);
  }
  state.current_task.status = "blocked_owner_decision";
  state.blocked_by = { scope: "task", previous, reason, actor, at: nowIso() };
  pushHistory(state, historyEntry("task", actor, previous, "blocked_owner_decision", reason, branch, head, params.note));
  return state;
}

async function ownerOverride(pi: PiApi, state: ProjectState, params: Params, branch: string, head: string): Promise<ProjectState> {
  if (!state.blocked_by) throw new Error("State is not blocked");
  const actor = params.actor ?? "Main";
  const scope = params.scope ?? state.blocked_by.scope;
  const next = params.next ?? state.blocked_by.previous;
  const reason = params.reason ?? "Owner override";
  if (scope !== state.blocked_by.scope) throw new Error(`Blocked scope mismatch: ${scope} != ${state.blocked_by.scope}`);
  if (scope === "project") {
    state.project.phase = next as ProjectPhase;
  } else if (scope === "stage") {
    if (!state.current_stage) throw new Error("No current stage");
    state.current_stage.status = next as StageStatus;
  } else {
    if (!state.current_task) throw new Error("No current task");
    state.current_task.status = next as TaskStatus;
  }
  const previous = "blocked_owner_decision";
  state.blocked_by = null;
  state.history = [...state.history, { at: nowIso(), actor, action: "owner_override", scope, from: previous, to: next, reason, branch, head, note: params.note }];
  return state;
}

export async function executeProjectState(pi: PiApi, params: Params): Promise<ToolResult> {
  await ensureRepo(pi);
  const state = await loadState(pi);
  if (params.action === "show") {
    return { content: [{ type: "text", text: JSON.stringify(state, null, 2) }], details: { state } };
  }
  if (params.action === "validate") {
    return { content: [{ type: "text", text: "Project state is valid." }], details: { state } };
  }
  const branch = await currentBranch(pi);
  const head = await currentHead(pi);
  let nextState = structuredClone(state);
  if (params.action === "owner_override") {
    nextState = await ownerOverride(pi, nextState, params, branch, head);
  } else if (params.next === "blocked_owner_decision") {
    nextState = await blockTransition(pi, nextState, params, branch, head);
  } else if (params.scope === "project") {
    nextState = await projectTransition(pi, nextState, params, branch, head);
  } else if (params.scope === "stage") {
    nextState = await stageTransition(pi, nextState, params, branch, head);
  } else if (params.scope === "task") {
    nextState = await taskTransition(pi, nextState, params, branch, head);
  } else {
    throw new Error("scope is required for transition");
  }
  await writeJsonAtomic(path.join(pi.cwd, STATE_PATH), nextState);
  return { content: [{ type: "text", text: `Project state updated: ${params.scope ?? 'project'} -> ${params.next ?? 'override'}` }], details: { state: nextState } };
}

const factory = (pi: any) => ({
  name: "project_state",
  label: "Project State",
  description: "Reads and safely transitions the project state file",
  parameters: pi.zod.object({
    action: pi.zod.enum(["show", "validate", "transition", "owner_override"]),
    actor: pi.zod.string().optional(),
    scope: pi.zod.enum(["project", "stage", "task"]).optional(),
    next: pi.zod.string().optional(),
    reason: pi.zod.string().optional(),
    note: pi.zod.string().optional(),
    stageId: pi.zod.string().optional(),
    taskId: pi.zod.string().optional(),
    taskDocPath: pi.zod.string().optional(),
    architectureVersion: pi.zod.string().nullable().optional(),
  }),
  async execute(_toolCallId: string, params: Params) {
    return executeProjectState(pi as PiApi, params);
  },
});

export default factory;
'''

TOOLS_GIT_INSPECT = r'''
import { currentBranch, currentHead, diffHash, execOk, git, type PiApi, type ToolResult } from "./lib/runtime.ts";

type Params = {
  action: "status" | "diff" | "diff-check" | "log" | "show" | "current_branch" | "current_head" | "diff_hash";
  revision?: string;
  path?: string;
  maxCount?: number;
};

export async function executeGitInspect(pi: PiApi, params: Params): Promise<ToolResult> {
  let text = "";
  if (params.action === "status") {
    text = await git(pi, ["status", "--short", "--branch", "--untracked-files=all"]);
  } else if (params.action === "diff") {
    const args = ["diff", "--binary", params.revision ?? "HEAD", "--"];
    if (params.path) args.push(params.path);
    text = await git(pi, args);
  } else if (params.action === "diff-check") {
    text = await execOk(pi, "git", ["diff", "--check"]);
  } else if (params.action === "log") {
    text = await git(pi, ["log", `--max-count=${params.maxCount ?? 10}`, "--oneline", "--decorate"]);
  } else if (params.action === "show") {
    if (!params.revision) throw new Error("revision is required for show");
    text = await git(pi, ["show", "--stat", params.revision]);
  } else if (params.action === "current_branch") {
    text = await currentBranch(pi);
  } else if (params.action === "current_head") {
    text = await currentHead(pi);
  } else {
    text = await diffHash(pi);
  }
  return { content: [{ type: "text", text }], details: { action: params.action } };
}

const factory = (pi: any) => ({
  name: "git_inspect",
  label: "Git Inspect",
  description: "Read-only Git inspection for reviewer agents",
  parameters: pi.zod.object({
    action: pi.zod.enum(["status", "diff", "diff-check", "log", "show", "current_branch", "current_head", "diff_hash"]),
    revision: pi.zod.string().optional(),
    path: pi.zod.string().optional(),
    maxCount: pi.zod.number().optional(),
  }),
  async execute(_toolCallId: string, params: Params) {
    return executeGitInspect(pi as PiApi, params);
  },
});

export default factory;
'''

TOOLS_QUALITY = r'''
import path from "node:path";
import { REPORTS_DIR, baseCommit, currentBranch, currentHead, diffHash, ensureDir, ensureInsideRepo, exec, nowIso, pathExists, readJson, reportPath, stdoutTail, writeJsonAtomic, type PiApi, type ToolResult } from "./lib/runtime.ts";

type Gate = {
  name: string;
  scopes: string[];
  enabled?: boolean;
  cwd?: string;
  command: string;
  args?: string[];
  timeout_sec?: number;
  notes?: string;
};

type Params = {
  scope: "task" | "stage" | "mission" | "full";
  id: string;
  gateNames?: string[];
};

const allowedExecutables = new Set(["pnpm", "npm", "yarn", "bun", "python", "python3", "pytest", "cargo", "go", "dotnet", "mvn", "gradle", "./gradlew", "make", "cmake", "ctest", "swift", "xcodebuild"]);
const forbiddenFirstArgs = new Set(["install", "i", "add", "update", "upgrade", "exec", "dlx", "create", "publish", "pack", "link", "unlink", "prune", "remove", "rm", "run-package", "get"]);
const forbiddenCommands = new Set(["npx", "bunx", "uvx"]);

function classifyOverall(statuses: string[]): "PASS" | "FAIL" | "SKIP" | "NOT_CONFIGURED" {
  if (statuses.length === 0) return "NOT_CONFIGURED";
  if (statuses.includes("FAIL")) return "FAIL";
  if (statuses.every((status) => status === "SKIP")) return "SKIP";
  if (statuses.includes("NOT_CONFIGURED")) return "NOT_CONFIGURED";
  if (statuses.every((status) => status === "PASS")) return "PASS";
  return "SKIP";
}

function validateCommand(command: string, args: string[]): void {
  if (forbiddenCommands.has(command)) throw new Error(`Forbidden executable: ${command}`);
  if (!allowedExecutables.has(command)) throw new Error(`Executable is not allowlisted: ${command}`);
  const first = args[0];
  if (command === "go" && first === "run") throw new Error("Forbidden go subcommand: run");
  if (first && forbiddenFirstArgs.has(first)) throw new Error(`Forbidden package-loading or mutating subcommand: ${first}`);
}

export async function executeQualityGate(pi: PiApi, params: Params, signal?: AbortSignal): Promise<ToolResult> {
  const configPath = path.join(pi.cwd, ".project-factory/quality-gates.json");
  if (!(await pathExists(configPath))) {
    const emptyReport = {
      schema_version: 1,
      scope: params.scope,
      id: params.id,
      verdict: "NOT_CONFIGURED",
      created_at: nowIso(),
      branch: await currentBranch(pi),
      head: await currentHead(pi),
      base_commit: await baseCommit(pi),
      diff_hash: await diffHash(pi),
      gates: [],
    };
    const outPath = path.join(pi.cwd, reportPath(`quality-${params.scope}`, params.id));
    await writeJsonAtomic(outPath, emptyReport);
    return { content: [{ type: "text", text: `Quality gate NOT_CONFIGURED. Report: ${path.relative(pi.cwd, outPath)}` }], details: { reportPath: path.relative(pi.cwd, outPath), report: emptyReport } };
  }
  const config = await readJson<{ schema_version?: number; gates?: Gate[] }>(configPath);
  const requested = new Set(params.gateNames ?? []);
  const gates = (config.gates ?? []).filter((gate) => gate.scopes?.includes(params.scope) && (requested.size === 0 || requested.has(gate.name)));
  const branch = await currentBranch(pi);
  const head = await currentHead(pi);
  const base = await baseCommit(pi);
  const hash = await diffHash(pi);
  const results: Array<Record<string, unknown>> = [];

  for (const gate of gates) {
    const gateStatus = gate.enabled === false ? "SKIP" : "PASS";
    if (gate.enabled === false) {
      results.push({
        name: gate.name,
        status: "SKIP",
        reason: gate.notes ?? "Gate disabled in configuration",
        cwd: gate.cwd ?? ".",
      });
      continue;
    }
    const args = Array.isArray(gate.args) ? gate.args.map(String) : [];
    validateCommand(gate.command, args);
    const resolvedCwd = ensureInsideRepo(pi.cwd, gate.cwd ?? ".");
    const startedAt = nowIso();
    const startedMs = Date.now();
    const timeout = Math.max(1, Math.min(3600, gate.timeout_sec ?? 900));
    const result = await exec(pi, gate.command, args, resolvedCwd, signal, timeout);
    results.push({
      name: gate.name,
      status: result.code === 0 && !result.killed ? gateStatus : "FAIL",
      command: gate.command,
      args,
      cwd: path.relative(pi.cwd, resolvedCwd) || ".",
      started_at: startedAt,
      finished_at: nowIso(),
      duration_ms: Date.now() - startedMs,
      exit_code: result.code,
      killed: result.killed === true,
      stdout_tail: stdoutTail(result.stdout),
      stderr_tail: stdoutTail(result.stderr),
    });
    if (result.code !== 0 || result.killed) break;
  }

  const verdict = classifyOverall(results.map((item) => String(item.status)));
  const report = {
    schema_version: 1,
    scope: params.scope,
    id: params.id,
    verdict,
    created_at: nowIso(),
    branch,
    head,
    base_commit: base,
    diff_hash: hash,
    gates: results,
  };
  await ensureDir(path.join(pi.cwd, REPORTS_DIR));
  const outPath = path.join(pi.cwd, reportPath(`quality-${params.scope}`, params.id));
  await writeJsonAtomic(outPath, report);
  return { content: [{ type: "text", text: `Quality gate ${verdict}. Report: ${path.relative(pi.cwd, outPath)}` }], details: { reportPath: path.relative(pi.cwd, outPath), report } };
}

const factory = (pi: any) => ({
  name: "quality_gate",
  label: "Quality Gate",
  description: "Runs repository-defined allowlisted quality gates and stores a structured report",
  parameters: pi.zod.object({
    scope: pi.zod.enum(["task", "stage", "mission", "full"]),
    id: pi.zod.string().min(1).max(100),
    gateNames: pi.zod.array(pi.zod.string()).optional(),
  }),
  async execute(_toolCallId: string, params: Params, _onUpdate: unknown, _ctx: unknown, signal: AbortSignal) {
    return executeQualityGate(pi as PiApi, params, signal);
  },
});

export default factory;
'''

TOOLS_TASK_COMMIT = r'''
import fs from "node:fs/promises";
import path from "node:path";
import { REVIEWS_DIR, STATE_PATH, currentBranch, currentHead, diffHash, ensureNotProtectedBranch, ensureRepo, git, listChangedFiles, matchesAny, pathExists, readJson, readTaskContract, reportPath, reviewPath, safeWriteTextAtomic, stageExactFiles, taskContractHash, unstageFiles, worktreeStatus, writeJsonAtomic, type PiApi, type ToolResult } from "./lib/runtime.ts";

type ReviewReport = {
  schema_version: number;
  task_id: string;
  reviewer_role: string;
  verdict: string;
  branch: string;
  head: string;
  diff_hash: string;
  created_at: string;
  findings: Array<{ severity?: string; status?: string; title?: string }>;
};

type State = {
  schema_version: number;
  project: { phase: string; architecture_version: string | null };
  current_stage: null | { id: string; status: string };
  current_task: null | {
    id: string;
    stage_id: string;
    status: string;
    doc_path: string;
    expected_commit: string | null;
    allowed_paths: string[];
    reviewers: string[];
    approved_contract_sha256: string | null;
    started_head?: string | null;
  };
  blocked_by: unknown;
  history: Array<Record<string, unknown>>;
};

type Params = { taskId: string; message: string };

const conventionalCommit = /^(feat|fix|test|refactor|docs|build|ci|perf|chore)(\([a-z0-9._/-]+\))?!?: .{5,100}$/;
const writerRoles = new Set(["developer", "test-engineer", "documentation-writer", "github-drafter"]);

function requiredRoles(frontmatter: Record<string, unknown>): string[] {
  const roles = Array.isArray(frontmatter.reviewers) ? frontmatter.reviewers.map(String) : [];
  if (frontmatter.sensitive === true && !roles.includes("security-reviewer")) roles.push("security-reviewer");
  if (frontmatter.data_change === true && !roles.includes("data-reviewer")) roles.push("data-reviewer");
  if (frontmatter.performance_sensitive === true && !roles.includes("performance-reviewer")) roles.push("performance-reviewer");
  if (frontmatter.infrastructure_change === true && !roles.includes("devops-reviewer")) roles.push("devops-reviewer");
  if (!roles.includes("reviewer")) roles.unshift("reviewer");
  return [...new Set(roles)];
}

async function loadReview(filePath: string): Promise<ReviewReport> {
  return JSON.parse(await fs.readFile(filePath, "utf8")) as ReviewReport;
}

function hasBlockingFinding(report: ReviewReport): boolean {
  return report.findings.some((finding) => {
    const severity = String(finding.severity ?? "").toUpperCase();
    const status = String(finding.status ?? "open").toLowerCase();
    return status !== "resolved" && (severity === "P0" || severity === "P1");
  });
}

export async function executeTaskCommit(pi: PiApi, params: Params): Promise<ToolResult> {
  await ensureRepo(pi);
  if (!conventionalCommit.test(params.message)) throw new Error("Commit message must follow Conventional Commits");
  const branch = await ensureNotProtectedBranch(pi);
  if (!branch.startsWith("stage/")) throw new Error(`Expected stage/* branch, actual: ${branch}`);
  const statusBefore = await worktreeStatus(pi);
  const state = await readJson<State>(path.join(pi.cwd, STATE_PATH));
  if (!state.current_stage || state.current_stage.status !== "active") throw new Error("Current stage must be active");
  if (!state.current_task || state.current_task.id !== params.taskId) throw new Error("Current task mismatch");
  if (state.current_task.status !== "ready_to_commit") throw new Error(`Task status must be ready_to_commit, actual: ${state.current_task.status}`);
  const taskPath = path.join(pi.cwd, state.current_task.doc_path);
  const taskDoc = await readTaskContract(taskPath);
  if (String(taskDoc.frontmatter.id) !== params.taskId) throw new Error("Task document id mismatch");
  if (String(taskDoc.frontmatter.status) !== "ready_to_commit") throw new Error("Task document status must be ready_to_commit");
  const approvedHash = state.current_task.approved_contract_sha256 ?? (taskDoc.frontmatter.approved_contract_sha256 ? String(taskDoc.frontmatter.approved_contract_sha256) : null);
  if (!approvedHash) throw new Error("Missing approved_contract_sha256");
  if (taskDoc.contractHash !== approvedHash) throw new Error("Task contract changed after approval");
  const expectedCommit = state.current_task.expected_commit ?? (taskDoc.frontmatter.expected_commit ? String(taskDoc.frontmatter.expected_commit) : null);
  if (!expectedCommit) throw new Error("Missing expected_commit in task contract");
  if (params.message !== expectedCommit) throw new Error(`Commit message mismatch: expected ${expectedCommit}`);
  const allowed = state.current_task.allowed_paths.length > 0 ? state.current_task.allowed_paths : (Array.isArray(taskDoc.frontmatter.allowed_paths) ? taskDoc.frontmatter.allowed_paths.map(String) : []);
  if (allowed.length === 0) throw new Error("No allowed_paths in approved task contract");
  if (allowed.some((item) => item === "**" || item === "*")) throw new Error("Overbroad allowed_paths are forbidden");
  const changedFiles = await listChangedFiles(pi);
  if (changedFiles.length === 0) throw new Error("No changed files");
  const mandatory = new Set([STATE_PATH, state.current_task.doc_path]);
  const unexpected = changedFiles.filter((file) => !mandatory.has(file) && !matchesAny(file, allowed));
  if (unexpected.length > 0) throw new Error(`Unexpected changed files:\n${unexpected.join("\n")}`);
  await git(pi, ["diff", "--check"]);
  const reportFile = path.join(pi.cwd, reportPath("quality-task", params.taskId));
  if (!(await pathExists(reportFile))) throw new Error(`Missing quality report: ${path.relative(pi.cwd, reportFile)}`);
  const quality = await readJson<any>(reportFile);
  const currentHeadHash = await currentHead(pi);
  const currentDiffHash = await diffHash(pi);
  if (quality.verdict !== "PASS") throw new Error(`Task quality report must be PASS, actual: ${quality.verdict}`);
  if (quality.scope !== "task" || quality.id !== params.taskId) throw new Error("Task quality report id mismatch");
  if (quality.branch !== branch || quality.head !== currentHeadHash || quality.diff_hash !== currentDiffHash) throw new Error("Task quality report is stale");
  const required = requiredRoles(taskDoc.frontmatter);
  for (const role of required) {
    const reviewFile = path.join(pi.cwd, reviewPath(params.taskId, role));
    if (!(await pathExists(reviewFile))) throw new Error(`Missing review report: ${path.relative(pi.cwd, reviewFile)}`);
    const review = await loadReview(reviewFile);
    if (review.reviewer_role !== role) throw new Error(`Review role mismatch in ${reviewFile}`);
    if (writerRoles.has(review.reviewer_role)) throw new Error(`Synthetic writer review is forbidden: ${review.reviewer_role}`);
    if (review.task_id !== params.taskId) throw new Error(`Review task mismatch in ${reviewFile}`);
    if (review.verdict !== "approve") throw new Error(`Review did not approve: ${role}`);
    if (review.branch !== branch || review.head !== currentHeadHash || review.diff_hash !== currentDiffHash) throw new Error(`Review is stale: ${role}`);
    if (hasBlockingFinding(review)) throw new Error(`Blocking finding remains in review: ${role}`);
  }
  const stageReadme = path.join(pi.cwd, `docs/stages/${state.current_stage.id}-README.md`);
  if (!(await pathExists(stageReadme))) throw new Error(`Missing stage README: ${path.relative(pi.cwd, stageReadme)}`);
  const stagedByTool = [...changedFiles];
  let committed = false;
  try {
    await stageExactFiles(pi, stagedByTool);
    await git(pi, ["diff", "--cached", "--check"]);
    await git(pi, ["commit", "-m", params.message]);
    committed = true;
  } finally {
    if (!committed) {
      await unstageFiles(pi, stagedByTool);
      const statusAfterFailure = await worktreeStatus(pi);
      if (statusAfterFailure !== statusBefore) {
        // best effort only; do not mutate state on failure
      }
    }
  }
  const sha = await currentHead(pi);
  const updatedFrontmatter = { ...taskDoc.frontmatter, status: "done" };
  await safeWriteTextAtomic(taskPath, renderTask(updatedFrontmatter, taskDoc.body));
  const nextState: State = {
    ...state,
    current_task: {
      ...state.current_task,
      status: "done",
    },
    history: [
      ...state.history,
      {
        at: new Date().toISOString(),
        actor: "task_commit",
        action: "task_commit",
        scope: "task",
        from: "ready_to_commit",
        to: "done",
        reason: params.message,
        branch,
        head: sha,
      },
    ],
  };
  await writeJsonAtomic(path.join(pi.cwd, STATE_PATH), nextState);
  const dirty = await worktreeStatus(pi);
  if (dirty) throw new Error(`Commit created but worktree remains dirty:\n${dirty}`);
  return { content: [{ type: "text", text: `Committed ${params.taskId}: ${sha}` }], details: { sha, branch, files: changedFiles } };
}

function renderTask(frontmatter: Record<string, unknown>, body: string): string {
  const lines = Object.entries(frontmatter).map(([key, value]) => `${key}: ${stringifyValue(value)}`);
  return `---\n${lines.join("\n")}\n---\n${body.startsWith("\n") ? body : `\n${body}`}`;
}

function stringifyValue(value: unknown): string {
  if (value === null) return "null";
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "number") return String(value);
  if (Array.isArray(value)) return `[${value.map((item) => stringifyValue(item)).join(", ")}]`;
  return JSON.stringify(String(value));
}

const factory = (pi: any) => ({
  name: "task_commit",
  label: "Task Commit",
  description: "Validates task state, fresh reports and allowed file scope, then creates one commit",
  parameters: pi.zod.object({
    taskId: pi.zod.string().min(1).max(100),
    message: pi.zod.string().min(5).max(140),
  }),
  async execute(_toolCallId: string, params: Params) {
    return executeTaskCommit(pi as PiApi, params);
  },
});

export default factory;
'''

TOOLS_MISSION_COMMIT = r'''
import path from "node:path";
import { STATE_PATH, currentBranch, currentHead, diffHash, ensureNotProtectedBranch, ensureRepo, git, listChangedFiles, matchesAny, pathExists, readJson, reportPath, stageExactFiles, unstageFiles, worktreeStatus, type PiApi, type ToolResult } from "./lib/runtime.ts";

type Params = {
  mission: "design" | "roadmap" | "plan_stage" | "close_stage" | "prepare_github";
  message: string;
};

type State = {
  project: { phase: string };
  current_stage: null | { id: string; status: string };
  current_task: null | { id: string; status: string };
};

const conventionalCommit = /^(docs|chore|refactor)(\([a-z0-9._/-]+\))?!?: .{5,100}$/;
const policies: Record<Params["mission"], string[]> = {
  design: ["PROJECT_BRIEF.md", "docs/**", ".project-factory/**", "AGENTS.md", ".omp/**"],
  roadmap: ["docs/**", ".project-factory/**", "AGENTS.md"],
  plan_stage: ["docs/**", ".project-factory/**"],
  close_stage: ["docs/**", ".project-factory/**"],
  prepare_github: [".project-factory/github-outbox/**", ".project-factory/reports/**", ".project-factory/reviews/**"],
};

function appCodeForbidden(file: string): boolean {
  return /(src|app|server|client|api|lib)\//.test(file) || /\.(ts|tsx|js|jsx|go|rs|py|rb|java|kt|swift|cs)$/.test(file);
}

export async function executeMissionCommit(pi: PiApi, params: Params): Promise<ToolResult> {
  await ensureRepo(pi);
  if (!conventionalCommit.test(params.message)) throw new Error("Mission commit message must be docs/chore/refactor conventional commit");
  const branch = await ensureNotProtectedBranch(pi);
  const state = await readJson<State>(path.join(pi.cwd, STATE_PATH));
  const changedFiles = await listChangedFiles(pi);
  if (changedFiles.length === 0) throw new Error("No changed files");
  const allowed = policies[params.mission];
  const unexpected = changedFiles.filter((file) => !matchesAny(file, allowed));
  if (unexpected.length > 0) throw new Error(`Unexpected files for ${params.mission}:\n${unexpected.join("\n")}`);
  if (params.mission !== "prepare_github") {
    const appCode = changedFiles.filter(appCodeForbidden);
    if (appCode.length > 0) throw new Error(`Application code is forbidden in mission commit:\n${appCode.join("\n")}`);
  }
  const reportFile = path.join(pi.cwd, reportPath(`quality-mission`, params.mission));
  if (await pathExists(reportFile)) {
    const report = await readJson<any>(reportFile);
    if (report.verdict === "FAIL") throw new Error("Mission quality report failed");
    if (report.diff_hash && report.diff_hash !== await diffHash(pi)) throw new Error("Mission quality report is stale");
  }
  const stagedByTool = [...changedFiles];
  let committed = false;
  try {
    await stageExactFiles(pi, stagedByTool);
    await git(pi, ["diff", "--cached", "--check"]);
    await git(pi, ["commit", "-m", params.message]);
    committed = true;
  } finally {
    if (!committed) await unstageFiles(pi, stagedByTool);
  }
  const sha = await currentHead(pi);
  const dirty = await worktreeStatus(pi);
  if (dirty) throw new Error(`Mission commit left dirty tree:\n${dirty}`);
  return { content: [{ type: "text", text: `Mission committed ${params.mission}: ${sha}` }], details: { branch, sha, state } };
}

const factory = (pi: any) => ({
  name: "mission_commit",
  label: "Mission Commit",
  description: "Guarded commit for documentation/process missions",
  parameters: pi.zod.object({
    mission: pi.zod.enum(["design", "roadmap", "plan_stage", "close_stage", "prepare_github"]),
    message: pi.zod.string().min(5).max(140),
  }),
  async execute(_toolCallId: string, params: Params) {
    return executeMissionCommit(pi as PiApi, params);
  },
});

export default factory;
'''

AUDIT_SH = r'''#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: ./audit.sh /path/to/repository" >&2
}

REPO="${1:-}"
if [ -z "$REPO" ]; then
  usage
  exit 2
fi
if [ ! -d "$REPO" ]; then
  echo "ERROR: repository path does not exist: $REPO" >&2
  exit 2
fi
if ! command -v git >/dev/null 2>&1; then
  echo "ERROR: git is required" >&2
  exit 2
fi
if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 is required" >&2
  exit 2
fi
if ! command -v omp >/dev/null 2>&1; then
  echo "ERROR: omp is not installed" >&2
  exit 2
fi

REPO="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$REPO")"

echo "[audit] repository: $REPO"
echo "[audit] omp version: $(omp --version)"

git -C "$REPO" rev-parse --is-inside-work-tree >/dev/null
echo "[audit] git repo: PASS"
echo "[audit] branch: $(git -C "$REPO" branch --show-current || true)"

STATUS="$(git -C "$REPO" status --short --branch --untracked-files=all)"
if [ -n "$STATUS" ]; then
  echo "[audit] worktree: DIRTY"
  printf '%s\n' "$STATUS"
else
  echo "[audit] worktree: CLEAN"
fi

if [ -e "$REPO/.omp" ]; then
  echo "[audit] existing project .omp: yes"
else
  echo "[audit] existing project .omp: no"
fi

if [ -f "$HOME/.omp/profiles/factory/agent/config.yml" ]; then
  echo "[audit] existing factory profile: yes"
else
  echo "[audit] existing factory profile: no"
fi

for runtime in node python3 git unzip zip; do
  if command -v "$runtime" >/dev/null 2>&1; then
    echo "[audit] runtime $runtime: OK"
  else
    echo "[audit] runtime $runtime: MISSING"
  fi
done

if [ -f "$REPO/RULES.md" ]; then
  echo "[audit] WARNING: repository has top-level RULES.md; compare with project/.omp/RULES.md manually"
fi

echo "[audit] config keys snapshot:"
python3 - <<'PY'
import json, subprocess
data = json.loads(subprocess.check_output(['omp', 'config', 'list', '--json'], text=True))
keys = [
    'modelRoles', 'tools.approvalMode', 'async.enabled', 'task.batch',
    'task.maxConcurrency', 'task.maxRecursionDepth', 'task.isolation.mode',
    'skills.enabled', 'advisor.enabled', 'mcp.enableProjectConfig'
]
for key in keys:
    print(f"- {key}: {'present' if key in data else 'missing'}")
PY

echo "[audit] read-only audit complete"
'''

INSTALL_SH = r'''#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat >&2 <<'EOF'
Usage:
  ./install.sh /path/to/repository        # dry-run
  ./install.sh --apply /path/to/repository
EOF
}

APPLY=0
REPO=""
if [ "${1:-}" = "--apply" ]; then
  APPLY=1
  REPO="${2:-}"
else
  REPO="${1:-}"
fi

if [ -z "$REPO" ]; then
  usage
  exit 2
fi
if [ ! -d "$REPO" ]; then
  echo "ERROR: repository path does not exist: $REPO" >&2
  exit 2
fi
if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 is required" >&2
  exit 2
fi

ROOT_DIR="$(python3 -c 'import os; print(os.path.realpath("."))')"
REPO="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$REPO")"
STAMP="$(date +%Y%m%d-%H%M%S)"
PROFILE_DIR="$HOME/.omp/profiles/factory/agent"
PROJECT_SRC="$ROOT_DIR/project"
TEMPLATES_SRC="$ROOT_DIR/templates"

echo "[install] mode: $( [ "$APPLY" -eq 1 ] && echo APPLY || echo DRY-RUN )"
echo "[install] package root: $ROOT_DIR"
echo "[install] repository: $REPO"

for rel in \
  ".omp" \
  ".project-factory" \
  "docs" \
  "PROJECT_BRIEF.md" \
  "AGENTS.md"
do
  if [ -e "$REPO/$rel" ]; then
    echo "[install] existing path: $rel"
  fi
done

if [ "$APPLY" -ne 1 ]; then
  echo "[install] dry-run only. No files were changed. Re-run with --apply to install."
  exit 0
fi

mkdir -p "$PROFILE_DIR"
if [ -f "$PROFILE_DIR/config.yml" ]; then
  cp -p "$PROFILE_DIR/config.yml" "$PROFILE_DIR/config.yml.backup.$STAMP"
  echo "[install] backup: $PROFILE_DIR/config.yml.backup.$STAMP"
fi
cp -p "$ROOT_DIR/profile/config.yml" "$PROFILE_DIR/config.yml"

for rel in ".omp" ".project-factory" "docs" "PROJECT_BRIEF.md" "AGENTS.md"; do
  if [ -e "$REPO/$rel" ]; then
    cp -pR "$REPO/$rel" "$REPO/$rel.backup.$STAMP"
    echo "[install] backup: $REPO/$rel.backup.$STAMP"
  fi
done

mkdir -p "$REPO"
cp -pR "$PROJECT_SRC/." "$REPO/"
mkdir -p "$REPO/.project-factory"
cp -p "$TEMPLATES_SRC/QUALITY_GATES.json" "$REPO/.project-factory/quality-gates.json"
cp -p "$TEMPLATES_SRC/PROJECT_BRIEF.md" "$REPO/PROJECT_BRIEF.md"
cp -p "$TEMPLATES_SRC/PROJECT_STATE.json" "$REPO/docs/PROJECT_STATE.json"

echo "[install] installed factory profile and project payload"
echo "[install] no dependencies, MCP servers or plugins were installed"
echo "[install] next: ./verify.sh \"$REPO\""
'''

VERIFY_SH = r'''#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: ./verify.sh /path/to/repository" >&2
}

REPO="${1:-}"
if [ -z "$REPO" ]; then
  usage
  exit 2
fi
if [ ! -d "$REPO" ]; then
  echo "ERROR: repository path does not exist: $REPO" >&2
  exit 2
fi
if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 is required" >&2
  exit 2
fi
if ! command -v node >/dev/null 2>&1; then
  echo "ERROR: node is required" >&2
  exit 2
fi

ROOT_DIR="$(python3 -c 'import os; print(os.path.realpath("."))')"
REPO="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$REPO")"

echo "[verify] package root: $ROOT_DIR"
echo "[verify] target repo: $REPO"

bash -n audit.sh
bash -n install.sh
bash -n verify.sh
bash -n uninstall.sh
echo "[verify] shell syntax: PASS"

python3 - <<'PY'
import json, pathlib, sys
root = pathlib.Path('.')
json_files = [root / 'MANIFEST.json', root / 'project/.omp/mcp.json', root / 'templates/PROJECT_STATE.json', root / 'templates/QUALITY_GATES.json', root / 'project/docs/PROJECT_STATE.json']
for path in json_files:
    json.load(path.open(encoding='utf-8'))
print('[verify] package JSON parse: PASS')
repo = pathlib.Path(sys.argv[1])
repo_json = [repo / 'docs/PROJECT_STATE.json', repo / '.project-factory/quality-gates.json', repo / '.omp/mcp.json']
for path in repo_json:
    json.load(path.open(encoding='utf-8'))
print('[verify] repo JSON parse: PASS')
PY "$REPO"

python3 - <<'PY'
import pathlib, yaml
for path in [pathlib.Path('profile/config.yml'), pathlib.Path('project/.omp/config.yml'), pathlib.Path('project/.omp/WATCHDOG.yml')]:
    yaml.safe_load(path.read_text(encoding='utf-8'))
print('[verify] YAML parse: PASS')
PY

python3 - <<'PY'
import pathlib, re
skills = {p.parent.name for p in pathlib.Path('project/.omp/skills').glob('*/SKILL.md')}
if not skills:
    raise SystemExit('no skills found')
for path in pathlib.Path('project/.omp/agents').glob('*.md'):
    text = path.read_text(encoding='utf-8')
    if not text.startswith('---\n'):
        raise SystemExit(f'missing frontmatter in {path}')
    if 'spawns: []' not in text or 'blocking: true' not in text:
        raise SystemExit(f'missing required frontmatter fields in {path}')
    m = re.search(r'autoloadSkills:\s*\[(.*?)\]', text, re.S)
    if not m:
        raise SystemExit(f'missing autoloadSkills in {path}')
    names = [item.strip() for item in m.group(1).split(',') if item.strip()]
    for name in names:
        if name not in skills:
            raise SystemExit(f'broken autoloadSkills reference {name} in {path}')
print('[verify] agent frontmatter and autoloadSkills: PASS')
PY

python3 - <<'PY'
import pathlib
required = [
  'design-project.md', 'create-roadmap.md', 'plan-stage.md', 'run-task.md',
  'close-stage.md', 'prepare-github.md', 'project-status.md'
]
commands = {p.name for p in pathlib.Path('project/.omp/commands').glob('*.md')}
missing = [name for name in required if name not in commands]
if missing:
    raise SystemExit(f'missing commands: {missing}')
required_tools = {'project_state.ts', 'quality_gate.ts', 'task_commit.ts', 'mission_commit.ts', 'git_inspect.ts'}
tools = {p.name for p in pathlib.Path('project/.omp/tools').glob('*.ts')}
missing_tools = sorted(required_tools - tools)
if missing_tools:
    raise SystemExit(f'missing tools: {missing_tools}')
print('[verify] commands and tools present: PASS')
PY

for tool in project/.omp/tools/*.ts; do
  node --experimental-strip-types --input-type=module -e "import(process.argv[1]).then(() => process.stdout.write('[verify] TS import PASS: ' + process.argv[1] + '\n'))" "$tool"
done

python3 - <<'PY'
import pathlib, re
bad = []
patterns = [r'\bgh\s+issue\s+create\b', r'\bgh\s+pr\s+create\b', r'\bgh\s+pr\s+merge\b']
for path in pathlib.Path('.').rglob('*'):
    if path.is_dir():
        continue
    if path.parts[0] == '.git':
        continue
    text = path.read_text(encoding='utf-8', errors='ignore')
    for pattern in patterns:
        if re.search(pattern, text):
            bad.append((str(path), pattern))
if bad:
    raise SystemExit('forbidden mutating GitHub command found: ' + '; '.join(f'{p}:{pat}' for p, pat in bad[:10]))
print('[verify] forbidden mutating GitHub commands: PASS')
PY

node tests/run-tests.mjs
echo "[verify] local test harness: PASS"

if command -v omp >/dev/null 2>&1; then
  echo "[verify] omp version: $(omp --version)"
  omp config list --json >/dev/null
  echo "[verify] omp config list --json: PASS"
  if ! omp --profile factory models; then
    echo "[verify] WARNING: omp models discovery failed"
  fi
else
  echo "[verify] WARNING: omp not installed; runtime checks skipped"
fi

echo "[verify] complete"
'''

UNINSTALL_SH = r'''#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: ./uninstall.sh --apply /path/to/repository" >&2
}

if [ "${1:-}" != "--apply" ] || [ -z "${2:-}" ]; then
  usage
  exit 2
fi

REPO="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$2")"
PROFILE_DIR="$HOME/.omp/profiles/factory/agent"

echo "[uninstall] repository: $REPO"

for rel in ".omp" ".project-factory" "AGENTS.md"; do
  if [ -e "$REPO/$rel" ]; then
    rm -rf "$REPO/$rel"
    echo "[uninstall] removed $REPO/$rel"
  fi
done

if [ -f "$PROFILE_DIR/config.yml" ]; then
  rm -f "$PROFILE_DIR/config.yml"
  echo "[uninstall] removed $PROFILE_DIR/config.yml"
fi

echo "[uninstall] project docs and application code were preserved"
echo "[uninstall] inspect *.backup.* files manually if you want to restore prior state"
'''

TESTS_LIB = r'''import { mkdtempSync, rmSync, writeFileSync, mkdirSync, existsSync, readFileSync } from "node:fs";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { pathToFileURL } from "node:url";

export function tempRepo(prefix = 'factory-test-') {
  const dir = mkdtempSync(path.join(os.tmpdir(), prefix));
  execFileSync('git', ['init', '-q', dir]);
  execFileSync('git', ['-C', dir, 'config', 'user.email', 'factory@example.com']);
  execFileSync('git', ['-C', dir, 'config', 'user.name', 'Factory Test']);
  mkdirSync(path.join(dir, 'docs', 'stages'), { recursive: true });
  mkdirSync(path.join(dir, '.project-factory', 'reports'), { recursive: true });
  mkdirSync(path.join(dir, '.project-factory', 'reviews'), { recursive: true });
  mkdirSync(path.join(dir, '.project-factory', 'github-outbox'), { recursive: true });
  mkdirSync(path.join(dir, 'src'), { recursive: true });
  writeFileSync(path.join(dir, 'docs', 'stages', '01-README.md'), '# Stage 01\n', 'utf8');
  writeFileSync(path.join(dir, 'src', 'main.ts'), 'export const x = 1;\n', 'utf8');
  return dir;
}

export function cleanupRepo(dir) {
  rmSync(dir, { recursive: true, force: true });
}

export function git(dir, args) {
  return execFileSync('git', ['-C', dir, ...args], { encoding: 'utf8' }).trim();
}

export async function importTool(relativePath) {
  return import(pathToFileURL(path.resolve(relativePath)).href);
}

export function fakePi(cwd) {
  return {
    cwd,
    async exec(command, args, options = {}) {
      try {
        const stdout = execFileSync(command, args, {
          cwd: options.cwd ?? cwd,
          encoding: 'utf8',
          timeout: options.timeout ? options.timeout * 1000 : undefined,
          stdio: ['ignore', 'pipe', 'pipe'],
        });
        return { stdout, stderr: '', code: 0, killed: false };
      } catch (error) {
        return {
          stdout: error.stdout ? String(error.stdout) : '',
          stderr: error.stderr ? String(error.stderr) : error.message,
          code: typeof error.status === 'number' ? error.status : 1,
          killed: false,
        };
      }
    },
  };
}

export async function writeJson(file, value) {
  await fs.mkdir(path.dirname(file), { recursive: true });
  await fs.writeFile(file, JSON.stringify(value, null, 2) + '\n', 'utf8');
}

export async function seedFactoryRepo(dir) {
  const state = {
    schema_version: 2,
    project: { phase: 'implementation', architecture_version: 'v1' },
    current_stage: { id: '01', status: 'active', readme_path: 'docs/stages/01-README.md' },
    current_task: {
      id: '01-001',
      stage_id: '01',
      status: 'ready_to_commit',
      doc_path: 'docs/stages/tasks/01-001.md',
      expected_commit: 'feat(core): complete task 01-001',
      allowed_paths: ['src/**', 'docs/**', '.project-factory/**'],
      reviewers: ['reviewer'],
      approved_contract_sha256: null,
      started_head: null,
    },
    blocked_by: null,
    history: [],
  };
  await writeJson(path.join(dir, 'docs', 'PROJECT_STATE.json'), state);
  await fs.mkdir(path.join(dir, 'docs', 'stages', 'tasks'), { recursive: true });
  const taskDoc = `---\nid: "01-001"\nstage: "01"\nstatus: "ready_to_commit"\ntitle: "Task"\ntype: "feature"\nrisk: "medium"\nreviewers: [reviewer]\nallowed_paths: ["src/**", "docs/**", ".project-factory/**"]\nexpected_commit: "feat(core): complete task 01-001"\napproved_contract_sha256: null\nsensitive: false\ndata_change: false\nperformance_sensitive: false\ninfrastructure_change: false\n---\n\n# Scope\n\nTask body.\n\n# Completion summary\n\nPending.\n`;
  await fs.writeFile(path.join(dir, 'docs', 'stages', 'tasks', '01-001.md'), taskDoc, 'utf8');
  await fs.writeFile(path.join(dir, '.project-factory', 'quality-gates.json'), JSON.stringify({ schema_version: 1, gates: [] }, null, 2) + '\n', 'utf8');
  git(dir, ['add', '.']);
  git(dir, ['commit', '-q', '-m', 'chore: seed repo']);
  git(dir, ['branch', '-m', 'main']);
  git(dir, ['checkout', '-q', '-b', 'stage/01-foundation']);
}

export function assert(condition, message) {
  if (!condition) throw new Error(message);
}

export function read(file) {
  return readFileSync(file, 'utf8');
}
'''

TESTS_RUN = r'''import fs from "node:fs/promises";
import path from "node:path";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { existsSync } from "node:fs";
import { cleanupRepo, fakePi, git, importTool, seedFactoryRepo, tempRepo, assert, read, writeJson } from './testlib.mjs';

async function prepareCommitRepo() {
  const dir = tempRepo();
  await seedFactoryRepo(dir);
  const runtime = await importTool('./../project/.omp/tools/lib/runtime.ts');
  const taskPath = path.join(dir, 'docs', 'stages', 'tasks', '01-001.md');
  const source = read(taskPath);
  const contractHash = runtime.taskContractHash(source);
  const statePath = path.join(dir, 'docs', 'PROJECT_STATE.json');
  const state = JSON.parse(read(statePath));
  state.current_task.approved_contract_sha256 = contractHash;
  await writeJson(statePath, state);
  const updated = source.replace('approved_contract_sha256: null', `approved_contract_sha256: "${contractHash}"`);
  await fs.writeFile(taskPath, updated, 'utf8');
  await fs.writeFile(path.join(dir, 'src', 'main.ts'), 'export const x = 2;\n', 'utf8');
  const diffHash = await runtime.diffHash(fakePi(dir));
  const head = git(dir, ['rev-parse', 'HEAD']);
  const branch = git(dir, ['branch', '--show-current']);
  await writeJson(path.join(dir, '.project-factory', 'reports', 'quality-task-01-001-latest.json'), {
    schema_version: 1,
    scope: 'task',
    id: '01-001',
    verdict: 'PASS',
    created_at: new Date().toISOString(),
    branch,
    head,
    base_commit: head,
    diff_hash: diffHash,
    gates: [],
  });
  await writeJson(path.join(dir, '.project-factory', 'reviews', '01-001--reviewer.json'), {
    schema_version: 1,
    task_id: '01-001',
    reviewer_role: 'reviewer',
    verdict: 'approve',
    branch,
    head,
    diff_hash: diffHash,
    created_at: new Date().toISOString(),
    findings: [],
  });
  return dir;
}

async function testStateTransitions() {
  const dir = tempRepo('state-test-');
  try {
    const statePath = path.join(dir, 'docs', 'PROJECT_STATE.json');
    await writeJson(statePath, {
      schema_version: 2,
      project: { phase: 'brief', architecture_version: null },
      current_stage: null,
      current_task: null,
      blocked_by: null,
      history: [],
    });
    const mod = await importTool('./../project/.omp/tools/project_state.ts');
    const pi = fakePi(dir);
    await mod.executeProjectState(pi, { action: 'transition', actor: 'Main', scope: 'project', next: 'design_in_progress', reason: 'start design' });
    let state = JSON.parse(read(statePath));
    assert(state.project.phase === 'design_in_progress', 'project phase should advance');
    await mod.executeProjectState(pi, { action: 'transition', actor: 'Main', scope: 'project', next: 'blocked_owner_decision', reason: 'need owner' });
    state = JSON.parse(read(statePath));
    assert(state.project.phase === 'blocked_owner_decision', 'project should block');
    await mod.executeProjectState(pi, { action: 'owner_override', actor: 'Main', scope: 'project', next: 'design_in_progress', reason: 'owner answered' });
    state = JSON.parse(read(statePath));
    assert(state.project.phase === 'design_in_progress', 'owner override should resume');
    let failed = false;
    try {
      await mod.executeProjectState(pi, { action: 'transition', actor: 'Main', scope: 'project', next: 'roadmap_in_progress', reason: 'illegal jump' });
    } catch {
      failed = true;
    }
    assert(failed, 'invalid project transition must fail');
    await mod.executeProjectState(pi, { action: 'transition', actor: 'Main', scope: 'stage', stageId: '01', next: 'planning', reason: 'plan stage' });
    await mod.executeProjectState(pi, { action: 'transition', actor: 'Main', scope: 'stage', stageId: '01', next: 'planned', reason: 'stage planned' });
    state = JSON.parse(read(statePath));
    assert(state.current_stage.status === 'planned', 'stage should reach planned');
  } finally {
    cleanupRepo(dir);
  }
}

async function testQualityGateRestrictions() {
  const dir = tempRepo('gate-test-');
  try {
    await writeJson(path.join(dir, '.project-factory', 'quality-gates.json'), {
      schema_version: 1,
      gates: [
        { name: 'skip', scopes: ['task'], enabled: false, command: 'pnpm', args: ['lint'] },
      ],
    });
    const mod = await importTool('./../project/.omp/tools/quality_gate.ts');
    let result = await mod.executeQualityGate(fakePi(dir), { scope: 'task', id: '01-001' });
    assert(result.details.report.verdict === 'SKIP', 'disabled gate should yield SKIP');
    await writeJson(path.join(dir, '.project-factory', 'quality-gates.json'), {
      schema_version: 1,
      gates: [
        { name: 'escape', scopes: ['task'], enabled: true, cwd: '../..', command: 'pnpm', args: ['lint'] },
      ],
    });
    let failed = false;
    try {
      await mod.executeQualityGate(fakePi(dir), { scope: 'task', id: '01-001' });
    } catch {
      failed = true;
    }
    assert(failed, 'cwd escape must fail');
    await writeJson(path.join(dir, '.project-factory', 'quality-gates.json'), {
      schema_version: 1,
      gates: [
        { name: 'npx', scopes: ['task'], enabled: true, command: 'npx', args: ['foo'] },
      ],
    });
    failed = false;
    try {
      await mod.executeQualityGate(fakePi(dir), { scope: 'task', id: '01-001' });
    } catch {
      failed = true;
    }
    assert(failed, 'package-loading executables must fail');
  } finally {
    cleanupRepo(dir);
  }
}

async function testTaskCommitBlocksAndSuccess() {
  const mod = await importTool('./../project/.omp/tools/task_commit.ts');

  {
    const dir = await prepareCommitRepo();
    try {
      git(dir, ['checkout', '-q', 'main']);
      let failed = false;
      try {
        await mod.executeTaskCommit(fakePi(dir), { taskId: '01-001', message: 'feat(core): complete task 01-001' });
      } catch {
        failed = true;
      }
      assert(failed, 'task_commit must block on protected branch');
    } finally {
      cleanupRepo(dir);
    }
  }

  {
    const dir = await prepareCommitRepo();
    try {
      await fs.rm(path.join(dir, '.project-factory', 'reviews', '01-001--reviewer.json'));
      let failed = false;
      try {
        await mod.executeTaskCommit(fakePi(dir), { taskId: '01-001', message: 'feat(core): complete task 01-001' });
      } catch {
        failed = true;
      }
      assert(failed, 'task_commit must block without review');
    } finally {
      cleanupRepo(dir);
    }
  }

  {
    const dir = await prepareCommitRepo();
    try {
      const taskPath = path.join(dir, 'docs', 'stages', 'tasks', '01-001.md');
      let source = read(taskPath).replace('sensitive: false', 'sensitive: true');
      await fs.writeFile(taskPath, source, 'utf8');
      let failed = false;
      try {
        await mod.executeTaskCommit(fakePi(dir), { taskId: '01-001', message: 'feat(core): complete task 01-001' });
      } catch {
        failed = true;
      }
      assert(failed, 'task_commit must block missing security review');
    } finally {
      cleanupRepo(dir);
    }
  }

  {
    const dir = await prepareCommitRepo();
    try {
      await fs.writeFile(path.join(dir, 'secret.txt'), 'nope\n', 'utf8');
      let failed = false;
      try {
        await mod.executeTaskCommit(fakePi(dir), { taskId: '01-001', message: 'feat(core): complete task 01-001' });
      } catch {
        failed = true;
      }
      assert(failed, 'task_commit must block unexpected file');
    } finally {
      cleanupRepo(dir);
    }
  }

  {
    const dir = await prepareCommitRepo();
    try {
      await fs.writeFile(path.join(dir, 'src', 'main.ts'), 'export const x = 3;\n', 'utf8');
      let failed = false;
      try {
        await mod.executeTaskCommit(fakePi(dir), { taskId: '01-001', message: 'feat(core): complete task 01-001' });
      } catch {
        failed = true;
      }
      assert(failed, 'task_commit must block stale quality or review');
    } finally {
      cleanupRepo(dir);
    }
  }

  {
    const dir = await prepareCommitRepo();
    try {
      const taskPath = path.join(dir, 'docs', 'stages', 'tasks', '01-001.md');
      await fs.writeFile(taskPath, read(taskPath).replace('# Scope', '# Scope changed'), 'utf8');
      let failed = false;
      try {
        await mod.executeTaskCommit(fakePi(dir), { taskId: '01-001', message: 'feat(core): complete task 01-001' });
      } catch {
        failed = true;
      }
      assert(failed, 'task_commit must block modified task contract');
      const state = JSON.parse(read(path.join(dir, 'docs', 'PROJECT_STATE.json')));
      assert(state.current_task.status === 'ready_to_commit', 'failed commit must not mutate state');
    } finally {
      cleanupRepo(dir);
    }
  }

  {
    const dir = await prepareCommitRepo();
    try {
      let failed = false;
      try {
        await mod.executeTaskCommit(fakePi(dir), { taskId: '01-001', message: 'fix(core): wrong message' });
      } catch {
        failed = true;
      }
      assert(failed, 'task_commit must block wrong commit message');
    } finally {
      cleanupRepo(dir);
    }
  }

  {
    const dir = await prepareCommitRepo();
    try {
      const before = git(dir, ['rev-list', '--count', 'HEAD']);
      const result = await mod.executeTaskCommit(fakePi(dir), { taskId: '01-001', message: 'feat(core): complete task 01-001' });
      const after = git(dir, ['rev-list', '--count', 'HEAD']);
      assert(Number(after) === Number(before) + 1, 'successful task commit must create one commit');
      assert(git(dir, ['status', '--porcelain']) === '', 'tree must be clean after successful task commit');
      assert(String(result.content[0].text).includes('Committed 01-001'), 'result should mention committed task');
    } finally {
      cleanupRepo(dir);
    }
  }
}

async function testMissionCommit() {
  const dir = tempRepo('mission-test-');
  try {
    await seedFactoryRepo(dir);
    await fs.writeFile(path.join(dir, '.project-factory', 'github-outbox', 'issue-01.md'), '# Draft\n', 'utf8');
    const mod = await importTool('./../project/.omp/tools/mission_commit.ts');
    let result = await mod.executeMissionCommit(fakePi(dir), { mission: 'prepare_github', message: 'docs(github): update local drafts' });
    assert(String(result.content[0].text).includes('Mission committed prepare_github'), 'mission commit should succeed for outbox');
    await fs.writeFile(path.join(dir, 'src', 'bad.ts'), 'export const bad = true;\n', 'utf8');
    let failed = false;
    try {
      await mod.executeMissionCommit(fakePi(dir), { mission: 'roadmap', message: 'docs(roadmap): update roadmap' });
    } catch {
      failed = true;
    }
    assert(failed, 'mission_commit must block application code');
  } finally {
    cleanupRepo(dir);
  }
}

async function testGitInspect() {
  const dir = tempRepo('inspect-test-');
  try {
    await seedFactoryRepo(dir);
    const mod = await importTool('./../project/.omp/tools/git_inspect.ts');
    const branch = await mod.executeGitInspect(fakePi(dir), { action: 'current_branch' });
    assert(String(branch.content[0].text).startsWith('stage/'), 'git_inspect should report current branch');
  } finally {
    cleanupRepo(dir);
  }
}

async function testScriptsAndPackaging() {
  const dir = tempRepo('install-test-');
  const root = path.resolve('.');
  try {
    execFileSync('bash', ['audit.sh', dir], { cwd: root, stdio: 'pipe' });
    const before = git(dir, ['status', '--porcelain']);
    assert(before === '', 'audit must not mutate repo');
    execFileSync('bash', ['install.sh', dir], { cwd: root, stdio: 'pipe' });
    assert(!existsSync(path.join(dir, '.omp')), 'dry-run must not create files');
    execFileSync('bash', ['install.sh', '--apply', dir], { cwd: root, stdio: 'pipe' });
    assert(existsSync(path.join(dir, '.omp', 'commands', 'design-project.md')), 'apply install must copy commands');
    assert(existsSync(path.join(dir, '.project-factory', 'quality-gates.json')), 'apply install must copy quality gates');
    execFileSync('bash', ['install.sh', '--apply', dir], { cwd: root, stdio: 'pipe' });
    const backups = execFileSync('bash', ['-lc', 'compgen -G "' + dir + '/.omp.backup.*" || true'], { encoding: 'utf8' }).trim();
    assert(backups !== '', 'repeat install should create backup');
  } finally {
    cleanupRepo(dir);
  }
}

await testStateTransitions();
await testQualityGateRestrictions();
await testTaskCommitBlocksAndSuccess();
await testMissionCommit();
await testGitInspect();
await testScriptsAndPackaging();
console.log('[tests] PASS');
'''

TOOL_FILES = {
    'project/.omp/tools/lib/runtime.ts': TOOLS_COMMON,
    'project/.omp/tools/project_state.ts': TOOLS_STATE,
    'project/.omp/tools/git_inspect.ts': TOOLS_GIT_INSPECT,
    'project/.omp/tools/quality_gate.ts': TOOLS_QUALITY,
    'project/.omp/tools/task_commit.ts': TOOLS_TASK_COMMIT,
    'project/.omp/tools/mission_commit.ts': TOOLS_MISSION_COMMIT,
}

SCRIPT_FILES = {
    'audit.sh': AUDIT_SH,
    'install.sh': INSTALL_SH,
    'verify.sh': VERIFY_SH,
    'uninstall.sh': UNINSTALL_SH,
}

TEST_FILES = {
    'tests/testlib.mjs': TESTS_LIB,
    'tests/run-tests.mjs': TESTS_RUN,
}

PROJECT_CONFIG = PROFILE_CONFIG

def write_all() -> None:
    w('README_RU.md', README)
    w('CHANGELOG.md', CHANGELOG)
    w('REPAIR_REPORT.md', REPAIR_REPORT)
    for path, content in ROOT_EXTRA.items():
        w(path, content)
    w('profile/config.yml', PROFILE_CONFIG)
    w('project/AGENTS.md', PROJECT_AGENTS)
    w('project/.omp/config.yml', PROJECT_CONFIG)
    w('project/.omp/RULES.md', RULES)
    w('project/.omp/APPEND_SYSTEM.md', APPEND_SYSTEM)
    w('project/.omp/WATCHDOG.md', WATCHDOG)
    w('project/.omp/WATCHDOG.yml', WATCHDOG_YML)
    w('project/.omp/mcp.json', MCP_JSON)
    for path, content in DOCS.items():
        w(path, content)
    for path, content in TEMPLATES.items():
        w(path, content)
    for path, content in COMMANDS.items():
        w(path, content)
    for path, content in SKILLS.items():
        w(path, content)
    for path, content in AGENTS.items():
        w(path, content)
    for path, content in TOOL_FILES.items():
        w(path, content)
    for path, content in SCRIPT_FILES.items():
        w(path, content)
    for path, content in TEST_FILES.items():
        w(path, content)


if __name__ == '__main__':
    write_all()
    print('package files generated')
