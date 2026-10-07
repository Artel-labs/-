#!/usr/bin/env bash
set -Eeuo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

UNIT=dpo-backup

main() {
    local root
    require_root "$@"
    root="$(project_root)"
    case "${1:-install}" in
        install) install_timer "$root" ;;
        remove) remove_timer ;;
        status) systemctl list-timers "$UNIT.timer" --no-pager ;;
        *) echo "Использование: sudo ./scripts/backup-timer.sh [install|remove|status]" >&2; exit 1 ;;
    esac
}

install_timer() {
    cat > "/etc/systemd/system/$UNIT.service" <<UNIT_FILE
[Unit]
Description=Резервная копия базы сайта Центра ДПО, очистка истёкших сессий и старых журналов
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
ExecStart=$1/scripts/backup.sh
ExecStart=-$1/scripts/clean-sessions.sh
ExecStart=-$1/scripts/rotate-logs.sh
PrivateTmp=true
NoNewPrivileges=true
UNIT_FILE
    cat > "/etc/systemd/system/$UNIT.timer" <<UNIT_FILE
[Unit]
Description=Ежедневная резервная копия сайта Центра ДПО в 03:00 по Москве

[Timer]
OnCalendar=*-*-* 03:00:00 Europe/Moscow
Persistent=true

[Install]
WantedBy=timers.target
UNIT_FILE
    systemctl daemon-reload
    systemctl enable --now "$UNIT.timer"
    echo "Таймер включён: копия каждый день в 03:00 по Москве."
    systemctl list-timers "$UNIT.timer" --no-pager
}

remove_timer() {
    systemctl disable --now "$UNIT.timer" 2>/dev/null || true
    rm -f "/etc/systemd/system/$UNIT.service" "/etc/systemd/system/$UNIT.timer"
    systemctl daemon-reload
    echo "Таймер резервного копирования отключён."
}

main "$@"
