#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

main() {
    cd "$(project_root)"
    require_env_file "$PWD"
    echo "Введите логин, почту и пароль администратора (пароль не короче 12 символов)."
    docker compose exec app python manage.py createsuperuser
}

main "$@"
