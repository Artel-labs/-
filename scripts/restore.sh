#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

CONFIRM_WORD=ВОССТАНОВИТЬ
WORK_FILE=""
WORK_MEDIA=""

main() {
    local root file
    root="$(project_root)"
    cd "$root"
    load_env "$root"
    file="${1:-}"
    if [[ -z "$file" ]]; then
        show_usage
        exit 1
    fi
    [[ -f "$file" ]] || { echo "Файл не найден: $file" >&2; exit 1; }
    gzip -t "$file" || { echo "Файл повреждён: $file" >&2; exit 1; }
    confirm "${2:-}"
    WORK_FILE="$(mktemp)"
    WORK_MEDIA="$(mktemp)"
    trap 'rm -f "$WORK_FILE" "$WORK_MEDIA"' EXIT
    cp "$file" "$WORK_FILE"
    copy_media_archive "$file"
    echo "[1/4] Сохраняем текущую базу на всякий случай"
    "$root/scripts/backup.sh"
    echo "[2/4] Останавливаем приложение"
    docker compose stop app
    trap 'on_failure' ERR
    echo "[3/4] Восстанавливаем базу из $file"
    drop_tables
    gunzip -c "$WORK_FILE" | db_shell mariadb
    restore_media
    trap - ERR
    echo "[4/4] Запускаем приложение и применяем миграции"
    docker compose run --rm app python manage.py migrate --noinput
    docker compose start app
    wait_for_site
    echo "Готово: база восстановлена из $(basename "$file")."
}

copy_media_archive() {
    local archive
    archive="$(media_archive "$1")"
    if [[ -f "$archive" ]]; then
        gzip -t "$archive" || { echo "Архив файлов повреждён: $archive" >&2; exit 1; }
        cp "$archive" "$WORK_MEDIA"
    else
        echo "Архива файлов сайта рядом с копией нет — восстанавливаем только базу."
        : > "$WORK_MEDIA"
    fi
}

restore_media() {
    if [[ -s "$WORK_MEDIA" ]]; then
        echo "Восстанавливаем файлы сайта (обложки, фото, документы)"
        docker compose run --rm --no-deps -T app sh -c "find $MEDIA_DIR -mindepth 1 -delete && tar -C $MEDIA_DIR -xzf -" < "$WORK_MEDIA"
    fi
}

show_usage() {
    echo "Использование: sudo ./scripts/restore.sh <файл копии> [--yes]"
    echo "Доступные копии (новые сверху):"
    find "$BACKUP_DIR" -maxdepth 1 -name 'dpo-*.sql.gz' -printf '%T@ %p\n' 2>/dev/null \
        | sort -rn | head -n 10 | cut -d' ' -f2- | sed 's/^/  /'
}

drop_tables() {
    local tables
    tables="$(echo "SET SESSION group_concat_max_len = 1000000; SELECT GROUP_CONCAT(CONCAT('\`', table_name, '\`')) FROM information_schema.tables WHERE table_schema = DATABASE();" | db_shell mariadb -N)"
    if [[ -n "$tables" && "$tables" != "NULL" ]]; then
        echo "SET FOREIGN_KEY_CHECKS = 0; DROP TABLE $tables; SET FOREIGN_KEY_CHECKS = 1;" | db_shell mariadb
    fi
}

on_failure() {
    echo "Ошибка восстановления. Запускаем приложение обратно; копия текущей базы сделана на шаге 1." >&2
    docker compose start app || true
}

confirm() {
    local answer
    if [[ "$1" == "--yes" ]]; then
        return
    fi
    echo "Текущие данные сайта будут заменены данными из копии."
    read -r -p "Чтобы продолжить, введите ${CONFIRM_WORD}: " answer
    [[ "$answer" == "$CONFIRM_WORD" ]] || { echo "Отменено."; exit 1; }
}

main "$@"
