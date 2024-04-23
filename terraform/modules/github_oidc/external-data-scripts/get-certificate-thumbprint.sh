#!/bin/bash

set -e
set -o pipefail

eval "$(jq -r '@sh "HOST=\(.host)"')"

THUMBPRINT="$(openssl s_client -connect "$HOST:443" < /dev/null 2>/dev/null | \
  openssl x509 -fingerprint -noout -in /dev/stdin | \
  cut -f2 -d'=' | \
  tr -d ':' | \
  tr '[:upper:]' '[:lower:]'
)"

jq -ncr --arg thumbprint "$THUMBPRINT" \
  '{
    thumbprint: $thumbprint
  }'
