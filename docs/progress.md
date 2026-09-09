# Progress Log

Dated record of what's actually been built and verified — not a duplicate of
[roadmap.md](roadmap.md)'s checklist, but the narrative behind it: what was done, how it was
proven to work, and what was deliberately left out.

---

## 2026-09-09 — Phase 0: repo scaffold

**Built:**
- Repo initialized (`git init`); spec moved to `docs/spec.md`.
- `backend/`: FastAPI app, SQLAlchemy async models (`organizations`, `org_members` only —
  the minimum needed for `get_current_org`), Alembic migration `0001`, Supabase JWT
  verification, the tenant-scoping dependency chain from spec section 6, pytest suite.
- Custom Postgres image (`backend/docker/postgres/Dockerfile`) combining PostGIS (base
  image) with pgvector (installed via apt) — no single official image ships both.
- `docker-compose.yml`: `db`, `redis`, `backend`, `worker` (Celery app instance, no tasks
  registered yet — nothing to run until Phase 2+).
- `frontend/`: Vite + React 18 + TypeScript, React Router v6, TanStack Query, Tailwind CSS
  v4, shadcn/ui conventions (`components.json`, `cn()` helper, a `Button` primitive),
  `lucide-react` for icons (no emoji anywhere per project convention), Supabase JS client
  (placeholder credentials), an API client that attaches the Supabase session JWT.
- Landing page that calls `GET /health` live, proving frontend → FastAPI → Postgres works
  end to end. Placeholder pages for the mine/buyer/admin portals and login.

**Verified (not just "should work"):**
- `docker compose build` — all four images build successfully.
- `docker compose up -d db redis backend worker` — all four containers start; `db` reports
  healthy before `backend`/`worker` start.
- `docker compose exec backend alembic upgrade head` — migration applies cleanly.
- `curl http://localhost:8000/health` → `{"status":"ok","db":"connected"}`.
- `http://localhost:8000/docs` — Swagger UI loads, lists `/organizations/me`.
- `GET /api/v1/organizations/me` with no auth header → `401` (auth dependency works).
- `docker compose exec backend pytest -q` — 1 passed.
- Frontend: `npx tsc -b` — clean. `npm run dev` serves on `:5173`. Screenshotted with a
  headless-Chromium script (Playwright): landing page renders "Backend ok, database
  connected" with zero console errors; `/mine`, `/buyer`, `/admin`, `/login` all render
  their placeholder content with zero console errors.

**Deliberately deferred (not bugs, not forgotten):**
- `matching_service.py`, `classification_service.py`, `claude_service.py` — no logic exists
  until Phase 2+, so they weren't stubbed out.
- Real Supabase project — `.env` ships placeholder `SUPABASE_*`/`VITE_SUPABASE_*` values;
  `/health` works today, `/organizations/me` needs real credentials to actually authenticate
  anyone (see [how-it-works.md](how-it-works.md)).
- No CI workflow yet — spec section 9 calls for migrations tested in CI; not part of the
  Phase 0 scope agreed with the user.

**Known rough edges hit and fixed during this build:**
- `postgis/postgis:16-3.4`'s bundled Debian security-repo metadata was stale, breaking
  `apt-get update` — worked around with `-o Acquire::Check-Valid-Until=false` (documented
  inline in the Dockerfile; does not disable signature verification).
- The freshly-published `@types/react@19.3.0` / `@types/react-dom@19.3.0` pair had an
  `npm install` resolution glitch under caret ranges — pinned to exact versions.
