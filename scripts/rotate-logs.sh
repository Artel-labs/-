#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

DEFAULT_LOG_RETENTION_DAYS=90
SECONDS_IN_DAY=86400
SITE_SERVICES=(web site app worker)
STATE_DIR=/var/lib/dpo
MARKER="$STATE_DIR/logs-rotated"

main() {
    local root days
    require_root "$@"
    root="$(project_root)"
    load_env "$root"
    days="$(env_value "$root/.env" LOG_RETENTION_DAYS "$DEFAULT_LOG_RETENTION_DAYS")"
    if [[ "${1:-}" != "--now" ]] && rotated_recently "$days"; then
        return
    fi
    cd "$root"
    docker compose up -d --force-recreate --no-deps "${SITE_SERVICES[@]}"
    wait_for_site
    mkdir -p "$STATE_DIR"
    touch "$MARKER"
    echo "Контейнеры сайта пересозданы, их прежние журналы удалены. Следующий раз — не позже чем через $days дн."
}

rotated_recently() {
    local age
    [[ -f "$MARKER" ]] || return 1
    age=$(( $(date +%s) - $(stat -c %Y "$MARKER") ))
    (( age < ($1 - 1) * SECONDS_IN_DAY ))
}

main "$@"
