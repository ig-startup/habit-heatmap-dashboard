# CLAUDE.md — Habit Heatmap Dashboard

## Архитектурные решения (зафиксировано)

- Отдельный сервис (не модуль в `019-09 assets-control`) — свой стек по ТЗ:
  Postgres + FastAPI + React/Tailwind + Docker Compose.
- Универсальная модель `Metric` + `MetricEvent` (ТЗ §4) — новые метрики добавляются
  без изменения ядра.
- Streak / total_days_tracked / today_value считаются на лету из `metric_events`,
  не хранятся отдельными полями.
- Тёмная тема — единственная, см. `DESIGN.md`.
- MVP (milestone 1): только GitHub-метрика, мок-данные, только Yearly-вид.
  Weekly/Single, сотрудники, auth — следующие milestone'ы (ТЗ §6).
- Milestone 2 (GitHub, реальные данные) и milestone 3 (Obsidian/YouTube-агент) —
  реализованы, см. ниже.
- GitHub: реальная активность через GraphQL (`contributionsCollection`), синк при
  старте бэкенда (`backend/app/sync_github.py`), фолбэк на мок при отсутствии
  токена/ошибке.
- Obsidian/YouTube: универсальный ingest-эндпоинт `POST /api/metrics/{slug}/ingest`
  (slug ∈ `obsidian`/`youtube`), метрика создаётся лениво при первом ingest
  (`source_type=webhook`, `meta.slug`). Защищён shared-secret заголовком
  `X-Ingest-Token` (`INGEST_TOKEN` в `.env`) — обязателен всегда, без токена
  ingest недоступен (fail-closed).
- Данные шлёт локальный агент-демон на Mac (`local-agent/`, launchd, каждые 15 мин):
  Obsidian — word-count дельта по папке `Статьи` (не весь vault); YouTube — время
  на youtube.com из `knowledgeC.db` (macOS Screen Time), требует Full Disk Access.
  iPhone-часть через `aw-import-screentime` — не сделана (см. `local-agent/README.md`).

## Структура

```
backend/app/     — FastAPI, SQLAlchemy async, роутер /api/metrics
frontend/src/    — React + TS, компоненты в components/
local-agent/     — демон на Mac: сбор Obsidian/YouTube, пуш на /api/metrics/*/ingest
```

## Тесты

`cd backend && .venv/bin/pytest` — 13 тестов (метрики, streak, heatmap, upsert,
GitHub-синк, ingest-эндпоинт с auth).
`cd local-agent && .venv/bin/pytest` — 5 тестов Obsidian-коллектора (word-count
delta, baseline-логика). YouTube-коллектор тестируется только вручную (нужен
реальный `knowledgeC.db` + Full Disk Access).
Frontend-тестов нет — MVP проверялся вручную в браузере (playwright screenshot).
