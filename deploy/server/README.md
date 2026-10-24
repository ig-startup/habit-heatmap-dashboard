# Деплой на sites-prod (80.71.152.161)

Деплой — только через GitHub Actions (`.github/workflows/deploy.yml`) при мёрже в `main`.
`scripts/deploy.sh` больше не использовать: он собирает образы на сервере (инцидент 07.10).

## Как устроено

1. Actions прогоняет тесты, собирает образы backend/frontend и кладёт их в
   `ghcr.io/ig-startup/habit-heatmap-dashboard-{backend,frontend}` с тегами `<sha>` и `latest`.
2. Actions заходит `ssh deploy@sites-prod <sha>`. Ключ CI в `authorized_keys` привязан к
   `habit-deploy-ssh`, тот через sudo запускает только `habit-deploy <sha>`.
3. `habit-deploy` берёт `docker-compose.yml` этого коммита, скачивает образы, перезапускает,
   проверяет `/api/metrics`; при сбое возвращает прежнюю версию. Текущая версия — `/opt/habit-heatmap-dashboard/.deployed`.

`.env` с секретами живёт только на сервере (`/opt/habit-heatmap-dashboard/.env`), деплой его не трогает.

## Установка на сервер (один раз, под root)

```bash
install -m 755 -o root -g root habit-deploy     /usr/local/bin/habit-deploy
install -m 755 -o root -g root habit-deploy-ssh /usr/local/bin/habit-deploy-ssh
echo 'deploy ALL=(root) NOPASSWD: /usr/local/bin/habit-deploy' > /etc/sudoers.d/habit-deploy
chmod 440 /etc/sudoers.d/habit-deploy && visudo -cf /etc/sudoers.d/habit-deploy
# в /home/deploy/.ssh/authorized_keys:
# command="/usr/local/bin/habit-deploy-ssh",restrict ssh-ed25519 AAAA… gha-sites-prod-habit
```

После правки скриптов в репо — переустановить их той же командой `install`.

## Руками (аварийно)

```bash
ssh sites-prod 'cat /opt/habit-heatmap-dashboard/.deployed'          # что сейчас на проде
ssh sites-prod '/usr/local/bin/habit-deploy <sha>'                   # выкатить/откатить коммит
```
