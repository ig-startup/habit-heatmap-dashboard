# Habit Heatmap Dashboard

Личный дашборд активности (GitHub, Obsidian, YouTube...) в виде GitHub-style хитмапов.
ТЗ: `../019-09 assets-control/tz-habit-heatmap-dashboard.md`.

Текущий статус: **milestone 1 (MVP)** — бэкенд + БД + Yearly-хитмап, одна метрика
(GitHub, мок-данные). Реальный сбор данных, сотрудники, Obsidian/YouTube-агенты,
Weekly/Single-режимы, auth — следующие итерации (см. ТЗ §6).

## Стек

- Backend: FastAPI + SQLAlchemy (async) + PostgreSQL
- Frontend: React + TypeScript + Vite + Tailwind CSS
- Деплой: Docker Compose (db + backend + frontend/nginx)

## Запуск локально (Docker)

```bash
cp .env.example .env
docker compose up --build
```

Фронтенд: http://localhost:5180

## Запуск в dev-режиме (без Docker)

```bash
# backend
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
DATABASE_URL="sqlite+aiosqlite:////tmp/habits_dev.db" .venv/bin/uvicorn app.main:app --reload --port 8000

# frontend (в отдельном терминале)
cd frontend
npm install
npm run dev
```

При первом старте backend сам засеивает мок-метрику "GitHub — я" данными за последний год.

## Тесты

```bash
cd backend
.venv/bin/pytest
```

## Модель данных

Универсальная схема `Metric` + `MetricEvent` (см. ТЗ §4) — новая метрика добавляется записью
в `metrics` без изменения кода ядра; конкретный источник данных (коллектор) подключается отдельно.
