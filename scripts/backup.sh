#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

main() {
    local root file
    root="$(project_root)"
    cd "$root"
    load_env "$root"
    mkdir -p "$BACKUP_DIR"
    chmod 700 "$BACKUP_DIR"
    file="$BACKUP_DIR/dpo-$(TZ=Europe/Moscow date +%Y%m%d-%H%M%S).sql.gz"
    if ! write_dump "$file"; then
        rm -f "$file.part"
        echo "Ошибка: копия не создана." >&2
        exit 1
    fi
    prune
    echo "Готово: $file ($(du -h "$file" | cut -f1))"
}

write_dump() {
    dump > "$1.part" && gzip -t "$1.part" && mv "$1.part" "$1" && chmod 600 "$1"
}

dump() {
    db_shell mariadb-dump "--single-transaction --no-tablespaces --routines --default-character-set=utf8mb4" | gzip -9
}

prune() {
    find "$BACKUP_DIR" -maxdepth 1 -name 'dpo-*.sql.gz' -printf '%T@ %p\n' \
        | sort -rn | tail -n +"$((BACKUP_KEEP + 1))" | cut -d' ' -f2- | xargs -r rm -f --
}

main "$@"
