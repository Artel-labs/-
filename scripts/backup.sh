#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

main() {
    local root base
    root="$(project_root)"
    cd "$root"
    load_env "$root"
    mkdir -p "$BACKUP_DIR"
    chmod 700 "$BACKUP_DIR"
    base="$BACKUP_DIR/dpo-$(TZ=Europe/Moscow date +%Y%m%d-%H%M%S)"
    if ! write_backup "$base"; then
        rm -f "$base.sql.gz" "$base.sql.gz.part" "$(media_archive "$base.sql.gz")" "$(media_archive "$base.sql.gz").part"
        echo "Ошибка: копия не создана." >&2
        exit 1
    fi
    prune 'dpo-*.sql.gz'
    prune 'dpo-*.media.tar.gz'
    echo "Готово: $base.sql.gz ($(du -h "$base.sql.gz" | cut -f1)), файлы сайта: $(du -h "$(media_archive "$base.sql.gz")" | cut -f1)"
}

write_backup() {
    save_checked "$1.sql.gz" dump && save_checked "$(media_archive "$1.sql.gz")" pack_media
}

save_checked() {
    local file="$1"
    shift
    "$@" > "$file.part" && gzip -t "$file.part" && mv "$file.part" "$file" && chmod 600 "$file"
}

dump() {
    db_shell mariadb-dump "--single-transaction --no-tablespaces --routines --default-character-set=utf8mb4" | gzip -9
}

pack_media() {
    docker compose run --rm --no-deps -T app tar -C "$MEDIA_DIR" -czf - .
}

prune() {
    find "$BACKUP_DIR" -maxdepth 1 -name "$1" -printf '%T@ %p\n' \
        | sort -rn | tail -n +"$((BACKUP_KEEP + 1))" | cut -d' ' -f2- | xargs -r rm -f --
}

main "$@"
