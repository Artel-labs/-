#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

PACKAGES=(git curl openssl)
DOCKER_PACKAGES=(docker.io docker-compose-v2)

main() {
    local root owner mode
    require_root "$@"
    root="$(project_root)"
    owner="${SUDO_USER:-root}"
    mode="$(choose_mode "${1:-}")"
    [[ $# -gt 0 ]] && shift
    step "1/7" "Устанавливаем пакеты"
    install_packages
    step "2/7" "Даём пользователю ${owner} право запускать Docker"
    allow_docker "$owner"
    step "3/7" "Готовим файл настроек .env"
    prepare_env "$root" "$owner" "$@"
    load_env "$root"
    step "4/7" "Собираем и запускаем сайт"
    start_site "$root"
    step "5/7" "Создаём администратора"
    create_admin "$root"
    step "6/7" "Включаем ежедневную резервную копию"
    enable_backups "$root"
    step "7/7" "Режим работы: ${mode^^}"
    enable_mode "$root" "$mode" "$@"
    echo
    echo "Готово. Сайт: ${mode}://$(server_ip)/  Админка: ${mode}://$(server_ip)/admin/"
    echo "Если группа docker добавлена только что, перезайдите по SSH, чтобы запускать скрипты без sudo."
}

choose_mode() {
    case "$1" in
        --https) echo https ;;
        --http | "") echo http ;;
        *) echo "Неизвестный параметр: $1. Допустимо: --https [домен-или-IP ...] или --http" >&2; exit 1 ;;
    esac
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
        echo "Файл .env уже есть — оставляем его как есть."
        return
    fi
    (
        umask 077
        write_env "$file" "$@"
    )
    chown "$owner" "$file"
    echo "Создан $file (доступен только владельцу)."
}

write_env() {
    local file="$1" hosts name
    shift
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
DB_PASSWORD=$(openssl rand -hex 24)
HTTP_PORT=80
HTTPS_PORT=443
TLS_DIR=/etc/dpo/tls
BACKUP_DIR=/var/backups/dpo
BACKUP_KEEP=30
ENV_FILE
}

start_site() {
    cd "$1"
    docker compose build
    docker compose up -d --wait db
    docker compose run --rm app python manage.py migrate --noinput
    docker compose up -d --remove-orphans
    wait_for_site
}

create_admin() {
    if [[ -t 0 ]]; then
        "$1/scripts/create-admin.sh"
    else
        echo "Нет терминала для ввода пароля. Создайте администратора позже: ./scripts/create-admin.sh"
    fi
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
