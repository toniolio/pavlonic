#!/usr/bin/env bash

set -euo pipefail

API_HOST="127.0.0.1"
API_PORT="8000"
WEB_HOST="127.0.0.1"
WEB_PORT="8001"

API_URL="http://${API_HOST}:${API_PORT}/v1/studies/0001"
WEB_URL="http://${WEB_HOST}:${WEB_PORT}/"

cleanup() {
  if [[ -n "${API_PID:-}" ]]; then
    kill "${API_PID}" >/dev/null 2>&1 || true
  fi
  if [[ -n "${WEB_PID:-}" ]]; then
    kill "${WEB_PID}" >/dev/null 2>&1 || true
  fi
}

trap cleanup INT TERM EXIT

uvicorn apps.api.main:app --reload --host "${API_HOST}" --port "${API_PORT}" &
API_PID=$!

python -m http.server --directory apps/web "${WEB_PORT}" --bind "${WEB_HOST}" &
WEB_PID=$!

printf '\nLocal dev servers started:\n'
printf 'API: %s\n' "${API_URL}"
printf 'Web: %s\n\n' "${WEB_URL}"

wait "${API_PID}" "${WEB_PID}"
