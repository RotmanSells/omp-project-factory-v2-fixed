# Repair Report

## Результат версии 2.1.0

Пакет повторно исправлен после независимого аудита исходников. Project Atlas намеренно не включён.

### Исправленные блокирующие дефекты

- Все 28 `SKILL.md` теперь начинаются с YAML frontmatter в первом байте и доступны native OMP discovery.
- Завершённая task может быть заменена следующей approved task; завершённый stage может быть заменён следующим stage в `planning`.
- `owner_override` возвращает только в точное состояние до блокировки и не принимает произвольные значения.
- Обычный `project_state` не может поставить task в `done`; это делает только `task_commit` после успешного Git commit.
- Добавлен `review_report`, который сам фиксирует branch, HEAD, diff hash, роль, verdict и findings.
- `task_commit` требует свежий `PASS` quality report и свежие role-bound reviews, проверяет stage branch и `started_head`, а при ошибке commit восстанавливает task/state.
- `mission_commit` требует допустимое состояние миссии, свежий `PASS` mission gate и свежий documentation review.
- `quality_gate` блокирует inline shell/Python, команды установки/публикации, неизвестные package scripts, path traversal и symlink escape.
- Installer сохраняет существующие brief/state/gates и создаёт installation ledger с backup.
- Uninstaller работает по ledger: изменённые пользователем файлы не удаляются, новые factory-файлы перемещаются в обратимый quarantine, заменённые файлы восстанавливаются из backup.

### Процесс разработки

Миссии приведены к утверждённой схеме владельца:

1. DESIGN: brief, вопросы, актуальное исследование, независимый architecture critic, решения владельца, полная документация и stack-specific rules; без application code.
2. ROADMAP: вертикальные stages с outcome, demo и DoD; без подробного планирования далёких stages.
3. PLAN STAGE: короткая карта всего этапа и ровно три ближайшие подробные task contracts.
4. RUN TASK: одна approved task, один writer, TDD по риску, focused gates, независимые reviews, один guarded commit и остановка.
5. CLOSE STAGE: все tasks done, integration, главный E2E, условные security/load checks, docs consistency и closeout.
6. PREPARE GITHUB: только локальные drafts, без публикации, push, merge или tag.

Архитекторы не обязаны искусственно соглашаться: материальный спор показывается владельцу как варианты, последствия и рекомендация. Ограничение 2500-3000 строк является warning ceiling, а не целью. E2E обязателен для stage, а README — для значимых модулей.

### State model

- project: `brief -> design_in_progress -> architecture_owner_review -> architecture_approved -> roadmap_in_progress -> roadmap_approved -> implementation -> completed`
- stage: `planning -> planned -> active -> closing -> done`
- task: `draft -> owner_review -> approved -> in_progress -> in_review -> ready_to_commit -> done`
- `blocked_owner_decision` хранит scope и точное предыдущее состояние
- history хранит actor, scope, from/to, reason, branch, HEAD и timestamp

### Проверки

GitHub Actions выполняет:

- release metadata regeneration;
- package JSON/YAML/frontmatter validation;
- TypeScript tool imports;
- behavioral tests state/commit/review/gate tools;
- две последовательные tasks и два последовательных stages;
- installer preservation and repeat install;
- reversible uninstall;
- control repository installation and verification;
- manifest/checksum generation as workflow artifact.

Первый полный PR-run `verify-factory` завершился успешно 6 августа 2026 года. Финальный merge выполняется только после повторного зелёного run на окончательном diff.

## Ограничения

- Реальные provider models требуют credentials владельца и проверяются командой `omp --profile factory models`.
- Stack-specific quality commands настраиваются после DESIGN; `NOT_CONFIGURED` и `SKIP` не считаются `PASS` для guarded commits.
- Пакет не устанавливает dependencies, MCP или plugins и не публикует GitHub artifacts.
- Интерактивное выполнение полной миссии в OMP требует настроенных моделей; CI проверяет discovery-compatible layout, imports и поведенческую логику tools.
- SHA-256 итогового ZIP сообщается внешне после сборки, чтобы не создавать самоссылочный hash внутри архива.
