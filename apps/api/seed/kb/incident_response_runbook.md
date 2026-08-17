# Incident Response Runbook

## 1. Severity Classification Matrix
OpsPilot classifies all service outages and operational anomalies into three severity levels:

- **SEV-1 (Critical Outage)**: Customer-facing outage affecting core business transactions, complete unavailability of primary services (API Gateway, Auth Service, or Payment Processing), or severe data loss/corruption risk.
- **SEV-2 (High Impact)**: Degraded system performance, partial failure of non-critical workflows (Search Index degradation, telemetry stream delay), or elevated error rates (>5%) without full customer disruption.
- **SEV-3 (Moderate / Low Impact)**: Minor bugs, isolated non-blocking customer reports, rate limit warning thresholds, or non-urgent maintenance alerts.

## 2. Escalation & Declaration Steps
1. **Declare the Incident**: Any engineer who detects a critical anomaly must declare the incident in Slack channel `#incident-war-room`.
2. **Assign Incident Commander (IC)**: The on-call primary engineer immediately assumes the role of Incident Commander unless delegated to an Engineering Manager or Lead.
3. **Establish Communication Channel**: Create a dedicated Google Meet bridge and incident Slack channel `#inc-YYYYMMDD-service-name`.
4. **Notify Stakeholders**: For SEV-1, the IC sends a status broadcast to `#leadership-updates` within 15 minutes of declaration and posts an external update to the Statuspage.

## 3. Incident Commander Responsibilities
- **Directing Mitigation**: The IC coordinates investigative hypotheses and authorizes mitigation actions (e.g. rollbacks, traffic throttling, feature flag disablement).
- **Maintaining Communications**: Posts progress updates every 15 minutes for SEV-1 and every 30 minutes for SEV-2.
- **Assigning Roles**: Assigns a Communications Lead, Technical Lead (debugging), and Scribe (logging actions and timestamps).

## 4. Mitigation & Resolution
- Primary goal during active incident is **fast mitigation**, not permanent root cause elimination.
- Once error rates return below SLA thresholds and services report healthy for at least 15 continuous minutes, the IC can mark the incident status as `RESOLVED`.
- Transition directly into postmortem scheduling within 24 hours of resolution.
