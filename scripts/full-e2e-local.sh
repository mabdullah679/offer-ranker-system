#!/usr/bin/env bash
set -euo pipefail

# activate virtualenv
source "$(git rev-parse --show-toplevel)/.venv/bin/activate"

# ensure Docker is running
echo "[INIT] Checking Docker..."

if ! docker info >/dev/null 2>&1; then
    echo "[INIT] Docker is not running. Starting Docker Desktop..."
    open -a Docker

    echo "[INIT] Waiting for Docker to start..."
    # retry for up to ~60 seconds
    for i in {1..30}; do
        if docker info >/dev/null 2>&1; then
            echo "[INIT] Docker is ready."
            break
        fi
        sleep 2
    done

    # after waiting, if still not ready, fail gracefully
    if ! docker info >/dev/null 2>&1; then
        echo "[ERROR] Docker failed to start after waiting. Aborting."
        exit 1
    fi
else
    echo "[INIT] Docker is already running."
fi

echo "[E2E] starting from repo root"
cd "$(git rev-parse --show-toplevel)"

########################################
# STEP 1: Data Quality (Project 3)
########################################
echo "[STEP 1] Running Data Quality validation"

python dq/dq_cli.py validate training/data/customers.csv \
  --config dq/dq_rules.yaml

echo "[STEP 1] PASS: DQ validation succeeded"

########################################
# STEP 2: Training notebook (Project 2)
########################################
echo "[STEP 2] Executing training notebook"

cd training
jupyter nbconvert --to notebook --execute customer_upsell_propensity.ipynb \
  --output customer_upsell_propensity.out.ipynb
cd ..

if ! ls training/models/*.joblib > /dev/null 2>&1; then
  echo "[STEP 2] FAIL: No model artifact found"
  exit 1
fi

echo "[STEP 2] PASS: Model artifact found"

########################################
# STEP 3: API smoke test in Docker (Project 1)
########################################
echo "[STEP 3] Build the OfferRanker API Docker image"
cd api
docker build -t offer-ranker-api:e2e .

echo "[STEP 3] Run container"
docker run -d --rm -p 8000:8080 --name offer-ranker-api-e2e offer-ranker-api:e2e
sleep 5

echo "[STEP 3] Health check:"
curl -s http://localhost:8000/health
echo

echo "[STEP 3] Prediction check:"
curl -s http://localhost:8000/predict \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"age":30,"tenure_months":24,"monthly_spend":120,"num_support_tickets":1}'
echo

docker stop offer-ranker-api-e2e || true
cd ..

########################################
# CLEANUP (important: no leftover artifacts)
########################################
echo "[CLEANUP] Removing DQ reports"
rm -f dq/reports/*.txt dq/reports/*.json

echo "[CLEANUP] Removing training artifacts"
rm -f training/customer_upsell_propensity.out.ipynb
rm -f training/models/*.joblib training/models/*.json

echo "[E2E] Complete. All temporary artifacts wiped."
