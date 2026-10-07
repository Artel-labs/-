#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

SYNCED_FLAG=DEPLOY_SYNCED_FROM

main() {
    local branch="${1:-main}" root
    root="$(project_root)"
    cd "$root"
    load_env "$root"
    upgrade_env "$root"
    if [[ -d .git && -z "${!SYNCED_FLAG:-}" ]]; then
        step "1/6" "Получаем ветку ${branch}"
        restart_with_new_code "$root" "$branch"
    fi
    if [[ -d .git ]]; then
        trap 'roll_back "${!SYNCED_FLAG}"' ERR
    else
        step "1/6" "Установка из архива: берём файлы из $root как есть"
        trap 'archive_failed' ERR
    fi
    step "2/6" "Скачиваем образы и собираем контейнеры"
    fetch_and_build
    step "3/6" "Резервная копия базы перед миграциями"
    as_root "$root/scripts/backup.sh"
    step "4/6" "Применяем миграции базы"
    docker compose run --rm app python manage.py migrate --noinput
    docker compose run --rm app python manage.py seed_catalog
    step "5/6" "Запускаем новую версию"
    docker compose up -d --remove-orphans
    step "6/6" "Проверяем, что сайт отвечает"
    wait_for_site
    trap - ERR
    echo "Готово: новая версия развёрнута."
}

restart_with_new_code() {
    local previous
    previous="$(git rev-parse HEAD)"
    sync_branch "$2"
    export "$SYNCED_FLAG=$previous"
    exec "$1/scripts/deploy.sh" "$2"
}

sync_branch() {
    git fetch origin "$1"
    git checkout -B "$1" "origin/$1"
    git reset --hard "origin/$1"
}

roll_back() {
    trap - ERR
    echo >&2
    echo "Ошибка развёртывания. Возвращаем прошлую версию кода ($(git rev-parse --short "$1"))." >&2
    git reset --hard "$1"
    docker compose up -d --build --remove-orphans || true
    wait_for_site || true
    echo "Прошлая версия запущена. Если миграции успели примениться и сайт работает с ошибками," >&2
    echo "восстановите базу из копии, сделанной перед миграциями: sudo ./scripts/restore.sh $(latest_backup) --key <закрытый ключ копий>" >&2
    exit 1
}

archive_failed() {
    trap - ERR
    echo >&2
    echo "Ошибка развёртывания. Верните прошлую папку сайта (с файлом .env) и запустите deploy.sh в ней." >&2
    echo "Если миграции успели примениться, восстановите базу: sudo ./scripts/restore.sh $(latest_backup) --key <закрытый ключ копий>" >&2
    exit 1
}

main "$@"
