#!/usr/bin/env bash

HEALTH_ATTEMPTS=30
HEALTH_DELAY_SECONDS=2
DEFAULT_HTTP_PORT=80
DEFAULT_HTTPS_PORT=443
SECRET_BYTES=24
NETWORK_ATTEMPTS=5
NETWORK_DELAY_SECONDS=10
PULLED_SERVICES=(db)
export MEDIA_DIR=/app/media

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
    HTTP_PORT="$(env_value "$file" HTTP_PORT "$DEFAULT_HTTP_PORT")"
    HTTPS_PORT="$(env_value "$file" HTTPS_PORT "$DEFAULT_HTTPS_PORT")"
    TLS_DIR="$(env_value "$file" TLS_DIR /etc/dpo/tls)"
    BACKUP_DIR="$(env_value "$file" BACKUP_DIR /var/backups/dpo)"
    BACKUP_KEEP="$(env_value "$file" BACKUP_KEEP 30)"
    COOKIE_SECURE="$(env_value "$file" COOKIE_SECURE 0)"
    export HTTP_PORT HTTPS_PORT TLS_DIR BACKUP_DIR BACKUP_KEEP COOKIE_SECURE
}

new_secret() {
    openssl rand -hex "$SECRET_BYTES"
}

ensure_env_secret() {
    if ! grep -qE "^$2=" "$1"; then
        set_env_value "$1" "$2" "$(new_secret)"
        echo "В .env добавлен недостающий $2."
    fi
}

upgrade_env() {
    ensure_env_secret "$1/.env" DB_ROOT_PASSWORD
}

port_suffix() {
    if [[ "$1" == "$2" ]]; then
        echo ""
    else
        echo ":$1"
    fi
}

site_url() {
    if [[ "$1" == "https" ]]; then
        echo "https://$(server_ip)$(port_suffix "$HTTPS_PORT" "$DEFAULT_HTTPS_PORT")"
    else
        echo "http://$(server_ip)$(port_suffix "$HTTP_PORT" "$DEFAULT_HTTP_PORT")"
    fi
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
    if [[ "$COOKIE_SECURE" == "1" ]]; then
        curl -fsSk --max-time 5 "https://127.0.0.1:${HTTPS_PORT}/api/health" 2>/dev/null
    else
        curl -fsS --max-time 5 "http://127.0.0.1:${HTTP_PORT}/api/health" 2>/dev/null
    fi
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

with_retries() {
    local attempt
    for attempt in $(seq 1 "$NETWORK_ATTEMPTS"); do
        if "$@"; then
            return 0
        fi
        echo "Не получилось (попытка $attempt из $NETWORK_ATTEMPTS). Похоже на сбой сети, повторяем через ${NETWORK_DELAY_SECONDS} с." >&2
        sleep "$NETWORK_DELAY_SECONDS"
    done
    echo "Не удалось после $NETWORK_ATTEMPTS попыток. Проверьте, что сервер видит Docker Hub и npm." >&2
    return 1
}

missing_images() {
    local image
    for image in $(docker compose config --images "${PULLED_SERVICES[@]}"); do
        docker image inspect "$image" >/dev/null 2>&1 || echo "$image"
    done
}

fetch_and_build() {
    local image
    for image in $(missing_images); do
        with_retries docker pull "$image"
    done
    with_retries docker compose build
}

db_shell() {
    docker compose exec -T db sh -c "MYSQL_PWD=\"\$MARIADB_PASSWORD\" $1 -u\"\$MARIADB_USER\" ${2:-} \"\$MARIADB_DATABASE\""
}

media_archive() {
    echo "${1%.sql.gz}.media.tar.gz"
}

latest_backup() {
    find "${BACKUP_DIR:-/var/backups/dpo}" -maxdepth 1 -name 'dpo-*.sql.gz' -printf '%T@ %p\n' 2>/dev/null \
        | sort -rn | head -n 1 | cut -d' ' -f2-
}
