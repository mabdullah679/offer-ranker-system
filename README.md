# Offer Ranker API

Production-style FastAPI service for upsell predictions with deterministic training, containerization, Terraform IaC, CI/CD, and orchestration helpers.

## Requirements

- Python 3.11+ (tested with 3.12)
- Docker
- Terraform ≥ 1.5
- Make

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Training

- `make train`
- or `python orchestrate.py train`

Outputs `models/offer_model.joblib`.

## Running the API locally

- `make run-local`
- or `python orchestrate.py api:local`

Then `curl http://localhost:8080/health` or send a POST to `/predict`.

## Testing

- `make test`
- or `python orchestrate.py test`

## Docker

- Build: `make docker-build`
- Run: `make docker-run` (respects `$PORT`, defaults to 8080)

Or via orchestrator:
- `python orchestrate.py docker:build`
- `python orchestrate.py docker:run`

## Smoke tests

Run `./scripts/smoke_test.sh https://your-service-url` or `python orchestrate.py smoke-test --url https://...`.

## Terraform

1. Copy `infrastructure/terraform.tfvars.example` → `terraform.tfvars` and fill:
   - `project_id`
   - `region`
   - `service_name`
   - `image`
   - `service_account_email`
2. Use orchestrator:
   - `python orchestrate.py tf:init`
   - `python orchestrate.py tf:plan`
   - `python orchestrate.py tf:apply` (prompts `y/N` before running `terraform apply -auto-approve`)

## CI/CD

### `.github/workflows/ci.yml`
- Trigger: push / PR to `main`.
- Installs deps, runs tests, builds Docker image, pushes to Artifact Registry.
- Runs `terraform init` and `terraform plan` (no apply) and uploads plan artifacts.
- Requires secrets:
  - `GCP_SERVICE_ACCOUNT_KEY`
  - `GCP_PROJECT_ID`
  - `GCP_REGION`
  - `CLOUD_RUN_SERVICE_NAME`
  - `ARTIFACT_REGISTRY_REPO`
  - `CLOUD_RUN_SERVICE_ACCOUNT`

### `.github/workflows/deploy.yml`
- Manual `workflow_dispatch` only.
- Authenticates to GCP, runs `terraform apply -auto-approve`, captures Cloud Run URL, runs `scripts/smoke_test.sh`.
- This is the only workflow allowed to apply Terraform.

## Master Orchestrator (`orchestrate.py`)

Subcommands:
- `train`
- `api:local`
- `test`
- `docker:build`
- `docker:run`
- `tf:init`
- `tf:plan`
- `tf:apply` (with confirmation)
- `deploy` (tests + Docker build + Terraform plan guidance)
- `smoke-test --url <base_url>`

Each step writes logs to `/tmp/offer_ranker_logs/<timestamp>/<step>.log`.

## MVP Checklist

- [x] `make train` produces `models/offer_model.joblib`.
- [x] `make run-local` serves FastAPI; `/health` and `/predict` respond.
- [x] `pytest` passes.
- [x] `docker build` + `docker run` work using `$PORT`.
- [x] GitHub Actions `ci` workflow builds/tests image and runs Terraform plan.
- [x] `deploy` workflow (manual) applies Terraform and runs smoke tests.
