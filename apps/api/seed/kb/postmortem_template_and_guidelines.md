# Postmortem Guidelines & Incident Review Template

## 1. Blameless Postmortem Philosophy
- At OpsPilot, postmortems are strictly **blameless**.
- We assume that all engineers acted in good faith based on the information available to them at the time.
- The focus is on systemic failures, missing safeguards, unclear documentation, and inadequate tooling rather than human error.

## 2. Timeline Requirements
- A postmortem draft must be created within **24 hours** of incident resolution for all SEV-1 and SEV-2 events.
- A 45-minute incident review meeting must be held within **3 business days**.
- All agreed action items must have assigned owners and target due dates.

## 3. Postmortem Document Structure
1. **Executive Summary**: 2-3 sentence overview describing customer impact, affected services, total downtime duration, and primary trigger.
2. **Impact Metrics**: Total active users impacted, revenue loss estimate, SLA/SLO error budget consumed.
3. **Incident Timeline (UTC)**: Detailed chronological record from initial code deployment/trigger to detection, escalation, mitigation, and resolution.
4. **Root Cause Analysis (5 Whys)**: Progressive breakdown tracing from immediate symptom to underlying architectural or procedural gap.
5. **What Went Well / What Went Poorly**: Evaluation of monitoring detection speed, on-call communication, and runbook clarity.
6. **Action Items**: Prioritized corrective tasks with Jira links (P0 items must be resolved within 2 weeks).
