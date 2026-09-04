# Local agent

Локальный демон на Mac, закрывающий metrics-источники, которые не доступны
удалённому бэкенду: Obsidian (word-count по `Статьи`) и YouTube (macOS Screen
Time). См. ТЗ §2.2–2.3, §4.

## Установка

```bash
cd local-agent
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

В корневом `.env` (см. `.env.example`) должны быть заданы:

```
BACKEND_URL=http://localhost:8000       # или адрес задеплоенного бэкенда
INGEST_TOKEN=...                        # тот же секрет, что и в backend .env
OBSIDIAN_ARTICLES_PATH=/Users/.../Статьи
```

## Full Disk Access (обязательно для YouTube-коллектора)

`knowledgeC.db` (источник macOS Screen Time) защищён TCC — без доступа
sqlite3 вернёт `authorization denied`. Нужно дать Full Disk Access:

1. System Settings → Privacy & Security → Full Disk Access
2. Добавить бинарник Python, которым запускается агент — `local-agent/.venv/bin/python3.13`
   (точный путь можно узнать: `local-agent/.venv/bin/python3 -c "import sys; print(sys.executable)"`)
3. Перезапустить агент

Без этого доступа Obsidian-часть агента продолжит работать нормально —
упадёт только YouTube-коллектор (ошибка логируется, не крашит процесс).

## Ручной запуск (для проверки)

```bash
.venv/bin/python3 agent.py
```

## Автозапуск по расписанию (launchd, каждые 15 минут)

```bash
./launchd/install.sh
```

Логи: `local-agent/logs/agent.log`. Остановить: `launchctl unload ~/Library/LaunchAgents/com.igfinance.habit-heatmap-agent.plist`.

## Тесты

```bash
.venv/bin/pytest -q
```

Только Obsidian-коллектор покрыт тестами (детерминированная логика на
`tmp_path`). YouTube-коллектор читает реальный `knowledgeC.db` — тестируется
вручную, требует Full Disk Access.

## Известные ограничения

- YouTube-агент пока закрывает только Mac (`knowledgeC.db`). iPhone-часть
  через `aw-import-screentime` (Biome/iCloud-синк) — не сделана, следующий шаг.
- Формат `knowledgeC.db` не документирован Apple — может измениться в
  будущих версиях macOS. План Б — ручной ввод значения в дашборд.
