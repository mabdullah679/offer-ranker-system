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

## Acceptance Criteria
- Scheduled job runs, trains, evaluates, registers a version with metrics.
- Promotion decision is logged and respects improvement threshold.
- CD can deploy the promoted version without manual artifact handling.

## Risks/Notes
- Control costs with small schedules (e.g., weekly) and preemptible/low-tier settings.
- Ensure failures alert rather than silently stop the schedule.
