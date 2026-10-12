#!/bin/bash
set -e

DOMAIN="YOUR_DOMAIN"
EMAIL="YOUR_EMAIL"
COMPOSE="docker compose -f docker-compose.prod.yaml"

echo "### Creating dummy certificate for $DOMAIN..."
$COMPOSE run --rm --entrypoint "/bin/sh -c" certbot \
  "mkdir -p /etc/letsencrypt/live/$DOMAIN && \
   openssl req -x509 -nodes -newkey rsa:4096 -days 1 \
     -keyout /etc/letsencrypt/live/$DOMAIN/privkey.pem \
     -out /etc/letsencrypt/live/$DOMAIN/fullchain.pem \
     -subj '/CN=localhost'"

echo "### Downloading recommended TLS params..."
$COMPOSE run --rm --entrypoint "/bin/sh -c" certbot \
  "curl -sf https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf \
     -o /etc/letsencrypt/options-ssl-nginx.conf && \
   openssl dhparam -out /etc/letsencrypt/ssl-dhparams.pem 2048"

echo "### Starting nginx with dummy cert..."
$COMPOSE up -d nginx

echo "### Obtaining real certificate from Let's Encrypt..."
$COMPOSE run --rm certbot certonly \
  --webroot -w /var/www/certbot \
  --email "$EMAIL" \
  --agree-tos \
  --no-eff-email \
  -d "$DOMAIN"

echo "### Reloading nginx with real cert..."
$COMPOSE exec nginx nginx -s reload

echo "### Starting all services..."
$COMPOSE up -d

echo "### Done. SSL active for https://$DOMAIN"
