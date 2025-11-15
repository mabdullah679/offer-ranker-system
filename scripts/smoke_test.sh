#!/usr/bin/env bash
set -euo pipefail

BASE_URL=${1:-${SMOKE_TEST_BASE_URL:-}}
if [[ -z "${BASE_URL}" ]]; then
  echo "[smoke-test] Base URL not provided. Pass as argument or set SMOKE_TEST_BASE_URL." >&2
  exit 1
fi

log() {
  echo "[smoke-test] $1"
}

health_code=$(curl -s -o /tmp/health_response.txt -w "%{http_code}" "${BASE_URL}/health" || true)
if [[ "${health_code}" != "200" ]]; then
  log "Health check failed with status ${health_code}. Response: $(cat /tmp/health_response.txt)"
  exit 1
fi
log "Health check passed."

predict_payload='{"age":30,"tenure_months":12,"monthly_spend":123.4,"num_support_tickets":1}'
predict_code=$(curl -s -o /tmp/predict_response.txt -w "%{http_code}" \
  -X POST "${BASE_URL}/predict" \
  -H 'Content-Type: application/json' \
  -d "${predict_payload}" || true)
if [[ "${predict_code}" != "200" ]]; then
  log "Predict check failed with status ${predict_code}. Response: $(cat /tmp/predict_response.txt)"
  exit 1
fi
log "Predict check passed. Response: $(cat /tmp/predict_response.txt)"
log "Smoke tests completed successfully against ${BASE_URL}."
