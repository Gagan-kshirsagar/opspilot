# Decision Log

A running record of notable engineering decisions — **this file is also your
interview prep.** For each entry: what you decided, why, and what you rejected.
Keep entries short (3–5 lines). Newest at the top.

Format:

```
## YYYY-MM-DD — <short title>
**Decision:** <what>
**Why:** <the reasoning / the constraint that drove it>
**Rejected:** <the alternative and why not>
```

## 2026-08-18 — Cost/abuse protection: RateStore, daily AI budget, and quota-resilient UX

**Decision:** Implemented a pluggable `RateStore` protocol (`MemoryRateStore` for offline/CI + `UpstashRedisRateStore` for production), per-IP/user rate limiting on chat endpoints (10 msgs/10 mins), a global daily AI request budget (500/day UTC reset) that short-circuits before LLM invocation, tight token caps (`maxOutputTokens=1024`, `top_k=4`, `max_iters=4`), and graceful handling for Gemini 429 quota exhaustion.
**Why:** Guarantees that public deployment on free tiers (Vercel, Render, Gemini API) cannot incur bills or crash on quota exhaustion, while giving visitors clear countdown timers and friendly explanations instead of HTTP 500 errors.
**Rejected:** External-only Redis dependency (would break offline CI and local development), unbuffered daily tracking (allows quota burnout in hours), silent 500 crashes on Gemini quota limits.

## 2026-08-18 — RAG & Agent evaluation harness with deterministic offline CI gate

**Decision:** Built a 28-case golden dataset with a multi-metric scorer measuring citation recall (`must_cite`), tool selection accuracy (`expected_tools`), deterministic factual point coverage (`expected_points`), decline/hallucination detection on out-of-scope queries, and an offline runner gating CI builds (`--offline --threshold 0.80`).
**Why:** Continuous regression testing for LLM retrieval and agentic tool routing without paying API costs or suffering network flakiness in CI. Offline execution against real repository tools executes under 20ms while validating that schemas, queries, and guardrails remain grounded.
**Rejected:** Pure LLM-as-a-judge in CI (flaky, non-deterministic, requires API keys and budget for every push), mock-only tests that skip real tool execution (fails to detect DB schema or repository regressions).

## 2026-08-17 — ReAct agent with typed tool calling & reasoning stream

**Decision:** Implemented a LangGraph ReAct-style agent graph with typed read-only tools (`retrieve_docs`, `query_services`, `query_incidents`, `query_users`, `get_service_detail`) calling existing repositories and retriever. Extended SSE streaming with `event: step` (`tool_call`, `tool_result`) and built a collapsible thought trail UI.
**Why:** Unifies static knowledge base runbooks with live operational database queries without creating duplicate query paths or raw SQL in tools. Loop guardrail (`AGENT_MAX_ITERS=5`) prevents runaway loops and forces grounded synthesis.
**Rejected:** Standalone single-turn RAG (cannot answer queries requiring live service/incident counts combined with runbooks), unconstrained autonomous agents with write permissions (high risk in ops environments; mutations belong in controlled review workflows).

## 2026-08-17 — SSE streaming chat & persistent multi-turn conversational memory

**Decision:** Server-Sent Events (`text/event-stream` via FastAPI `StreamingResponse`) with typed events (`token`, `citations`, `done`, `error`), backed by `chat_sessions` and `chat_messages` tables in Postgres. Prompt memory dynamically caps the last 6 messages (3 conversation turns) for multi-turn dialogue context.
**Why:** Unidirectional HTTP streaming is lightweight and robust through standard reverse proxies without WebSocket connection management overhead. Dynamic turn-capping provides natural follow-up context while strictly bounding LLM context token usage. Single source of truth is preserved by buffering tokens locally during streaming and committing to Postgres + invalidating TanStack Query cache upon the `done` event.
**Rejected:** WebSockets (unnecessary duplex complexity for a request-response chat stream), storing conversation history purely in client state (lost across devices/reloads), unbounded conversation history in prompt (risks token limit overflows and excessive latency).

## 2026-08-17 — RAG knowledge base foundation with pgvector & Gemini

**Decision:** Postgres `pgvector` with HNSW cosine similarity index, chunking markdown ops docs, provider-agnostic `EmbeddingsProvider` & `LLMProvider` abstractions wrapping Gemini `text-embedding-004` and `gemini-1.5-flash`, with similarity threshold guardrail and citation tracking.
**Why:** Single database engine for app data + embeddings (no external vector database needed), swappable LLM/embeddings clients for zero vendor lock-in, and strict similarity threshold guardrail to eliminate hallucination by declining out-of-KB queries without model invocation.
**Rejected:** External vector databases like Pinecone/Weaviate (adds operational complexity and cost when Postgres/pgvector already exists), client-side RAG or ungrounded model queries (high hallucination risk).

## 2026-08-17 — Services & Incidents domains with rank-based sorting

**Decision:** Postgres-backed queryable `services` and `incidents` models with operational priority ranking (sev1 < sev2 < sev3, open < investigating < resolved) using SQL `CASE WHEN` expressions in SQLAlchemy 2.0 async, paired with a TanStack Table UI and RBAC-guarded resolve endpoint.
**Why:** Maintains domain separation, provides high-performance server-side ranking for triage workflows, and structures data cleanly for future AI agent query toolkits.
**Rejected:** Alphabetical column sorting for severity/status (semantically incorrect for triage), client-side post-sort (breaks pagination offsets), inline business logic in API routers.

## 2026-08-17 — Server-side users table with TanStack Table + shadcn

**Decision:** Server-side pagination, sorting, and multi-field filtering backed by SQLAlchemy 2.0 async queries, surfaced via headless TanStack Table + shadcn table primitives.
**Why:** Scales to thousands of users without memory or network bottlenecks, keeps query parameters URL/state synchronised, and provides a fully accessible data table with custom token styling.
**Rejected:** Client-side sorting/filtering (unscalable for large databases, transmits entire table over network), pre-packaged heavy grid libraries like AG-Grid or MUI X-Data-Grid (breaks single UI system rule and adds bloated bundle size).

## 2026-08-17 — Session persistence & auth bootstrap on reload

**Decision:** Use an `httpOnly`, `SameSite=Lax` refresh cookie set by FastAPI on auth endpoints, backed by a provider-agnostic `restoreSession()` method and `<AuthBootstrap>` on startup, with status initialized to `'loading'`.
**Why:** Persists credentials across page reloads securely without exposing long-lived tokens to JavaScript/XSS, while preventing premature route guard redirects or login page flashes during hydration.
**Rejected:** Storing refresh tokens purely in memory (wiped on reload), storing purely in localStorage (exposed to XSS), or letting route guards inspect uninitialized in-memory state before rehydration finishes.

## 2026-08-16 — UI library: shadcn/ui only (no Material UI)


**Decision:** Use shadcn/ui + Tailwind as the single UI system.
**Why:** Code ownership, zero runtime styling cost, RSC-friendly, and it matches
our existing Tailwind design tokens. One styling engine keeps the app consistent.
**Rejected:** Material UI, and MUI+shadcn together — two styling engines (Emotion

- Tailwind) add bundle weight and visual inconsistency for no benefit here.

## 2026-08-16 — Server vs client state split

**Decision:** TanStack Query owns all server state; Zustand owns only UI state.
**Why:** Server data needs caching, dedup, revalidation, retry — Query does this;
hand-rolling it in Zustand/useState reinvents a caching layer badly.
**Rejected:** Redux Toolkit (heavier than needed), fetching in useEffect (no
caching, prone to stale-response races).

## 2026-08-16 — Backend in Python/FastAPI (separate service)

**Decision:** FastAPI backend, separate from the Next.js frontend.
**Why:** Best Python agent/eval ecosystem (LangGraph, Langfuse) for Phase 2, and
demonstrates real full-stack: Next.js client + Python API + Postgres.
**Rejected:** All-in-Next.js API routes — weaker agent tooling in TS for the
Tier-3 agent, and a less clear full-stack story.

<!-- Add new decisions above this line as you build each slice. -->
