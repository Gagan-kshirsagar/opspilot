# Security Incident Response Procedure

## 1. Security Incident Classification
- **P0 Critical Security Event**: Active unauthorized root access, leaked production credentials/secrets in public repos, confirmed database exfiltration, or ransomware attacks.
- **P1 High Security Event**: Suspicious admin privilege escalation, unauthorized API access tokens detected in logs, or vulnerable zero-day dependency exploitation.
- **P2 Moderate Security Event**: Phishing report targeting employees, failed brute-force rate limit trigger, or missing encryption on non-PII internal data.

## 2. Immediate Containment Actions
1. **Rotate Leaked Credentials Immediately**:
   - For compromised database passwords, immediately generate new credentials in AWS Secrets Manager and trigger an application rolling restart.
   - For compromised JWT signing keys, update `OPSPILOT_JWT_SECRET` and invalidate all active session tokens immediately.
2. **Isolate Affected Pods**:
   - Remove compromised Kubernetes pods from the active Service load balancer using network policies:
     `kubectl label pod <pod-name> quarantine=true -n production`.
3. **Capture Forensic Evidence**:
   - Take disk snapshots and preserve access logs before pod termination.

## 3. Communication & Legal Disclosure
- All communication must stay strictly inside encrypted, private Slack channels `#sec-incident-internal`.
- Do not speculate on breach scope in public or general channels.
- The Security Lead notifies Legal and Compliance within 24 hours if PII or customer financial data was accessed.
