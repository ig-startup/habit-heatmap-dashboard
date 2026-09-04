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
  Weekly/Single, реальный GitHub API, сотрудники, Obsidian/YouTube-агенты, auth —
  следующие milestone'ы (ТЗ §6).

## Структура

```
backend/app/   — FastAPI, SQLAlchemy async, роутер /api/metrics
frontend/src/  — React + TS, компоненты в components/
```

## Тесты

`cd backend && .venv/bin/pytest` — backend покрыт (создание метрики, streak с разрывом,
year-scoped heatmap, upsert события, 404 на несуществующую метрику).
Frontend-тестов нет — MVP проверялся вручную в браузере (playwright screenshot).
