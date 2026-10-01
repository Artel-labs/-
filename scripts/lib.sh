#!/usr/bin/env bash

HEALTH_ATTEMPTS=30
HEALTH_DELAY_SECONDS=2

project_root() {
    cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd
}

step() {
    echo
    echo "[$1] $2"
}

env_value() {
    local value
    value="$(grep -E "^$2=" "$1" 2>/dev/null | tail -n 1 | cut -d= -f2- || true)"
    echo "${value:-$3}"
}

set_env_value() {
    local file="$1" key="$2" value="$3"
    if grep -qE "^$key=" "$file"; then
        sed -i "s|^$key=.*|$key=$value|" "$file"
    else
        printf '%s=%s\n' "$key" "$value" >> "$file"
    fi
}

require_env_file() {
    if [[ ! -f "$1/.env" ]]; then
        echo "Нет файла .env в $1. Сначала запустите: sudo ./scripts/install.sh" >&2
        exit 1
    fi
}

load_env() {
    local file="$1/.env"
    require_env_file "$1"
    HTTP_PORT="$(env_value "$file" HTTP_PORT 80)"
    HTTPS_PORT="$(env_value "$file" HTTPS_PORT 443)"
    TLS_DIR="$(env_value "$file" TLS_DIR /etc/dpo/tls)"
    BACKUP_DIR="$(env_value "$file" BACKUP_DIR /var/backups/dpo)"
    BACKUP_KEEP="$(env_value "$file" BACKUP_KEEP 30)"
    export HTTP_PORT HTTPS_PORT TLS_DIR BACKUP_DIR BACKUP_KEEP
}

as_root() {
    if [[ $EUID -eq 0 ]]; then
        "$@"
    else
        sudo "$@"
    fi
}

require_root() {
    if [[ $EUID -ne 0 ]]; then
        echo "Запустите через sudo: sudo $0 $*" >&2
        exit 1
    fi
}

server_ip() {
    hostname -I | awk '{print $1}'
}

site_health() {
    curl -fsSk --max-time 5 "https://127.0.0.1:${HTTPS_PORT}/api/health" 2>/dev/null \
        || curl -fsS --max-time 5 "http://127.0.0.1:${HTTP_PORT}/api/health" 2>/dev/null
}

wait_for_site() {
    local _
    for _ in $(seq 1 "$HEALTH_ATTEMPTS"); do
        if site_health; then
            echo
            return 0
        fi
        sleep "$HEALTH_DELAY_SECONDS"
    done
    echo "Сайт не ответил за $((HEALTH_ATTEMPTS * HEALTH_DELAY_SECONDS)) секунд. Логи: docker compose logs --tail=50" >&2
    return 1
}

db_shell() {
    docker compose exec -T db sh -c "MYSQL_PWD=\"\$MARIADB_PASSWORD\" $1 -u\"\$MARIADB_USER\" ${2:-} \"\$MARIADB_DATABASE\""
}

latest_backup() {
    find "${BACKUP_DIR:-/var/backups/dpo}" -maxdepth 1 -name 'dpo-*.sql.gz' -printf '%T@ %p\n' 2>/dev/null \
        | sort -rn | head -n 1 | cut -d' ' -f2-
}
