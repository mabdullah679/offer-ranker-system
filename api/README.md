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

Workflows in `.github/workflows/` (checked against the files, 2026-11-18):

- `pr-checks.yml` – runs on pull requests and pushes to `main`, free runners, no cloud credentials: `pytest` in `api/`, `docker build`, gitleaks.
- `ci.yml` – push to `dev` (only when the commit message contains `ci-cd`) or manual. Runs pytest, optional data-quality check, pip-audit, builds the image, Trivy scan (non-blocking), pushes to Artifact Registry. Needs GCP secrets.
- `cd.yml` – after `ci` succeeds on `dev`, or manual. Deploys the image to Cloud Run, smoke-tests it, rolls back on failure.
- `cd_dispatch.yml` – manual Cloud Run deploy.
- `ci-cd.yml` – manual build, push and `terraform apply`.
- `destroy.yml` – manual teardown of the Cloud Run service and Artifact Registry repo.

Secrets used by the cloud workflows: `GCP_SA_KEY`, `GCP_PROJECT_ID`, `GCP_REGION`, `GCS_MODEL_BUCKET`.

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
- [x] GitHub Actions `ci` workflow tests, builds and pushes the image; `ci-cd.yml` (manual) applies Terraform.
