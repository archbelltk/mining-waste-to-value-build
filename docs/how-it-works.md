# How It Works

A walkthrough of the system as it exists right now (Phase 0), for someone comfortable with
Node/React but new to Python. It describes what's actually running, not what's planned — see
[roadmap.md](roadmap.md) for what's next and [spec.md](spec.md) for the full design.

## 1. What's actually running

`docker compose up` starts four containers:

| Service | What it is | Port |
|---|---|---|
| `db` | Postgres 16 + PostGIS + pgvector | 5432 |
| `redis` | Redis — the queue Celery background jobs use | 6379 |
| `backend` | FastAPI, auto-reloading on code changes | 8000 |
| `worker` | Celery worker — currently idle, no jobs registered yet | — |

The frontend is **not** in Docker — you run it directly with `npm run dev` (port 5173) since
Node is already on your machine and Vite's hot-reload is faster outside a container.

## 2. A request's lifecycle

Browser (`localhost:5173`) → `fetch` in `frontend/src/lib/api-client.ts` → FastAPI
(`localhost:8000`) → SQLAlchemy → Postgres. Nothing else talks to Postgres directly — not the
frontend, not Celery workers outside their own service-layer calls — so there's exactly one
place a tenant-isolation bug could hide (spec section 3's design principle).

Concretely, for `GET /organizations/me`:

1. The frontend's `apiFetch()` helper pulls the current Supabase session and attaches
   `Authorization: Bearer <jwt>` if one exists.
2. FastAPI's `get_current_user` dependency (`backend/app/api/deps.py`) decodes that JWT
   locally against `SUPABASE_JWT_SECRET` — no network call to Supabase, since FastAPI already
   has the secret needed to verify the signature itself.
3. `get_current_org` takes the verified user's ID, looks it up in `org_members`, and returns
   their `Organization` row — or a 403 if they don't belong to one.
4. The endpoint function receives that `Organization` as a plain parameter (`Depends(...)`)
   and only ever queries data scoped to `org.id`.

## 3. Why there's no database-level tenant isolation

The original design (spec v0.1) used Postgres Row-Level Security — the database itself
refused to return another tenant's rows, no matter what code ran the query. v0.2 moved that
enforcement into `get_current_org` because the matching engine needs Python's data/ML
ecosystem more than it needs to stay inside Supabase's Edge Function runtime (spec section 2).

The trade-off: a bug in application code *can* leak data across tenants now, in a way RLS
would have blocked. The mitigations, in order of how much they matter:

1. Every tenant-scoped endpoint depends on `get_current_org` — there's one dependency to get
   right, not one check per endpoint.
2. `test_tenant_isolation.py` (arriving in Phase 1, once there's a tenant-scoped table beyond
   `organizations` itself) asserts org A's token can never read/write org B's data.
3. `org_id` is never trusted from a request body or query string — only from the JWT.

## 4. Auth is real, but Supabase isn't configured yet

`.env` ships with placeholder `SUPABASE_URL` / `SUPABASE_JWT_SECRET` values. That means:

- `GET /health` works right now — it doesn't require auth.
- `GET /organizations/me` will correctly return `401` for any request (there's no valid
  secret to verify a real JWT against), but you can't actually sign in and get past it until
  you:
  1. Create a project at [supabase.com](https://supabase.com).
  2. Copy its URL, anon key, and JWT secret (Project Settings → API) into `.env` (root) and
     `frontend/.env`.
  3. Restart `docker compose` and the Vite dev server so they pick up the new values.

Until then, the login page (`/login`) is a placeholder — wiring up the actual Supabase
sign-in flow is Phase 1 work.

## 5. Day-to-day commands

```bash
# Backend + infra
docker compose up --build              # start db, redis, backend, worker
docker compose exec backend alembic upgrade head    # apply migrations
docker compose exec backend alembic revision --autogenerate -m "..."   # new migration
docker compose exec backend pytest -q  # run tests
docker compose logs -f backend         # tail backend logs

# Frontend (outside Docker)
cd frontend && npm run dev             # dev server on :5173
npx tsc -b                             # type-check
```

`http://localhost:8000/docs` is FastAPI's auto-generated Swagger UI — every endpoint can be
called from the browser there without writing any frontend code, which is useful while
learning the shape of the API.

## 6. Where things live, and why

- `backend/app/core/` — settings, DB engine, JWT verification: the stuff every request path
  touches.
- `backend/app/models/` — one file per table (SQLAlchemy). `backend/app/schemas/` — the
  matching Pydantic response shape for each model. Endpoints never return a raw model; they
  return its schema (see `organizations.py` in both directories for the pattern).
- `backend/app/api/deps.py` — the tenant-isolation dependency chain (section 3 above).
- `backend/app/api/v1/endpoints/` — one file per resource; thin (validate → call a service →
  return a schema). There's no `services/` yet because Phase 0 has no business logic to put
  there — it arrives with the matching engine in Phase 2+.
- `frontend/src/features/` — one folder per portal (`mine-portal/`, `buyer-portal/`,
  `admin-portal/`, `auth/`), matching who the screens are for.
- `frontend/src/lib/` — `api-client.ts` (talks to FastAPI) and `supabase-client.ts` (talks to
  Supabase directly, for auth only — never for data, per section 3).
