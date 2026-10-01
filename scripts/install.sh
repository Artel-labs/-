#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

PACKAGES=(git curl openssl iproute2)
DOCKER_PACKAGES=(docker.io docker-compose-v2)
REQUESTED_HTTP_PORT="${HTTP_PORT:-}"
REQUESTED_HTTPS_PORT="${HTTPS_PORT:-}"
PORT_PAIRS=("80 443" "8080 8443" "8081 8444" "8082 8445" "8083 8446")

main() {
    local root owner mode
    require_root "$@"
    root="$(project_root)"
    owner="${SUDO_USER:-root}"
    mode="$(choose_mode "${1:-}")"
    [[ $# -gt 0 ]] && shift
    validate_ports
    step "1/7" "Устанавливаем пакеты"
    install_packages
    step "2/7" "Даём пользователю ${owner} право запускать Docker"
    allow_docker "$owner"
    step "3/7" "Готовим файл настроек .env"
    prepare_env "$root" "$owner" "$@"
    load_env "$root"
    step "4/7" "Собираем и запускаем сайт на портах ${HTTP_PORT} (HTTP) и ${HTTPS_PORT} (HTTPS)"
    start_site "$root"
    step "5/7" "Создаём администратора"
    create_admin "$root"
    step "6/7" "Включаем ежедневную резервную копию"
    enable_backups "$root"
    step "7/7" "Режим работы: ${mode^^}"
    enable_mode "$root" "$mode" "$@"
    echo
    echo "Готово. Сайт: $(site_url "$mode")/  Админка: $(site_url "$mode")/admin/"
    echo "Логин и пароль администратора — выше, в шаге 5."
    echo "Если группа docker добавлена только что, перезайдите по SSH, чтобы запускать скрипты без sudo."
}

choose_mode() {
    case "$1" in
        --https | "") echo https ;;
        --http) echo http ;;
        *) echo "Неизвестный параметр: $1. Допустимо: --http или --https [домен-или-IP ...] (по умолчанию HTTPS)" >&2; exit 1 ;;
    esac
}

validate_ports() {
    local port
    for port in "$REQUESTED_HTTP_PORT" "$REQUESTED_HTTPS_PORT"; do
        if [[ -n "$port" && ! ( "$port" =~ ^[0-9]+$ && "$port" -ge 1 && "$port" -le 65535 ) ]]; then
            echo "Порт должен быть числом от 1 до 65535, получено: $port" >&2
            exit 1
        fi
    done
}

install_packages() {
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -q
    apt-get install -y -q "${PACKAGES[@]}"
    if docker compose version >/dev/null 2>&1; then
        echo "Docker и Compose уже установлены: $(docker compose version --short)"
    else
        apt-get install -y -q "${DOCKER_PACKAGES[@]}"
    fi
    systemctl enable --now docker 2>/dev/null || true
}

allow_docker() {
    if [[ "$1" != "root" ]]; then
        usermod -aG docker "$1"
    fi
}

prepare_env() {
    local root="$1" owner="$2" file="$1/.env"
    shift 2
    if [[ -f "$file" ]]; then
        echo "Файл .env уже есть — сохраняем его настройки."
    else
        (
            umask 077
            write_env "$file" "$@"
        )
        chown "$owner" "$file"
        echo "Создан $file (доступен только владельцу)."
    fi
    apply_requested_ports "$file"
    upgrade_env "$root"
}

apply_requested_ports() {
    if [[ -n "$REQUESTED_HTTP_PORT" ]]; then
        set_env_value "$1" HTTP_PORT "$REQUESTED_HTTP_PORT"
    fi
    if [[ -n "$REQUESTED_HTTPS_PORT" ]]; then
        set_env_value "$1" HTTPS_PORT "$REQUESTED_HTTPS_PORT"
    fi
}

port_free() {
    ! ss -ltnH "( sport = :$1 )" | grep -q .
}

free_port_pair() {
    local pair http https
    for pair in "${PORT_PAIRS[@]}"; do
        read -r http https <<< "$pair"
        if port_free "$http" && port_free "$https"; then
            echo "$pair"
            return 0
        fi
    done
    echo "Не нашлось свободных портов из списка: ${PORT_PAIRS[*]}. Укажите свои: sudo env HTTP_PORT=… HTTPS_PORT=… ./scripts/install.sh" >&2
    return 1
}

chosen_ports() {
    local http https
    read -r http https <<< "$(free_port_pair)"
    echo "${REQUESTED_HTTP_PORT:-$http} ${REQUESTED_HTTPS_PORT:-$https}"
}

write_env() {
    local file="$1" hosts name http https
    shift
    read -r http https <<< "$(chosen_ports)"
    hosts="$(server_ip),localhost,127.0.0.1"
    for name in "$@"; do
        hosts="$hosts,$name"
    done
    cat > "$file" <<ENV_FILE
DJANGO_SECRET_KEY=$(openssl rand -hex 32)
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=${hosts}
COOKIE_SECURE=0
DB_NAME=dpo
DB_USER=dpo
DB_PASSWORD=$(new_secret)
DB_ROOT_PASSWORD=$(new_secret)
HTTP_PORT=${http}
HTTPS_PORT=${https}
TLS_DIR=/etc/dpo/tls
BACKUP_DIR=/var/backups/dpo
BACKUP_KEEP=30
ENV_FILE
}

start_site() {
    cd "$1"
    require_free_ports
    echo "Скачиваем образы и собираем сайт. На медленном канале это займёт 5–10 минут — не прерывайте:"
    echo "при сбое сети скрипт сам повторит попытку."
    fetch_and_build
    docker compose up -d --wait db
    docker compose run --rm app python manage.py migrate --noinput
    docker compose run --rm app python manage.py seed_catalog
    docker compose up -d --remove-orphans
    wait_for_site
}

require_free_ports() {
    local port
    if [[ -n "$(docker compose ps -q web 2>/dev/null)" ]]; then
        return
    fi
    for port in "$HTTP_PORT" "$HTTPS_PORT"; do
        if ! port_free "$port"; then
            echo "Порт $port уже занят другой программой:" >&2
            ss -ltnpH "( sport = :$port )" >&2 || true
            echo "Укажите свободные порты, например: sudo env HTTP_PORT=8080 HTTPS_PORT=8443 ./scripts/install.sh" >&2
            exit 1
        fi
    done
}

create_admin() {
    "$1/scripts/create-admin.sh"
}

enable_backups() {
    if [[ -d /run/systemd/system ]]; then
        "$1/scripts/backup-timer.sh" install
    else
        echo "systemd не найден — таймер не включён. Копию можно делать вручную: sudo ./scripts/backup.sh"
    fi
}

enable_mode() {
    local root="$1" mode="$2"
    shift 2
    if [[ "$mode" == "https" ]]; then
        "$root/scripts/setup-https.sh" "$@"
    else
        echo "Сайт работает по HTTP. Включить HTTPS позже: sudo ./scripts/setup-https.sh [домен-или-IP ...]"
    fi
}

main "$@"
