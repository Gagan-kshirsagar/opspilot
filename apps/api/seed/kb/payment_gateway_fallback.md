# Payment Processing Gateway Fallback and Retry Policy

## 1. Settlement Pipeline Overview
The Payment Processing service handles customer subscription charges, invoice settlements, and refund requests via primary payment provider (Stripe) and secondary fallback provider (Adyen).

## 2. Idempotency & Duplicate Prevention
- Every charge request must include a unique client-generated `Idempotency-Key` header (UUID v4 format).
- Idempotency keys are cached in Redis with a 24-hour expiration. If a duplicate request arrives while a previous transaction is processing, the gateway waits for settlement completion or returns the cached response.

## 3. Circuit Breaker & Automatic Provider Failover
- **Failure Threshold**: If the primary payment provider error rate exceeds **10%** over a 2-minute rolling window or p95 response time exceeds **4,000ms**, the Circuit Breaker trips to `OPEN`.
- **Failover Route**: All subsequent charge requests automatically route to the secondary gateway without interrupting user checkout flows.
- **Half-Open Probe**: After 5 minutes, 5% of traffic is routed back to the primary provider. If all probe transactions succeed, the circuit breaker resets to `CLOSED`.

## 4. Exponential Backoff Policy
For transient network timeouts (HTTP 502/503/504), clients must implement exponential backoff with full jitter:
- Initial delay: 500ms
- Multiplier: 2.0
- Maximum retries: 3 attempts
- Maximum delay: 5,000ms
