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

---

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
