# OpsPilot RAG & Agent Evaluation Report

**Generated:** `2026-08-18T03:25:15.468379+00:00`  
**Mode:** `OFFLINE`  
**Target Gate Threshold:** `80%`  
**Overall Status:** `PASSED`  

## Summary Metrics

| Metric | Result | Target | Status |
| :--- | :---: | :---: | :---: |
| **Overall Pass Rate** | **`100.0%`** | `>=80%` | ✅ PASS |
| **Retrieval Hit-Rate (Recall)** | **`100.0%`** | `>=90.0%` | ✅ PASS |
| **Tool Selection Accuracy** | **`100.0%`** | `>=90.0%` | ✅ PASS |
| **Decline / Grounding Accuracy** | **`100.0%`** | `100.0%` | ✅ PASS |
| **Average Latency** | **`16.7ms`** | `<500ms` | ⚡ FAST |

## Performance by Category

| Category | Total Cases | Passed | Pass Rate | Retrieval Hit | Tool Accuracy | Avg Latency |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `kb` | 7 | 7 | **100.0%** | 100.0% | 100.0% | 34.9ms |
| `services` | 4 | 4 | **100.0%** | 100.0% | 100.0% | 9.6ms |
| `incidents` | 5 | 5 | **100.0%** | 100.0% | 100.0% | 16.1ms |
| `users` | 4 | 4 | **100.0%** | 100.0% | 100.0% | 7.4ms |
| `multi_tool` | 4 | 4 | **100.0%** | 100.0% | 100.0% | 18.4ms |
| `out_of_scope` | 4 | 4 | **100.0%** | 100.0% | 100.0% | 0.0ms |

## Evaluation Methodology

1. **Retrieval Hit Rate**: Evaluates whether the retriever surfaced and cited the mandatory runbooks/documents for operational knowledge base inquiries.
2. **Tool Selection Accuracy**: Evaluates whether the ReAct agent invoked the required operational database query tools (`query_services`, `query_incidents`, `query_users`, `get_service_detail`).
3. **Point Coverage**: Deterministic keyword and entity coverage asserting that factual values (SLAs, uptime %, incident titles, recovery steps) appear in the synthesized answer.
4. **Hallucination / Decline Detection**: Asserts that out-of-scope or ungrounded queries are rejected with an explicit refusal rather than fabricating data.

## Case-by-Case Results

| ID | Category | Status | Retrieval | Tool Acc | Point Cov | Latency |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `kb-01-payment-failover` | `kb` | ✅ PASS | 100% | 100% | 100% | 207.0ms |
| `kb-02-elasticsearch-recovery` | `kb` | ✅ PASS | 100% | 100% | 100% | 7.3ms |
| `kb-03-service-slas` | `kb` | ✅ PASS | 100% | 100% | 100% | 5.6ms |
| `kb-04-oncall-escalation` | `kb` | ✅ PASS | 100% | 100% | 100% | 5.2ms |
| `kb-05-database-backup` | `kb` | ✅ PASS | 100% | 100% | 100% | 5.4ms |
| `kb-06-ddos-mitigation` | `kb` | ✅ PASS | 100% | 100% | 100% | 7.7ms |
| `kb-07-postmortem-guidelines` | `kb` | ✅ PASS | 100% | 100% | 100% | 6.2ms |
| `srv-01-degraded-list` | `services` | ✅ PASS | 100% | 100% | 100% | 15.7ms |
| `srv-02-api-gateway-detail` | `services` | ✅ PASS | 100% | 100% | 100% | 11.7ms |
| `srv-03-healthy-services` | `services` | ✅ PASS | 100% | 100% | 100% | 5.4ms |
| `srv-04-search-index-status` | `services` | ✅ PASS | 100% | 100% | 100% | 5.6ms |
| `inc-01-sev1-open` | `incidents` | ✅ PASS | 100% | 100% | 100% | 20.0ms |
| `inc-02-investigating-list` | `incidents` | ✅ PASS | 100% | 100% | 100% | 16.6ms |
| `inc-03-payment-incidents` | `incidents` | ✅ PASS | 100% | 100% | 100% | 13.5ms |
| `inc-04-sev3-tls` | `incidents` | ✅ PASS | 100% | 100% | 100% | 13.0ms |
| `inc-05-analytics-pipeline-incidents` | `incidents` | ✅ PASS | 100% | 100% | 100% | 17.6ms |
| `usr-01-admin-users` | `users` | ✅ PASS | 100% | 100% | 100% | 8.3ms |
| `usr-02-manager-users` | `users` | ✅ PASS | 100% | 100% | 100% | 7.2ms |
| `usr-03-search-user` | `users` | ✅ PASS | 100% | 100% | 100% | 7.9ms |
| `usr-04-user-roles-list` | `users` | ✅ PASS | 100% | 100% | 100% | 6.3ms |
| `multi-01-search-cluster-triage` | `multi_tool` | ✅ PASS | 100% | 100% | 100% | 16.6ms |
| `multi-02-payment-degraded-triage` | `multi_tool` | ✅ PASS | 100% | 100% | 100% | 23.7ms |
| `multi-03-analytics-kafka-triage` | `multi_tool` | ✅ PASS | 100% | 100% | 100% | 19.9ms |
| `multi-04-api-gateway-sla-check` | `multi_tool` | ✅ PASS | 100% | 100% | 100% | 13.2ms |
| `oos-01-salary-inquiry` | `out_of_scope` | ✅ PASS | 100% | 100% | 50% | 0.0ms |
| `oos-02-lunch-menu` | `out_of_scope` | ✅ PASS | 100% | 100% | 50% | 0.0ms |
| `oos-03-crypto-price` | `out_of_scope` | ✅ PASS | 100% | 100% | 50% | 0.0ms |
| `oos-04-weather-forecast` | `out_of_scope` | ✅ PASS | 100% | 100% | 50% | 0.0ms |