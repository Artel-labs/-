#!/bin/sh
set -e
if [ -s /etc/nginx/tls/fullchain.pem ] && [ -s /etc/nginx/tls/privkey.pem ]; then
    cp /etc/nginx/available/https.conf /etc/nginx/conf.d/default.conf
    echo "nginx: HTTPS включён (найден сертификат в /etc/nginx/tls)"
else
    cp /etc/nginx/available/http.conf /etc/nginx/conf.d/default.conf
    echo "nginx: работает по HTTP (сертификат не найден)"
fi
exec nginx -g 'daemon off;'
