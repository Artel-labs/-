#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

MINUTES_IN_DAY=1440
MEDIA_BACKUP_PATTERN="dpo-*.media.tar.gz*"

main() {
    local root base
    root="$(project_root)"
    cd "$root"
    load_env "$root"
    ensure_backup_key
    mkdir -p "$BACKUP_DIR"
    chmod 700 "$BACKUP_DIR"
    base="$BACKUP_DIR/dpo-$(TZ=Europe/Moscow date +%Y%m%d-%H%M%S).sql.gz$ENCRYPTED_SUFFIX"
    if ! write_backup "$base"; then
        rm -f "$base" "$base.part" "$(media_archive "$base")" "$(media_archive "$base").part"
        echo "Ошибка: копия не создана." >&2
        exit 1
    fi
    prune "$DB_BACKUP_PATTERN"
    prune "$MEDIA_BACKUP_PATTERN"
    echo "Готово: $base ($(du -h "$base" | cut -f1)), файлы сайта: $(du -h "$(media_archive "$base")" | cut -f1). Копия зашифрована."
    warn_private_key_left
}

write_backup() {
    save_encrypted "$1" dump && save_encrypted "$(media_archive "$1")" pack_media
}

save_encrypted() {
    local file="$1"
    shift
    "$@" | encrypt_stream > "$file.part" && check_encrypted "$file.part" && mv "$file.part" "$file" && chmod 600 "$file"
}

dump() {
    db_shell mariadb-dump "--single-transaction --no-tablespaces --routines --default-character-set=utf8mb4" | gzip -9
}

pack_media() {
    docker compose run --rm --no-deps -T app tar -C "$MEDIA_DIR" -czf - .
}

prune() {
    find "$BACKUP_DIR" -maxdepth 1 -name "$1" -mmin +"$((BACKUP_MAX_AGE_DAYS * MINUTES_IN_DAY))" -delete
    find "$BACKUP_DIR" -maxdepth 1 -name "$1" -printf '%T@ %p\n' \
        | sort -rn | tail -n +"$((BACKUP_KEEP + 1))" | cut -d' ' -f2- | xargs -r rm -f --
}

main "$@"
