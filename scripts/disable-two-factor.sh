#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

main() {
    cd "$(project_root)"
    require_env_file "$PWD"
    docker compose exec -T app python manage.py disable_two_factor "${1:-admin}"
}

main "$@"
