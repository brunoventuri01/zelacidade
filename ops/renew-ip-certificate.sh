#!/usr/bin/env sh
set -eu

cd /opt/zelacidade
docker run --rm \
  -v /opt/zelacidade/certbot/conf:/etc/letsencrypt \
  -v /opt/zelacidade/certbot/www:/var/www/certbot \
  certbot/certbot:latest renew --quiet
docker compose exec -T proxy nginx -s reload
