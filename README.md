# Сайт Центра ДПО факультета права НИУ ВШЭ

Новая версия сайта Центра дополнительного профессионального образования. Переписывается с нуля
на готовых фреймворках вместо самописного кода прежней версии
([itspecR/dpo-pravo-hse](https://github.com/itspecR/dpo-pravo-hse)). Дизайн сохраняется.

## Стек

| Часть | Технологии |
|---|---|
| Публичный сайт | Astro (статическая сборка, без JS по умолчанию), TypeScript |
| Сервер | Django 5.2 LTS, django-ninja (API), gunicorn |
| Админка | Django Admin с темой Unfold, защита от подбора пароля django-axes |
| База данных | MariaDB 11.8 (в контейнере) |
| Веб-сервер | nginx: раздаёт статику, проксирует `/api/`, `/admin/`, `/static/` |
| Развёртывание | Docker Compose, скрипты в `scripts/` |
| Проверки | pytest, ruff, mypy (strict), ESLint, astro check, shellcheck, GitHub Actions |

```
браузер ──► nginx (web) ──► статические страницы Astro
                 │
                 └─► /api/, /admin/, /static/ ──► gunicorn + Django (app) ──► MariaDB (db)
```

## Структура

```
backend/            Django: config (настройки, API), core (служебное), accounts (пользователи), tests
frontend/           Astro: страницы, макеты, стили и шрифты
deploy/             Dockerfile для app и web, конфигурация nginx
scripts/            установка, обновление, резервные копии, HTTPS
docker-compose.yml  три контейнера: db, app, web
```

## Установка на сервер

Нужен сервер с Ubuntu 24.04 (или новее), доступ по SSH с правами sudo, свободные порты 80 и 443.
Скрипт сам поставит Docker, если его нет.

1. Склонируйте репозиторий. Он приватный, поэтому серверу нужен ключ доступа только на чтение (deploy key):

   ```bash
   ssh-keygen -t ed25519 -N "" -f ~/.ssh/dpo_deploy
   cat ~/.ssh/dpo_deploy.pub
   ```

   Добавьте показанный ключ в GitHub: репозиторий → Settings → Deploy keys → Add deploy key
   (галочку «Allow write access» не ставьте). Затем:

   ```bash
   GIT_SSH_COMMAND="ssh -i ~/.ssh/dpo_deploy" git clone git@github.com:itspecR/dpo-pravo-hse-v2.git ~/dpo
   cd ~/dpo
   git config core.sshCommand "ssh -i ~/.ssh/dpo_deploy"
   ```

2. Запустите установку:

   ```bash
   sudo ./scripts/install.sh            # сайт по HTTP
   sudo ./scripts/install.sh --https    # сразу с самоподписанным HTTPS
   ```

   Скрипт сделает всё по шагам:
   - поставит пакеты;
   - создаст `.env` со случайными паролями (файл доступен только владельцу);
   - соберёт и запустит контейнеры, применит миграции;
   - попросит логин и пароль администратора;
   - включит ежедневную резервную копию.

3. Откройте `http://<IP сервера>/` — заглушка сайта, `http://<IP сервера>/admin/` — админка.

Если группа `docker` была добавлена только что, перезайдите по SSH: после этого скрипты обновления
работают без `sudo`.

## Обновление

```bash
./scripts/update.sh          # ветка main
./scripts/deploy.sh <ветка>  # любая ветка
```

Порядок: получить код → собрать контейнеры → резервная копия базы → миграции → запуск → проверка
`/api/health`. Если любой шаг упал, скрипт вернёт прошлую версию кода и подскажет команду
восстановления базы.

## HTTPS

```bash
sudo ./scripts/setup-https.sh [домен-или-IP ...]
```

Создаёт самоподписанный сертификат в `/etc/dpo/tls`, включает защищённые cookie и перезапускает
сайт. Сертификат Let's Encrypt для настоящего домена будет добавлен отдельным шагом, когда домен
будет известен.

## Резервные копии

- Каждый день в 03:00 по Москве (таймер systemd `dpo-backup`). Хранятся последние `BACKUP_KEEP`
  копий в `BACKUP_DIR` (по умолчанию 30 штук в `/var/backups/dpo`).
- Вручную: `sudo ./scripts/backup.sh`.
- Восстановление: `sudo ./scripts/restore.sh` покажет список копий,
  `sudo ./scripts/restore.sh <файл>` восстановит базу (перед этим сохранит текущую).
- Таймер: `sudo ./scripts/backup-timer.sh status|install|remove`.

## Администраторы

- Новый администратор: `./scripts/create-admin.sh`.
- Пароль — не короче 12 символов.
- После 5 неверных попыток пара «логин + адрес» блокируется на 15 минут.
- Снять блокировку: `docker compose exec app python manage.py axes_reset`.

## Настройки (`.env`)

| Переменная | Назначение |
|---|---|
| `DJANGO_SECRET_KEY` | секретный ключ Django, создаётся при установке |
| `DJANGO_DEBUG` | `1` только для разработки |
| `DJANGO_ALLOWED_HOSTS` | адреса и домены сайта через запятую |
| `COOKIE_SECURE` | `1` при работе по HTTPS |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD` | база MariaDB |
| `HTTP_PORT`, `HTTPS_PORT` | внешние порты nginx |
| `TLS_DIR` | папка с сертификатом |
| `BACKUP_DIR`, `BACKUP_KEEP` | куда и сколько копий хранить |

## Разработка

Сервер (нужны Python 3.12 и MariaDB):

```bash
python -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
export DJANGO_SECRET_KEY=dev DB_HOST=127.0.0.1 DB_USER=root DB_PASSWORD=<пароль>
.venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/mypy && .venv/bin/pytest
```

Сайт (нужен Node.js 24):

```bash
cd frontend && npm ci
npm run lint && npm run build
npm run dev   # http://127.0.0.1:4321, запросы /api и /admin уходят на Django :8000
```

Все проверки повторяются в GitHub Actions (`.github/workflows/ci.yml`), включая полную установку
`install.sh` на чистой машине, резервную копию и восстановление.
