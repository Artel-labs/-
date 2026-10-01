#!/bin/sh
set -e

STANDARD_HTTPS_PORT=443

https_suffix() {
    case "${HTTPS_PORT:-$STANDARD_HTTPS_PORT}" in
        "$STANDARD_HTTPS_PORT") echo "" ;;
        *[!0-9]* | "") echo "nginx: HTTPS_PORT должен быть числом" >&2; exit 1 ;;
        *) echo ":${HTTPS_PORT}" ;;
    esac
}

if [ -s /etc/nginx/tls/fullchain.pem ] && [ -s /etc/nginx/tls/privkey.pem ]; then
    suffix="$(https_suffix)"
    sed "s/__HTTPS_SUFFIX__/${suffix}/" /etc/nginx/available/https.conf > /etc/nginx/conf.d/default.conf
    echo "nginx: HTTPS включён (найден сертификат в /etc/nginx/tls)"
else
    cp /etc/nginx/available/http.conf /etc/nginx/conf.d/default.conf
    echo "nginx: работает по HTTP (сертификат не найден)"
fi
exec nginx -g 'daemon off;'
