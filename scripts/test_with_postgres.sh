#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

DOCKER_CONTAINER_NAME=""
DOCKER_STARTED="false"

cleanup() {
  if [[ "$DOCKER_STARTED" == "true" && -n "$DOCKER_CONTAINER_NAME" ]]; then
    docker rm -f "$DOCKER_CONTAINER_NAME" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

ensure_poetry_python() {
  if poetry run python - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if sys.version_info[:2] == (3, 13) else 1)
PY
  then
    return 0
  fi

  local py313=""
  if command -v python3.13 >/dev/null 2>&1; then
    py313="$(command -v python3.13)"
  elif command -v python3 >/dev/null 2>&1 && python3 - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if sys.version_info[:2] == (3, 13) else 1)
PY
  then
    py313="$(command -v python3)"
  fi

  if [[ -z "$py313" ]]; then
    echo "ERROR: Python 3.13 is required by this project but was not found." >&2
    echo "Install Python 3.13, then run: poetry env use python3.13" >&2
    return 1
  fi

  echo "Switching Poetry environment to Python 3.13: ${py313}" >&2
  poetry env use "$py313" >/dev/null
}

ensure_poetry_python

find_free_port() {
  poetry run python - <<'PY'
import socket
s = socket.socket()
s.bind(("127.0.0.1", 0))
print(s.getsockname()[1])
s.close()
PY
}

can_connect_url() {
  local db_url="$1"
  TEST_URL="$db_url" poetry run python - <<'PY' >/dev/null 2>&1
import os
import psycopg2

url = os.environ["TEST_URL"]
conn = psycopg2.connect(url)
conn.close()
PY
}

ensure_db_url() {
  if [[ -n "${TEST_POSTGRES_URL:-}" ]]; then
    if ! can_connect_url "$TEST_POSTGRES_URL"; then
      echo "ERROR: TEST_POSTGRES_URL is set but not reachable: $TEST_POSTGRES_URL" >&2
      return 1
    fi
    echo "$TEST_POSTGRES_URL"
    return 0
  fi

  if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: TEST_POSTGRES_URL is not set and docker is not installed." >&2
    echo "Set TEST_POSTGRES_URL or install/start Docker." >&2
    return 1
  fi

  local host_port
  host_port="$(find_free_port)"
  DOCKER_CONTAINER_NAME="enrichment-test-pg-${host_port}"

  docker run --rm -d \
    --name "$DOCKER_CONTAINER_NAME" \
    -e POSTGRES_PASSWORD=postgres \
    -e POSTGRES_DB=testdb \
    -p "${host_port}:5432" \
    postgres:16-alpine >/dev/null

  DOCKER_STARTED="true"

  local docker_url="postgresql://postgres:postgres@127.0.0.1:${host_port}/testdb"

  local attempts=60
  while (( attempts > 0 )); do
    if docker exec "$DOCKER_CONTAINER_NAME" pg_isready -U postgres -d testdb >/dev/null 2>&1; then
      echo "$docker_url"
      return 0
    fi
    attempts=$((attempts - 1))
    sleep 0.5
  done

  echo "ERROR: Docker Postgres did not become ready in time." >&2
  return 1
}

DB_URL="$(ensure_db_url)"

echo "Running tests with PostgreSQL at ${DB_URL}" >&2
TEST_POSTGRES_URL="$DB_URL" PYTHONPATH=src poetry run pytest "$@"
