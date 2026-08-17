# Monitoring, Metrics, and Alerting Guidelines

## 1. Golden Signals
All OpsPilot production services must export Prometheus metrics covering the four Google SRE Golden Signals:
1. **Latency**: Duration taken to process requests (measured at p50, p90, p95, p99 percentiles).
2. **Traffic**: Demand placed on the service (HTTP requests per second or message ingestion rate).
3. **Errors**: Rate of failed requests (HTTP 5xx status codes, unhandled exceptions, database deadlocks).
4. **Saturation**: System capacity utilization (CPU, memory consumption, connection pool exhaustion, disk IOPS).

## 2. Multi-Window Multi-Burn-Rate Alerting
To prevent alert fatigue and catch fast outages without waiting hours:
- **Fast Burn Alert (SEV-1 Page)**: 14.4x burn rate over 1 hour (2% of 30-day error budget consumed in 1 hour) -> Instant PagerDuty page.
- **Slow Burn Alert (SEV-2 Alert)**: 3x burn rate over 6 hours (5% of error budget consumed in 6 hours) -> Urgent Slack alert.
- **Maintenance Alert (SEV-3 Ticket)**: 1x burn rate over 3 days -> Automated Jira ticket created for team backlog.

## 3. Grafana Dashboard Standard
Every service team must maintain a standard dashboard in Grafana containing:
- High-level SLO gauge & 30-day error budget remaining.
- Real-time RPS and error rate timeline broken down by HTTP status code.
- Endpoint latency heatmap (p50, p95, p99).
- Database query latency and connection pool saturation gauges.
