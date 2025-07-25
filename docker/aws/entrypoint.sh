#!/bin/bash
set -e

echo "Starting Jupyter Lab..."
jupyter lab --ServerApp.ip=0.0.0.0 \
  --ServerApp.allow_remote_access=True \
  --ServerApp.allow_origin='*' \
  --ServerApp.identity_provider_class="jupyter_server.auth.identity.PasswordIdentityProvider" \
  --PasswordIdentityProvider.hashed_password='argon2:$argon2id$v=19$m=10240,t=10,p=8$jarNdnLzxbBMZknYR35n1A$7AihqKDInHAvY/57vnbn/UnyQRaYenWsZ0HlDBWMqn0' \
  --notebook-dir=/app/ \
  --preferred-dir=/app \
  --port=9000