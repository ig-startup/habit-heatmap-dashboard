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

## YouTube-коллектор — отложен (нужен Full Disk Access)

`YOUTUBE_COLLECTOR_ENABLED=false` по умолчанию — коллектор не запускается.
Причина: `knowledgeC.db` (источник macOS Screen Time) защищён TCC, доступ
открывается только через **Full Disk Access**, а это не узкое разрешение
«только на этот файл» — это доступ ко всему, что TCC защищает на диске
(Mail, Messages, история Safari, контейнеры других приложений и т.д.), причём
выдаётся он **конкретному бинарнику интерпретатора** (`local-agent/.venv/bin/python3.13`,
который обычно является symlink на системный python), а не только этому
скрипту. Если тот же системный python используется другими venv/проектами —
они тоже получат FDA.

Когда решите включать:
1. Рассмотреть выделенный python-интерпретатор только для `local-agent`
   (например через `pyenv`), чтобы FDA не расползался на другие проекты
2. System Settings → Privacy & Security → Full Disk Access → добавить бинарник
   (точный путь: `local-agent/.venv/bin/python3 -c "import sys; print(sys.executable)"`)
3. В `.env` выставить `YOUTUBE_COLLECTOR_ENABLED=true`
4. Перезапустить агент

Пока выключено, Obsidian-часть агента работает независимо и не требует
никаких дополнительных разрешений.

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
