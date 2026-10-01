#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

main() {
    local branch="${1:-main}" root previous
    root="$(project_root)"
    cd "$root"
    load_env "$root"
    upgrade_env "$root"
    if [[ -d .git ]]; then
        previous="$(git rev-parse HEAD)"
        step "1/6" "Получаем ветку ${branch}"
        sync_branch "$branch"
        trap 'roll_back "$previous"' ERR
    else
        step "1/6" "Установка из архива: берём файлы из $root как есть"
        trap 'archive_failed' ERR
    fi
    step "2/6" "Собираем контейнеры"
    docker compose build
    step "3/6" "Резервная копия базы перед миграциями"
    as_root "$root/scripts/backup.sh"
    step "4/6" "Применяем миграции базы"
    docker compose run --rm app python manage.py migrate --noinput
    step "5/6" "Запускаем новую версию"
    docker compose up -d --remove-orphans
    step "6/6" "Проверяем, что сайт отвечает"
    wait_for_site
    trap - ERR
    echo "Готово: новая версия развёрнута."
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
    echo "восстановите базу из копии, сделанной перед миграциями: sudo ./scripts/restore.sh $(latest_backup)" >&2
    exit 1
}

archive_failed() {
    trap - ERR
    echo >&2
    echo "Ошибка развёртывания. Верните прошлую папку сайта (с файлом .env) и запустите deploy.sh в ней." >&2
    echo "Если миграции успели примениться, восстановите базу: sudo ./scripts/restore.sh $(latest_backup)" >&2
    exit 1
}

main "$@"
