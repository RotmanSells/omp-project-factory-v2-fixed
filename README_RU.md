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
