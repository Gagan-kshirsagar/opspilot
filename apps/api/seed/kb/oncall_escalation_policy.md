# On-Call and Escalation Policy

## 1. On-Call Rotations & Tiers
OpsPilot uses a tiered on-call schedule managed via PagerDuty:

- **Tier 1 (Primary On-Call)**: First responder for all high-priority alerts across production services. Rotates weekly on Mondays at 10:00 AM UTC.
- **Tier 2 (Secondary / Backup)**: Escalation fallback if the primary responder does not acknowledge an alert within the required SLA window.
- **Tier 3 (Engineering Management / Leads)**: Escalation for unacknowledged critical alerts or when emergency resource allocation is required across multiple engineering teams.

## 2. Response Time SLAs
- **SEV-1 Critical Alert**: Acknowledgement within **5 minutes**, initial investigative triage within **15 minutes**.
- **SEV-2 High Alert**: Acknowledgement within **15 minutes**, initial triage within **30 minutes**.
- **SEV-3 Moderate Alert**: Acknowledged within **2 hours** during business hours or next business morning if triggered overnight.

## 3. Escalation Rules
1. If Tier 1 does not acknowledge a page within 5 minutes, PagerDuty automatically pages Tier 2.
2. If Tier 2 does not acknowledge within an additional 5 minutes, the on-call Engineering Manager (Tier 3) is paged.
3. If an active investigation stalls for more than 30 minutes without clear mitigation, the primary responder must page the respective service owner or secondary domain expert.

## 4. Handover Checklist
At the end of each weekly shift, the outgoing on-call engineer and incoming on-call engineer conduct a 30-minute sync to review:
- Open incidents and active investigations.
- Flapping or noisy monitoring alerts.
- Upcoming maintenance windows or planned production releases.
- Status of outstanding postmortem action items.
