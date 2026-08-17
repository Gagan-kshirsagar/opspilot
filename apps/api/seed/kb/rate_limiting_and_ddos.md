# Rate Limiting and DDoS Mitigation Guide

## 1. Gateway Rate Limiting Architecture
OpsPilot enforces multi-layer rate limiting at the API Gateway edge using a distributed Redis Token Bucket algorithm.

## 2. Standard Rate Limit Tiers
- **Anonymous / Unauthenticated Requests**: **60 requests per minute** per IP address. Burst limit: 20 requests.
- **Authenticated Viewer / Regular Users**: **600 requests per minute** per user token. Burst limit: 100 requests.
- **Service-to-Service Internal API Calls**: **5,000 requests per minute** with mutual TLS (mTLS) authentication.
- **High-Risk Endpoints (Login, Password Reset, Token Refresh)**: **5 requests per minute** per IP address to prevent brute-force attacks.

## 3. Rate Limit Headers
When a client makes a request, the API Gateway returns the following RFC standard headers:
- `X-RateLimit-Limit`: Maximum permitted request quota in the current window.
- `X-RateLimit-Remaining`: Remaining request tokens in the current window.
- `X-RateLimit-Reset`: Unix epoch timestamp when the current quota bucket replenishes.
- `Retry-After`: Returned with HTTP status code `429 Too Many Requests` indicating how many seconds the client must wait.

## 4. Mitigating Active Layer-7 Attacks
1. If a DDoS attack is detected on the API Gateway, enable Cloudflare Under Attack Mode from the edge security dashboard.
2. Apply temporary IP blocklists via AWS WAF or Kubernetes Ingress Controller rules.
3. Scale the API Gateway replica count from 3 to 10 pods:
   `kubectl scale deployment/api-gateway --replicas=10 -n production`.
