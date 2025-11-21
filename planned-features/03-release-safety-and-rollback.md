# Release Safety & Rollback

## Goal
Deploy safely with canary/shadow options and fast rollback on regression.

## Scope (MVP)
- Keep previous image tag; automatic rollback if smoke tests fail.
- Add manual flag to deploy as canary (small traffic slice) before full rollout.
- Shadow testing option: mirror a percentage of traffic to a candidate model without affecting users; compare outputs.

## Steps
1) Persist previous image tag in CD (already captured); add a rollback command wired to failure hooks.
2) Add CD inputs for strategy: `canary_percent` (e.g., 5–10%) or `shadow_only` toggle.
3) Implement Cloud Run traffic split for canary; promote to 100% if health/smoke pass.
4) For shadow: duplicate requests to candidate endpoint inside API or via middleware; log paired outputs for comparison; no user impact.
5) Add a small regression checker that compares shadow vs. current outputs on a sample window; if divergence exceeds threshold, abort promotion.

## Stretch
- Automated promotion from canary after N minutes and stable metrics.
- Output diff dashboards; alerts on divergence.

## Dependencies
- Cloud Run traffic-splitting enabled; CD can set traffic rules.
- Logging/metrics in place to compare outputs.

## Cost & Free Tier Considerations
- For this project (no real user traffic), treat canary and shadow deployments as short-lived experiments rather than long-running multi-revision setups.
- When experimenting, keep Cloud Run CPU/RAM minimal and limit the duration of canary/shadow phases so additional concurrent revisions do not materially exceed free-tier compute.
- Avoid running multiple high-traffic revisions in parallel; once tests or comparisons complete, consolidate traffic back to a single active revision to minimize resource usage.

## Acceptance Criteria
- CD can deploy with canary traffic and roll forward/rollback based on health.
- Shadow mode collects comparison logs without impacting responses.
- Rollback can be triggered automatically on smoke test failure or manually via input.

## Risks/Notes
- Ensure shadow requests don’t double-charge downstream services.
- Keep rollback command well-tested; avoid stale previous image references.
