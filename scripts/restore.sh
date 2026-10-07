#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

CONFIRM_WORD=ВОССТАНОВИТЬ
WORK_FILE=""
WORK_MEDIA=""
ASSUME_YES=""
PRIVATE_KEY=""

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
    shift
    read_options "$@"
    [[ -f "$file" ]] || { echo "Файл не найден: $file" >&2; exit 1; }
    WORK_FILE="$(mktemp)"
    WORK_MEDIA="$(mktemp)"
    trap 'rm -f "$WORK_FILE" "$WORK_MEDIA"' EXIT
    unpack "$file" "$WORK_FILE" || { echo "Файл повреждён или ключ не подходит: $file" >&2; exit 1; }
    copy_media_archive "$file"
    confirm
    echo "[1/5] Сохраняем текущую базу на всякий случай"
    "$root/scripts/backup.sh"
    echo "[2/5] Останавливаем приложение"
    docker compose stop app
    trap 'on_failure' ERR
    echo "[3/5] Восстанавливаем базу из $file"
    drop_tables
    gunzip -c "$WORK_FILE" | db_shell mariadb
    restore_media
    trap - ERR
    echo "[4/5] Применяем миграции"
    docker compose run --rm app python manage.py migrate --noinput
    echo "[5/5] Удаляем данные с истёкшим сроком хранения и запускаем приложение"
    docker compose run --rm app python manage.py purge_expired
    docker compose start app
    wait_for_site
    echo "Готово: база восстановлена из $(basename "$file")."
}

read_options() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --yes) ASSUME_YES=1 ;;
            --key) PRIVATE_KEY="${2:-}"; shift ;;
            *) echo "Неизвестный параметр: $1" >&2; show_usage; exit 1 ;;
        esac
        shift
    done
}

unpack() {
    if is_encrypted "$1"; then
        require_private_key
        decrypt_to "$PRIVATE_KEY" "$1" "$2" 2>/dev/null || return 1
    else
        cp "$1" "$2"
    fi
    gzip -t "$2"
}

require_private_key() {
    if [[ -z "$PRIVATE_KEY" || ! -f "$PRIVATE_KEY" ]]; then
        echo "Копия зашифрована. Укажите закрытый ключ: sudo ./scripts/restore.sh <файл копии> --key <файл ключа>" >&2
        exit 1
    fi
}

copy_media_archive() {
    local archive
    archive="$(media_archive "$1")"
    if [[ -f "$archive" ]]; then
        unpack "$archive" "$WORK_MEDIA" || { echo "Архив файлов повреждён или ключ не подходит: $archive" >&2; exit 1; }
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
    echo "Использование: sudo ./scripts/restore.sh <файл копии> --key <закрытый ключ> [--yes]"
    echo "Доступные копии (новые сверху):"
    find "$BACKUP_DIR" -maxdepth 1 -name "$DB_BACKUP_PATTERN" -printf '%T@ %p\n' 2>/dev/null \
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
    if [[ -n "$ASSUME_YES" ]]; then
        return
    fi
    echo "Текущие данные сайта будут заменены данными из копии."
    read -r -p "Чтобы продолжить, введите ${CONFIRM_WORD}: " answer
    [[ "$answer" == "$CONFIRM_WORD" ]] || { echo "Отменено."; exit 1; }
}

main "$@"
