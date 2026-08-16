# AGENTS.md — Engineering standards for OpsPilot

**Read this file fully before generating or modifying any code. Follow it strictly.**
Every change must comply. If a request conflicts with these rules, flag the
conflict and propose a compliant alternative instead of silently breaking a rule.

This repo is built to demonstrate the work of a senior (4+ year) engineer.
Consistency, correctness, tests, and clear reasoning matter more than speed.

---

## 0. How to work in this repo

- **Plan before coding.** For any non-trivial change, first output a short plan
  (files to touch, data flow, trade-offs) and wait for approval.
- **Thin vertical slices.** Build one complete feature at a time (UI → API → DB),
  not broad horizontal layers.
- **Every feature ships with tests.** No feature is "done" without them.
- **Never invent APIs.** Verify a library export/method exists before using it.
- **Record decisions.** Any new dependency or non-obvious choice gets 2–3 lines
  in `DECISIONS.md` (what, why, what was rejected).
- **Small commits.** Conventional Commits, one logical change per commit.

---

## 1. Monorepo structure

```
opspilot/
├─ apps/
│  ├─ web/     # Next.js (App Router) frontend — a PURE client of the API
│  └─ api/     # FastAPI backend — owns all business logic and data
├─ .github/    # CI, PR template
├─ AGENTS.md   # this file
├─ DECISIONS.md
└─ README.md
```

- The frontend contains **no business logic** — it renders and calls the API.
- The backend is the **single source of truth** for data and rules.
- Never reach across the boundary (no direct DB access from the frontend).

---

## 2. Frontend rules (apps/web)

### Stack (use these, not alternatives)

- **Next.js App Router + TypeScript (strict)**.
- **Server state → TanStack Query ONLY.** Never fetch server data with
  `useState`/`useEffect`. Never store server data in Zustand.
- **Client/UI state → Zustand ONLY** (modals, sidebars, ephemeral UI).
- **HTTP → a single typed Axios instance** in `lib/api/client.ts` with auth +
  error interceptors. No bare `fetch` scattered in components.
- **UI → shadcn/ui + Tailwind design tokens.** Do **not** add Material UI or any
  second component/styling library. One system only.
- **Forms → react-hook-form + zod**, schema colocated with the form.
- **Tables → TanStack Table** (headless) styled with shadcn.

### Conventions

- TypeScript `strict`. **No `any`.** No non-null `!` without an inline reason.
- API response types must mirror the backend Pydantic schemas.
- Every data view renders **all four states**: loading, empty, error, success.
- Loading uses skeletons sized to the real content (no layout shift).
- Lists use a **stable key** (an id) — **never the array index** for anything
  sortable/filterable/reorderable.
- Guard async work against **stale responses** (request id or AbortController)
  and cancel on unmount.
- **No inline colours** — use Tailwind semantic tokens only.
- Accessibility is required: semantic elements, `<label>`s, keyboard operability,
  `aria-*`, visible focus. Interactive things are real `<button>`/`<a>`/`<input>`.

### Folder layout (apps/web/src)

```
app/            # routes (App Router)
components/
  ui/           # shadcn primitives + shared building blocks
  <feature>/    # feature components
hooks/          # reusable hooks (useDebounce, etc.)
lib/
  api/          # axios client + typed API functions
  query/        # TanStack Query keys + query/mutation hooks
  utils/
stores/         # Zustand stores (UI state only)
types/          # shared TS types
```

---

## 3. Backend rules (apps/api)

### Stack

- **FastAPI, async everywhere.** No blocking I/O in the event loop.
- **Pydantic v2** models for **every** request and response — never bare dicts.
- **SQLAlchemy 2.0 async + asyncpg**; **Alembic** migrations for every schema
  change. No raw SQL in routes.
- **Postgres + pgvector** (app data and embeddings in one DB).

### Layering (keep routes thin)

```
app/
  api/            # routers — thin: validate, call a service, return a schema
  services/       # business logic lives here
  repositories/   # all DB access here (no queries in routers/services elsewhere)
  models/         # SQLAlchemy models
  schemas/        # Pydantic request/response models
  core/           # config, security, logging, rate limiting
  db/             # engine, session
```

- Routers **must not** contain business logic or raw queries.
- Services orchestrate; repositories touch the DB.
- Every endpoint: typed request model, typed response model, explicit error
  handling with correct HTTP status + a typed error body.

### Conventions

- **No secrets in code.** All config via env, namespaced `OPSPILOT_` (a generic
  var like `ENVIRONMENT` must never be able to override app config).
- Type hints on everything; docstrings on public functions/services.
- Deterministic, testable functions — inject dependencies, don't hide them.

---

## 4. Quality bar (applies to both apps)

- **Tests with every feature.** Frontend: component/behaviour tests (React
  Testing Library, query by role). Backend: pytest, happy path + ≥1 failure case.
- **Lint/format clean:** frontend ESLint (incl. `jsx-a11y`) + Prettier; backend
  Ruff + mypy. Code must pass before commit (pre-commit hooks enforce this).
- **CI must be green** before merge: lint, typecheck, test, build.
- **Conventional Commits** (`feat:`, `fix:`, `chore:`, `test:`, `docs:`, …).
- Update `README.md` when structure changes; update `DECISIONS.md` for choices.

---

## 5. Hard "do NOT" list

- ❌ Do not add Material UI or a second UI/styling library. shadcn + Tailwind only.
- ❌ Do not fetch server data with `useState`/`useEffect` — use TanStack Query.
- ❌ Do not put server data in Zustand.
- ❌ Do not use the array index as a React key for dynamic lists.
- ❌ Do not leave async effects without cancellation/stale-response guards.
- ❌ Do not put business logic or raw SQL in FastAPI routers.
- ❌ Do not return bare dicts from endpoints — use Pydantic response models.
- ❌ Do not commit secrets or hard-code config.
- ❌ Do not add a dependency without a line in DECISIONS.md.
- ❌ Do not ship a feature without tests and all four UI states.
- ❌ Do not invent library APIs — verify they exist.

---

## 6. Definition of done (per feature)

- [ ] Matches the approved plan and this file.
- [ ] Types complete and accurate (no `any`); FE types mirror BE schemas.
- [ ] All four UI states handled (FE); typed errors handled (BE).
- [ ] Tests written and passing; at least one failure/edge case covered.
- [ ] Lint, typecheck, format all clean.
- [ ] Accessibility checked (keyboard + labels + roles).
- [ ] Migration added if schema changed.
- [ ] DECISIONS.md updated if a choice was made.
- [ ] Small, conventional commit(s) with clear messages.
