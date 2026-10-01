#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

CERT_DAYS=825

main() {
    local root
    require_root "$@"
    root="$(project_root)"
    cd "$root"
    load_env "$root"
    make_cert "$@"
    set_env_value "$root/.env" COOKIE_SECURE 1
    allow_hosts "$root/.env" "$@"
    step "3/3" "Перезапускаем сайт"
    docker compose up -d --force-recreate app web
    wait_for_site
    echo "Готово. HTTPS включён: https://$(server_ip)/"
    echo "Сертификат самоподписанный: браузер один раз предупредит. Для домена позже подключим Let's Encrypt."
}

make_cert() {
    local san="DNS:localhost,IP:127.0.0.1" name ip
    step "1/3" "Создаём самоподписанный сертификат в $TLS_DIR"
    mkdir -p "$TLS_DIR"
    chmod 700 "$TLS_DIR"
    for ip in $(hostname -I); do san="$san,IP:$ip"; done
    for name in "$@"; do
        if [[ "$name" =~ ^[0-9.]+$ ]]; then san="$san,IP:$name"; else san="$san,DNS:$name"; fi
    done
    openssl req -x509 -newkey rsa:2048 -nodes \
        -keyout "$TLS_DIR/privkey.pem" -out "$TLS_DIR/fullchain.pem" \
        -days "$CERT_DAYS" -subj "/CN=Центр ДПО" \
        -addext "subjectAltName=$san" \
        -addext "keyUsage=digitalSignature,keyEncipherment" \
        -addext "extendedKeyUsage=serverAuth" 2>/dev/null
    chmod 600 "$TLS_DIR/privkey.pem"
    chmod 644 "$TLS_DIR/fullchain.pem"
    echo "Адреса в сертификате: $san"
}

allow_hosts() {
    local file="$1" hosts name
    shift
    step "2/3" "Включаем защищённые cookie и обновляем список адресов"
    hosts="$(env_value "$file" DJANGO_ALLOWED_HOSTS "localhost,127.0.0.1")"
    for name in "$@"; do
        [[ ",$hosts," == *",$name,"* ]] || hosts="$hosts,$name"
    done
    set_env_value "$file" DJANGO_ALLOWED_HOSTS "$hosts"
}

main "$@"
