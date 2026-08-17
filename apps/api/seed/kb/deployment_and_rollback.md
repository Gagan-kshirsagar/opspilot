# Deployment and Rollback Runbook

## 1. Deployment Strategy
OpsPilot follows a progressive delivery model:

1. **Staging Verification**: All code merged to `main` is automatically deployed to the staging cluster and validated by automated end-to-end integration test suites.
2. **Canary Rollout (10%)**: Production deployments begin with a 10% canary slice evaluated over a 15-minute observation window.
3. **Full Production Rollout (100%)**: If error rate delta is < 0.1% and latency percentiles remain steady, the remaining 90% fleet is updated using rolling blue-green pod replacement.

## 2. Automated Rollback Triggers
Canary deployments automatically trigger an instant rollback if any of the following conditions occur:
- 5xx error rate spikes above **1.0%** for 3 consecutive minutes.
- p99 latency increases by more than **50%** relative to baseline.
- Kubernetes pod health checks report continuous crash loops or OOM kills.
- Synthetic health check probes to `/health` or `/metrics` fail.

## 3. Manual Rollback Procedure
If an issue is detected after 100% rollout:
1. Announce the rollback in `#engineering-deployments` and `#incident-war-room`.
2. Revert the target release using GitHub Actions rollback workflow or execute `kubectl rollout undo deployment/<service-name> -n production`.
3. Verify that new pods have initialized and traffic has drained from the faulty version:
   `kubectl rollout status deployment/<service-name> -n production`.
4. Run smoke test queries against the service endpoint to verify healthy response codes.
5. Notify the team upon successful restoration.
