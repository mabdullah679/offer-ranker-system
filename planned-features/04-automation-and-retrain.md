# Automation & Scheduled Retrain

## Goal
Automate training/evaluation and promote only if a new model beats the incumbent.

## Scope (MVP)
- Scheduled job (Cloud Scheduler → Cloud Run job) to run training pipeline (scripts already in repo).
- Evaluate on held-out/validation set; log metrics and package model artifact + metadata.
- Register new version; optionally auto-promote if metric improves beyond threshold.
- Notify via CI/CD summary or Slack/webhook with results.

## Steps
1) Containerize training job (reusing api/training deps); add entrypoint for `train_and_eval`.
2) Cloud Scheduler triggers Cloud Run job with project/region/registry info; job writes model + metadata to registry bucket.
3) Compare new metrics vs. current production version (from registry); mark stage `Staging` or auto-promote to `Production` if better and stable.
4) Emit summary (metrics, version, decision) to logs and notification channel; surface in GitHub Summary if run via Actions.
5) Wire CD to deploy a specified version or last promoted production version.

## Stretch
- Add dataset versioning hash; cache features; incremental training.
- Add human-approval gate before promotion.
- Add AB test harness for multiple candidate models.

## Dependencies
- Registry in place; bucket + write perms.
- Training data access (GCS or repo data).
- Cloud Scheduler + Cloud Run jobs enabled.

## Cost & Free Tier Considerations
- Prefer running the training and evaluation pipeline on a local machine or GitHub-hosted runners, keeping GCP usage limited to storing the resulting compressed model artifact in GCS.
- If GCP-based training is ever used, keep schedules infrequent (manual or at most weekly), choose the smallest suitable machine sizes, and use subsampled data so compute time remains within or close to free-tier limits.
- Apply the same discipline as the model registry: keep only a few candidate models in GCS, prune aggressively, and ensure total stored model size stays under the free storage allowance.
- Document that, for this project, automation and retrain flows are conceptual and not intended for continuous, production-scale runs.

## Acceptance Criteria
- Scheduled job runs, trains, evaluates, registers a version with metrics.
- Promotion decision is logged and respects improvement threshold.
- CD can deploy the promoted version without manual artifact handling.

## Risks/Notes
- Control costs with small schedules (e.g., weekly) and preemptible/low-tier settings.
- Ensure failures alert rather than silently stop the schedule.
