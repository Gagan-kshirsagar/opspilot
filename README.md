# OpsPilot — Step-by-Step Repo Setup (zero → green CI)

Follow these in order. By the end you'll have a monorepo with both apps
scaffolded, standards in place, and CI green — the right foundation before
Antigravity builds features.

Assumes: Node 20+, Python 3.12+, Git, a GitHub account. Commands are for
macOS/Linux; on Windows use Git Bash or WSL.

---

## Step 0 — Prerequisites (verify once)

```bash
node -v      # v20 or higher
python --version   # 3.12+
git --version
# install uv (fast Python package manager) if you don't have it:
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## Step 1 — Create the repo locally

```bash
mkdir opspilot && cd opspilot
git init
git branch -M main
mkdir -p apps
```

---

## Step 2 — Drop in the standards + CI files

Copy these from the `opspilot-repo-setup` bundle into the repo **root**:

```
opspilot/
├─ AGENTS.md
├─ DECISIONS.md
├─ README.md
├─ .gitignore
└─ .github/
   ├─ pull_request_template.md
   └─ workflows/
      ├─ web-ci.yml
      └─ api-ci.yml
```

> Do this now, before any code. These files are what keep everything after
> them consistent.

Commit the foundation:

```bash
git add .
git commit -m "chore: repo standards, CI, and gitignore"
```

---

## Step 3 — Scaffold the frontend (apps/web)

```bash
cd apps
npx create-next-app@latest web \
  --typescript --tailwind --eslint --app --src-dir \
  --import-alias "@/*" --use-npm
cd web
```

### 3a — Install the stack (per AGENTS.md)

```bash
# server state, http, client state, forms, tables
npm install @tanstack/react-query axios zustand \
  react-hook-form zod @hookform/resolvers @tanstack/react-table

# testing + a11y lint (dev)
npm install -D vitest @testing-library/react @testing-library/jest-dom \
  @testing-library/user-event jsdom eslint-plugin-jsx-a11y
```

### 3b — Initialise shadcn/ui

```bash
npx shadcn@latest init      # choose defaults; it wires Tailwind + components dir
npx shadcn@latest add button card input badge dialog table dropdown-menu sonner
```

### 3c — Add the scripts CI expects

Edit `apps/web/package.json` → `"scripts"`:

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "typecheck": "tsc --noEmit",
    "test": "vitest"
  }
}
```

### 3d — Minimal Vitest config

Create `apps/web/vitest.config.ts`:

```ts
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./vitest.setup.ts",
  },
  resolve: { alias: { "@": path.resolve(__dirname, "./src") } },
});
```

Create `apps/web/vitest.setup.ts`:

```ts
import "@testing-library/jest-dom";
```

```bash
npm install -D @vitejs/plugin-react
```

### 3e — One smoke test so CI has something green

Create `apps/web/src/app/__tests__/smoke.test.tsx`:

```tsx
import { describe, it, expect } from "vitest";

describe("smoke", () => {
  it("runs", () => {
    expect(1 + 1).toBe(2);
  });
});
```

### 3f — Verify locally

```bash
npm run lint && npm run typecheck && npm run test -- --run && npm run build
```

All four must pass before you move on.

```bash
cd ../..            # back to repo root
git add . && git commit -m "feat: scaffold Next.js frontend with core stack"
```

---

## Step 4 — Scaffold the backend (apps/api)

Use the **opspilot-backend** bundle you already have (it boots and passes tests):

```bash
# from repo root
cp -r /path/to/opspilot-backend apps/api
cd apps/api
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
```

### 4a — Verify it boots + tests pass

```bash
uvicorn app.main:app --reload    # visit http://localhost:8000/docs, then Ctrl-C
pytest -q                         # 4 tests should pass
ruff check . && ruff format --check .
```

### 4b — Commit

```bash
cd ../..
git add . && git commit -m "feat: scaffold FastAPI backend foundation"
```

> Note: `api-ci.yml` also runs `alembic upgrade head` and `mypy`. Those come in
> Day 2 (DB + migrations). Until then, either (a) hold off pushing changes under
> `apps/api/` so that workflow doesn't run, or (b) temporarily comment the
> `migrations` + `mypy` steps in `api-ci.yml` and re-enable them on Day 2. The
> web workflow is fully green now.

---

## Step 5 — Create the GitHub repo and push

```bash
# create an empty repo named "opspilot" on github.com first (no README), then:
git remote add origin https://github.com/<your-username>/opspilot.git
git push -u origin main
```

Open the repo's **Actions** tab — **Web CI** should run and go green.
Add the badge to the top of `README.md`:

```md
![Web CI](https://github.com/<you>/opspilot/actions/workflows/web-ci.yml/badge.svg)
```

---

## Step 6 — Turn on the guardrails on GitHub

In the repo **Settings**:

1. **Branches → Add branch protection rule** for `main`:
   - Require a pull request before merging.
   - Require status checks to pass → select **Web CI** (and **API CI** once it's
     green in Step 4/Day 2).
2. This enforces the "CI green before merge" rule in `AGENTS.md` — a real
   senior signal, and it stops you (or Antigravity) merging broken code.

---

## Step 7 — Pre-commit hooks (optional but senior)

From `apps/web`:

```bash
npm install -D husky lint-staged
npx husky init
echo "cd apps/web && npx lint-staged" > .husky/pre-commit
```

Add to `apps/web/package.json`:

```json
"lint-staged": {
  "*.{ts,tsx}": ["eslint --fix", "prettier --write"]
}
```

Now formatting/lint runs automatically on every commit.

---

## Step 8 — You're ready for Antigravity

Repo state now:

- ✅ Monorepo: `apps/web` + `apps/api`, both scaffolded and running.
- ✅ `AGENTS.md` standards in place.
- ✅ Web CI green; branch protection on.
- ✅ Clean, conventional commit history.

### The workflow from here (per feature)

```
1. I write the spec (ask me).
2. In Antigravity: "Read AGENTS.md. Here's the spec. Plan first, then wait."
3. Approve the plan → let it generate the slice.
4. Paste the output here → I run a senior code review.
5. Fix what review flags → tests pass → CI green.
6. Explain the slice out loud → log 3 lines in DECISIONS.md.
7. Open a PR (template auto-fills) → merge on green.
```

### First feature to build

**Auth + demo-guest login**, end to end (FastAPI JWT → axios client →
TanStack Query → shadcn login form). It's small, complete, and testable — the
ideal first vertical slice.

---

## Quick reference — the commit sequence

```
chore: repo standards, CI, and gitignore
feat: scaffold Next.js frontend with core stack
feat: scaffold FastAPI backend foundation
# then per feature:
feat(auth): demo-guest + JWT login end to end
...
```

---

## If something breaks

- **Web CI red on lint:** run `npm run lint` locally, fix, recommit.
- **`tsc` errors:** you likely have a stray `any` or missing type — AGENTS.md
  forbids `any`, so type it properly.
- **API CI red on mypy/alembic:** expected until Day 2 — see the note in Step 4b.
- **shadcn init fails:** ensure Tailwind was set up by create-next-app first.

Tell me when Step 5 is green, and I'll hand you the **auth slice spec** to start
Antigravity.
