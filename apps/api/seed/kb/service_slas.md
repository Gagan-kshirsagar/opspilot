# Service Level Agreements (SLAs) & Availability Targets

## 1. Overview
Service Level Agreements (SLAs) and Service Level Objectives (SLOs) define our contractual availability and latency targets across all production microservices.

## 2. Core Service Availability Targets
- **API Gateway**: **99.98% availability** (monthly downtime allowance: ~8.6 minutes). Target latency: p95 < 50ms, p99 < 150ms.
- **Auth Service**: **99.95% availability** (monthly downtime allowance: ~21.6 minutes). Target latency: p95 < 80ms, p99 < 200ms.
- **Payment Processing**: **99.90% availability** (monthly downtime allowance: ~43.2 minutes). Target settlement latency: p95 < 800ms.
- **Search Index**: **99.50% availability** (monthly downtime allowance: ~3.6 hours). Target query latency: p95 < 250ms.
- **Notification Service**: **99.90% availability**. Target dispatch latency: p95 < 5 seconds for OTP and SMS, p95 < 30 seconds for marketing emails.
- **Analytics Pipeline**: **99.00% availability**. Target telemetry ingestion lag: < 60 seconds end-to-end.

## 3. Error Budgets & Deployment Freeze
- Each service has a rolling 30-day error budget calculated as `(1 - SLO) * total_requests`.
- If a service exhausts more than **80% of its monthly error budget**, non-critical feature deployments are frozen. Engineering efforts must pivot exclusively to stability, reliability improvements, and automated testing until the budget recovers.

## 4. SLA Breach Consequences & Reporting
- Any SLA breach triggers an automatic SEV-1 or SEV-2 incident review.
- The VP of Engineering and Product Leads receive a monthly SLA compliance audit report detailing all incidents, downtime causes, and corrective action items.
