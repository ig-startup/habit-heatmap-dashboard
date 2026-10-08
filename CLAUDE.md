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
- Milestone 2 (GitHub, реальные данные) и milestone 3 (Obsidian/YouTube/Telegram-агент) —
  реализованы, см. ниже.
- GitHub: реальная активность через GraphQL (`contributionsCollection`), синк при
  старте бэкенда (`backend/app/sync_github.py`), фолбэк на мок при отсутствии
  токена/ошибке.
- Obsidian/YouTube/Telegram: универсальный ingest-эндпоинт `POST /api/metrics/{slug}/ingest`
  (slug ∈ `obsidian`/`youtube`/`telegram`), метрика создаётся лениво при первом ingest
  (`source_type=webhook`, `meta.slug`). Защищён shared-secret заголовком
  `X-Ingest-Token` (`INGEST_TOKEN` в `.env`) — обязателен всегда, без токена
  ingest недоступен (fail-closed).
- Данные шлёт локальный агент-демон на Mac (`local-agent/`, launchd, каждые 2 часа):
  Obsidian — word-count дельта по папке `Статьи` (не весь vault); YouTube — время
  на youtube.com из `knowledgeC.db` (macOS Screen Time), требует Full Disk Access.
  iPhone-часть через `aw-import-screentime` — не сделана (см. `local-agent/README.md`).
- Telegram: посты в канале (не просмотры/ER — решили не делать MTProto-логин
  ради простоты). Скрапинг публичной `t.me/s/<channel>` (без API/логина),
  каждый прогон агента видит только последние ~20 постов; полная история —
  разовый `local-agent/backfill_telegram.py` проходом по `?before=` пагинации.
  Значение за день = число постов (каждое сообщение, включая репосты/альбомы,
  считается отдельно). Работает только для публичных каналов.
- Milestone 4 (Yandex Metrika — посетители сайта): бэкенд-синк
  `backend/app/sync_metrika.py` + `backend/app/services/yandex_metrika.py`,
  по образцу GitHub (`GET stat/v1/data`, `dimensions=ym:s:date`,
  `metrics=ym:s:visits`, `Authorization: OAuth <token>`), периодический ресинк
  каждый час (`METRIKA_SYNC_INTERVAL_SECONDS`). Нужны `YANDEX_METRIKA_TOKEN`
  и `YANDEX_METRIKA_COUNTER_ID` в `.env` — без обоих синк просто выключен
  (мок-фолбэка нет, в отличие от GitHub). Метрика создаётся один раз при
  первом успешном синке (`source_type=metrika`).
  Визуализация — не обычный Yearly-хитмап, а отдельный компонент
  `frontend/src/components/GrowthStaircase.tsx` в духе графика трат Apple
  Card: один столбец = один день, серый бар — скользящий максимум за 7 дней,
  оранжевый поверх — значение за сам день, оба нормированы на максимум
  7-дневного максимума во всём видимом окне; подписи `0`/максимума по левому
  краю (`AXIS_GUTTER`). `HeatmapCard` выбирает этот компонент для
  `metric.source_type === "metrika"` и `"ton"` (см. ниже), обычный Yearly-хитмап
  — для остальных. Используется также для milestone 5.
- Milestone 5 (TON-кошелёк — баланс): бэкенд-синк `backend/app/sync_ton.py` +
  `backend/app/services/ton.py`, публичный `toncenter.com` API
  (`GET /api/v2/getAddressBalance?address=...`, без API-ключа), периодический
  ресинк раз в час (`TON_SYNC_INTERVAL_SECONDS`). Нужен только `TON_WALLET_ADDRESS`
  в `.env` — без него синк выключен. В отличие от GitHub/Metrika, у публичного API
  нет истории баланса по дням — только текущий снимок, поэтому каждый синк просто
  апсертит значение на СЕГОДНЯ (`source_type=ton`, `aggregation=last`); дни до
  начала трекинга остаются пустыми, как у Obsidian/Telegram в начале.

## Структура

```
backend/app/     — FastAPI, SQLAlchemy async, роутер /api/metrics
frontend/src/    — React + TS, компоненты в components/
local-agent/     — демон на Mac: сбор Obsidian/YouTube/Telegram, пуш на /api/metrics/*/ingest
```

## Тесты

`cd backend && .venv/bin/pytest` — 13 тестов (метрики, streak, heatmap, upsert,
GitHub-синк, ingest-эндпоинт с auth).
`cd local-agent && .venv/bin/pytest` — 10 тестов: 5 Obsidian-коллектора (word-count
delta, baseline-логика), 5 Telegram-коллектора (парсинг HTML, пагинация, group-by-day).
YouTube-коллектор тестируется только вручную (нужен реальный `knowledgeC.db` +
Full Disk Access).
Frontend-тестов нет — MVP проверялся вручную в браузере (playwright screenshot).
