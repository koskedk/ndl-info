#!/usr/bin/env bash
# Creates the local settings the POC needs: .env and the keys for the stand-in S3 Ceph.
# Safe to run again: existing files are left alone. Nothing here is committed.
set -euo pipefail
POC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
mkdir -p "$POC_DIR/.secrets" "$POC_DIR/.data"
chmod 700 "$POC_DIR/.secrets"
rand() { python3 -c "import secrets; print(secrets.token_hex($1))"; }

if [[ ! -f "$POC_DIR/.env" ]]; then
  write_key="$(rand 10)"; write_secret="$(rand 20)"; read_key="$(rand 10)"; read_secret="$(rand 20)"
  cat > "$POC_DIR/.env" <<ENV
# Local settings for the POC. Not committed.
STANDIN_S3_PORT=8333

# The stand-in S3 Ceph, as pick-up and the explorer see it: a key that can only list and read.
STANDIN_S3_ENDPOINT=http://127.0.0.1:8333
STANDIN_S3_ACCESS_KEY=$read_key
STANDIN_S3_SECRET_KEY=$read_secret
STANDIN_S3_REGION=us-east-1
STANDIN_S3_BUCKETS=dha-analytics
STANDIN_S3_PATH_STYLE=true
STANDIN_S3_VERIFY_SSL=false

# The sampler's key, the only one that can write to the stand-in.
STANDIN_S3_WRITE_ACCESS_KEY=$write_key
STANDIN_S3_WRITE_SECRET_KEY=$write_secret
ENV
  chmod 600 "$POC_DIR/.env"
  echo "created .env"
fi

if [[ ! -f "$POC_DIR/.secrets/standin-s3.json" ]]; then
  set -a; . "$POC_DIR/.env"; set +a
  cat > "$POC_DIR/.secrets/standin-s3.json" <<JSON
{
  "identities": [
    {
      "name": "sampler",
      "credentials": [{"accessKey": "$STANDIN_S3_WRITE_ACCESS_KEY", "secretKey": "$STANDIN_S3_WRITE_SECRET_KEY"}],
      "actions": ["Admin", "Read", "Write", "List", "Tagging"]
    },
    {
      "name": "pickup",
      "credentials": [{"accessKey": "$STANDIN_S3_ACCESS_KEY", "secretKey": "$STANDIN_S3_SECRET_KEY"}],
      "actions": ["Read", "List"]
    }
  ]
}
JSON
  chmod 644 "$POC_DIR/.secrets/standin-s3.json"
  echo "created .secrets/standin-s3.json"
fi

if [[ ! -f "$POC_DIR/.secrets/hash_key" ]]; then
  rand 32 > "$POC_DIR/.secrets/hash_key"
  chmod 600 "$POC_DIR/.secrets/hash_key"
  echo "created .secrets/hash_key"
fi
