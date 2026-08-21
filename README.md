<div align="center">

<!-- Optional: replace with your logo. A simple wordmark works great. -->
<h1>OpsPilot</h1>

### Operations, on autopilot — an open-source, AI-powered operations platform.

A production-grade full-stack app with a **tool-using LangGraph agent** that answers
questions about your operations from a knowledge base **and** live data — grounded,
cited, and streamed in real time.

<!-- Replace the URLs/badges below with your real ones -->
[**🔴 Live Demo**](https://your-opspilot.vercel.app) &nbsp;·&nbsp;
[**📺 Demo Video**](https://your-demo-video-link) &nbsp;·&nbsp;
[**🏗️ Architecture**](#-architecture)

![Web CI](https://github.com/Gagan-kshirsagar/opspilot/actions/workflows/web-ci.yml/badge.svg)
![API CI](https://github.com/Gagan-kshirsagar/opspilot/actions/workflows/api-ci.yml/badge.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Next.js](https://img.shields.io/badge/Next.js-15-black)
![FastAPI](https://img.shields.io/badge/FastAPI-async-009688)
![Gemini](https://img.shields.io/badge/LLM-Gemini-4285F4)

<br/>

<!-- Replace with a real hero screenshot or GIF of the agent answering a question -->
<img src="docs/hero.png" alt="OpsPilot dashboard and Ask OpsPilot agent" width="90%"/>

<sub>Try it: sign in with <b>“Continue as demo guest”</b> — no signup needed.</sub>

</div>

---

## ✨ Highlights

- 🤖 **Agentic AI, not just a chatbot.** A LangGraph ReAct agent decides which tools to call —
  searching runbooks (RAG) *and* querying live services/incidents/users — then synthesizes a
  grounded, cited answer.
- 📚 **Grounded RAG with citations.** Answers come from an indexed knowledge base (pgvector);
  every claim links its source. Out-of-scope questions are **declined**, not hallucinated.
- ⚡ **Real-time streaming.** Responses stream token-by-token over Server-Sent Events, with a
  visible “thinking” trail of the tools the agent used.
- 🧪 **Measured, not vibe-checked.** An eval harness scores retrieval hit-rate, tool selection,
  answer coverage, and hallucination rate — gated in CI.
- 🔐 **Provider-pluggable auth.** JWT today, Firebase/OAuth tomorrow — behind a single interface.
- 💸 **Deployed on $0.** Scale-to-zero hosting, a free-tier LLM key that can only rate-limit
  (never bill), plus app-level daily/per-IP caps. Defence-in-depth cost control.

---

## 🎬 Demo

<!-- Replace with a real GIF: login → users table → agent answering a multi-tool question -->
![OpsPilot demo](docs/demo.gif)

> **Ask it:** _“Which services are degraded and what’s the runbook for them?”_
> → the agent queries live service data **and** retrieves the runbook, then answers with citations.

---

## 🏗️ Architecture

```
                       ┌──────────────────────────┐
   Recruiter ─────────▶│   Next.js (Vercel)       │   Pure frontend:
   browser             │   App Router · TS        │   TanStack Query · Zustand
                       │   shadcn/ui · Tailwind   │   Axios · TanStack Table
                       └───────────┬──────────────┘
                                   │ HTTPS / SSE (streaming)
                                   ▼
                       ┌──────────────────────────┐
                       │   FastAPI (scale-to-zero) │   thin routers → services
                       │   Pydantic · async        │   → repositories
                       │   Auth · Users · Services  │
                       │   Incidents · RAG · Agent  │
                       └───────────┬──────────────┘
             ┌─────────────────────┼───────────────────────────┐
             ▼                     ▼                           ▼
   ┌───────────────────┐  ┌──────────────────┐    ┌──────────────────────┐
   │ Postgres+pgvector │  │  Gemini (free)   │    │  Upstash · Langfuse  │
   │  app data +       │  │  LLM + embeddings│    │  rate limits · traces│
   │  document_chunks  │  └──────────────────┘    └──────────────────────┘
   │  (Neon)           │
   └───────────────────┘
```

**The RAG + agent flow**

```
question ─▶ agent (Gemini, reasons) ─▶ needs a tool?
                    ▲                        │ yes
                    │                        ▼
                    │             retrieve_docs / query_services /
                    └── observe ── query_incidents / query_users
                                             │ no
                                             ▼
                          grounded, cited answer  ── streamed via SSE
```

---

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 15 (App Router), React, TypeScript, TanStack Query, TanStack Table, Zustand, Axios, shadcn/ui, Tailwind CSS |
| **Backend** | FastAPI, Pydantic v2, SQLAlchemy 2.0 (async), Alembic |
| **AI** | LangGraph (agent), Google Gemini (LLM + `text-embedding-004`), Postgres **pgvector** (RAG) |
| **Data** | PostgreSQL (Neon) |
| **Infra** | Vercel · Render/Cloud Run · Upstash Redis · Langfuse · GitHub Actions CI |
| **Auth** | JWT (provider-pluggable) + demo-guest |

---

## 🔬 Evaluation results

The agent is measured against a golden dataset (KB, live-data, multi-tool, and
out-of-scope cases). Deterministic checks run offline in CI and gate the build.

<!-- Replace with your real numbers from evals/reports/latest.md -->
| Metric | Score |
|---|---|
| Overall pass rate | **100.0% (28/28)** |
| Retrieval hit-rate (sources) | **100.0%** |
| Tool-selection accuracy | **100.0%** |
| Hallucination / decline accuracy | **100.0%** |
| Avg latency / request | **16.7ms** |

> _Full methodology and the latest run:_ [`apps/api/evals/reports/latest.md`](apps/api/evals/reports/latest.md)

<!-- Optional but powerful: a Langfuse trace screenshot -->
<!-- ![Langfuse trace](docs/trace.png) -->

---

## 🚀 Key engineering decisions

Selected from [`DECISIONS.md`](DECISIONS.md) — the trade-offs behind the build.

- **Grounding over fluency.** If retrieval is weak, the agent declines (“I don’t have that in
  the knowledge base”) instead of fabricating — enforced *before* the model is even called, and
  guarded by out-of-scope eval cases in CI.
- **Server-side pagination/sort/filter.** All done in SQL, not in React — the table stays fast
  past thousands of rows and doesn’t ship the whole dataset to the client.
- **No optimistic updates where placement is unknowable.** With server-side sorting/filtering,
  a new row’s page position isn’t known, so mutations are pessimistic + refetch — correctness
  over a 600 ms illusion.
- **Provider-pluggable auth.** JWT lives behind an `AuthProvider` interface; swapping to Firebase
  is a new adapter, not a rewrite. (Same pattern for the LLM/embeddings.)
- **Defence-in-depth $0 cost control.** Free Gemini key (rate-limits, never bills) + a global
  daily budget + per-IP limits + scale-to-zero hosting.
- **Race-safe streaming.** SSE with an `AbortController` stop, capped conversation memory, and a
  DB-persisted message as the source of truth after streaming.

---

## 🖥️ Running locally

**Prerequisites:** Node 20+, Python 3.12+, a Postgres with `pgvector` (or a free Neon project),
a free [Gemini API key](https://aistudio.google.com/apikey).

```bash
git clone https://github.com/Gagan-kshirsagar/opspilot.git
cd opspilot
```

### Backend (`apps/api`)
```bash
cd apps/api
uv venv && source .venv/bin/activate
uv sync --extra dev
cp .env.example .env            # fill in OPSPILOT_DATABASE_URL, OPSPILOT_GOOGLE_API_KEY, OPSPILOT_SECRET_KEY
uv run alembic upgrade head     # create tables
uv run python -m app.seed       # seed teams/users/services/incidents
uv run python -m app.rag.ingest # embed the knowledge base into pgvector
uv run uvicorn app.main:app --reload   # http://localhost:8000/docs
```

### Frontend (`apps/web`)
```bash
cd apps/web
npm install
cp .env.example .env.local      # set NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev                     # http://localhost:3000
```

---

## 🧪 Tests, lint & evals

```bash
# Backend
cd apps/api
uv run pytest -q
uv run ruff check .
uv run python -m app.evals.run --offline   # run the eval harness

# Frontend
cd apps/web
npm run lint && npm run typecheck && npm run test -- --run
```

CI (GitHub Actions) runs lint · typecheck · tests · build · offline evals on every push.

---

## 📁 Project structure

```
opspilot/
├─ apps/
│  ├─ web/                 # Next.js frontend (pure client of the API)
│  │  └─ src/{app,components,hooks,lib,stores}
│  └─ api/                 # FastAPI backend
│     └─ app/{api,services,repositories,models,schemas,rag,agent,evals,core}
├─ .github/workflows/      # web-ci.yml · api-ci.yml
├─ AGENTS.md               # engineering standards
├─ DECISIONS.md            # decision log
└─ README.md
```

---

## 📝 License

MIT — see [`LICENSE`](LICENSE).

<div align="center">
<sub>Built by <a href="https://github.com/Gagan-kshirsagar">Gagan Kshirsagar</a> ·
<a href="https://www.linkedin.com/in/gagankshirsagar">LinkedIn</a></sub>
</div>
