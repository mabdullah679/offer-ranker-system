# Model Registry & Versioned Promotion

## Goal
Track models by version with immutable artifacts and metrics, and deploy by version tag instead of ad-hoc files.

## Scope (MVP)
- Registry: MLflow serverless (local file/GCS backend) or GCS bucket with metadata JSON per version (`version`, `artifact_uri`, `metrics`, `params`, `created_at`, `stage`).
- CI: on successful build/test, publish model metadata + artifact to registry and tag image with model version.
- CD: deploy image parameterized by model version; store model version in container env/metadata.
- API: surface `/info` endpoint with deployed model version and hash.

## Steps
1) Create registry layout in GCS (`gs://<bucket>/models/<model>/<version>/`) with `metadata.json` and artifact(s).
2) Add small Python helper (`api/scripts/model_registry.py`) to read/write metadata and resolve latest/production stage.
3) CI: after tests, write metadata (`metrics`, `params`, `sha`, `artifact_uri`, `version`) and upload artifact(s) to registry bucket; emit `MODEL_VERSION` output.
4) CD: accept `MODEL_VERSION` input (from CI output or manual); resolve artifact URI; bake into image or download at startup; set env `MODEL_VERSION`.
5) API: add `/info` returning `model_version`, `model_uri`, `git_sha`.

## Stretch
- Add stages (`Staging`, `Production`) and a promotion CLI to change stage without rebuild.
- Add signatures/checksums for artifacts.
- Add lineage links (dataset version, training code commit).

## Dependencies
- GCS bucket for registry; service account with read/write to bucket.
- Minor code changes in CI/CD + API.

## Acceptance Criteria
- Given a version in registry, CD deploys it without manual artifact placement.
- `/info` returns the deployed version and matches registry metadata.
- Promotion uses version tags; no reliance on local `api/models` files.

## Risks/Notes
- Keep versions immutable; never overwrite an existing version key.
- Enforce retention policy on registry bucket to control cost.
