# Mining Waste-to-Value Platform — Technical Specification

**Version:** 0.2 (supersedes v0.1 — stack moved from Supabase Edge Functions to Python/FastAPI)
**Type:** Multi-tenant SaaS marketplace
**Stack:** React + React Router (frontend) · FastAPI + SQLAlchemy + Postgres (backend) · Redis/Celery · Claude API

> **How to read this document if you're new to Python/FastAPI:** wherever a concept has a
> direct equivalent in the Node/Express/Zod/Supabase world you already know, this spec calls
> it out in a *"Like what you know"* note. You don't need to know Python to understand the
> architecture — the shapes are the same, the syntax is what's new.

---

## 1. Product Summary

A platform that lets mines register waste streams (type, quantity, composition, location,
availability) and matches them against potential buyers/applications (construction materials,
aggregates, cement products, metal recovery, rehabilitation, etc.), using a combination of
rules-based classification and AI-assisted matching.

**Tenant types:**
- **Mine orgs** — supply side. Register waste streams, manage lab data, respond to inquiries.
- **Buyer orgs** — demand side. Browse/search listings, submit requirements, negotiate.
- **Platform admin** — verification, dispute resolution, taxonomy management, oversight.

**First real tenant:** the Samancor slag opportunity — build against it as a live pilot before
generalizing the buyer-side marketplace.

---

## 2. Why the Stack Changed (v0.1 → v0.2)

The original spec put all backend logic in Supabase Edge Functions with Postgres Row Level
Security (RLS) doing tenant isolation. That's a good stack for a lightweight CRUD app. This
project's core value, though, is the **matching engine** — composition chemistry, embeddings,
AI reasoning — which benefits from Python's data/ML ecosystem (pandas, scikit-learn, numpy)
more than it benefits from staying inside Supabase's Deno runtime.

Given you have some Python learning curve ahead but are starting from one pilot tenant (not
under pressure to ship a full marketplace immediately), this is the right time to make the
switch — before there's a working system to migrate.

**What this changes structurally:** FastAPI becomes the *only* thing that talks to Postgres.
The frontend no longer calls Supabase's data API directly — it calls your FastAPI backend,
which calls Postgres via SQLAlchemy. Because of that, **tenant isolation moves from database
RLS policies into FastAPI application code** (Section 6). Supabase Auth and Supabase Storage
are still used — no reason to rebuild authentication or file storage yourself.

---

## 3. High-Level Architecture

```
┌──────────────────────────────┐
│  React + React Router SPA     │
│  (mine portal / buyer portal / │
│   admin portal — role-gated)   │
└───────────────┬───────────────┘
                │ HTTPS / JSON (calls FastAPI, not Supabase directly)
                ▼
┌──────────────────────────────┐        ┌─────────────────────┐
│          FastAPI               │◄──────►│   Supabase Auth      │
│  ┌───────────────────────────┐│        │  (issues JWTs;        │
│  │ API routers (v1)           ││        │   FastAPI verifies    │
│  │ - organizations             ││        │   locally, no        │
│  │ - waste_streams             ││        │   round-trip needed) │
│  │ - applications               ││        └─────────────────────┘
│  │ - inquiries                  ││
│  │ - matching                   ││        ┌─────────────────────┐
│  └───────────────┬─────────────┘│◄──────►│  Supabase Storage     │
│  ┌───────────────▼─────────────┐│        │  (lab reports,        │
│  │ Service layer                ││        │   certificates)       │
│  │ - matching_service.py        ││        └─────────────────────┘
│  │ - classification_service.py  ││
│  │ - claude_service.py          ││
│  └───────────────┬─────────────┘│
└──────────────────┼──────────────┘
                    │ SQLAlchemy (async)
                    ▼
┌──────────────────────────────┐        ┌─────────────────────┐
│   Postgres                     │        │  Redis + Celery       │
│   - PostGIS (location/distance)│◄──────►│  (background jobs:    │
│   - pgvector (embeddings)      │        │   re-matching,        │
│   - core relational tables     │        │   notifications)      │
└──────────────────────────────┘        └─────────────────────┘
                    ▲
                    │
            ┌───────────────┐
            │  Claude API     │  (match reasoning, application
            └───────────────┘   suggestions, composition analysis)
```

**Design principle:** Postgres remains the single source of truth for all tenant data.
FastAPI is the single gatekeeper to it. Nothing else (frontend, Celery workers) talks to
Postgres directly except through the same SQLAlchemy models and the same tenant-scoping
helpers, so there's exactly one place tenant-isolation bugs could hide, not several.

---

## 4. Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| Frontend framework | React 18 + React Router v6 | Unchanged from v0.1 — no reason to touch a working choice |
| State/data fetching | TanStack Query | Now calls FastAPI endpoints instead of Supabase's REST API |
| Styling | Tailwind CSS + shadcn/ui | Unchanged |
| Backend framework | **FastAPI** | Async-native, automatic OpenAPI docs, Pydantic-based validation |
| ORM | **SQLAlchemy 2.0 (async)** | *Like what you know:* this is Python's Prisma/TypeORM equivalent |
| Migrations | **Alembic** | *Like what you know:* Prisma Migrate / Supabase migrations, but for SQLAlchemy |
| Validation / schemas | **Pydantic v2** | *Like what you know:* this is basically Zod — schemas double as request/response contracts |
| Database | Postgres 16 (PostGIS + pgvector) | Same extensions as before; now self-managed via Docker locally, or any managed Postgres in production |
| Auth | Supabase Auth (JWTs verified locally in FastAPI) | Keep Supabase for what it's good at — don't rebuild auth |
| File storage | Supabase Storage | Lab reports, certificates, signed URLs |
| Background jobs | **Celery + Redis** | *Like what you know:* this is Python's BullMQ equivalent |
| AI | Claude API via official `anthropic` Python SDK | Composition reasoning, application suggestions, ranked matches |
| Local dev | **Docker Compose** | Postgres, Redis, FastAPI, Celery worker all spin up with one command |
| Testing | pytest + pytest-asyncio + httpx | *Like what you know:* Jest/Vitest equivalent, with an async-aware test client |
| Code quality | Ruff (lint) + Black (format) + mypy (types) + pre-commit | *Like what you know:* ESLint + Prettier + TypeScript, wired into a pre-commit hook the way Husky would be |
| Payments (phase 2+) | Stripe Connect / Flutterwave / PayFast | Unchanged |

---

## 5. Data Model

The relational shape is unchanged from v0.1 — what changes is *where it's defined*
(SQLAlchemy model classes instead of raw Supabase SQL) and *who enforces access to it*
(FastAPI, not Postgres RLS).

### 5.1 Core tables

```sql
-- Organizations (tenants)
create table organizations (
  id uuid primary key default gen_random_uuid(),
  type text not null check (type in ('mine','buyer','admin')),
  name text not null,
  registration_number text,
  country text,
  location geography(point, 4326),
  verification_status text not null default 'pending'
    check (verification_status in ('pending','verified','rejected','suspended')),
  created_at timestamptz not null default now()
);

-- Org membership (links Supabase auth users to organizations)
create table org_members (
  org_id uuid references organizations(id) on delete cascade,
  user_id uuid not null,               -- Supabase auth.users.id (no FK — different DB/service boundary)
  role text not null check (role in ('owner','admin','member','viewer')),
  created_at timestamptz not null default now(),
  primary key (org_id, user_id)
);

-- Waste stream listings (mine-side)
create table waste_streams (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references organizations(id) on delete cascade,
  title text not null,
  waste_type text not null,               -- e.g. 'slag', 'tailings', 'overburden'
  quantity numeric not null,
  unit text not null,                     -- 'tonnes', 'm3', etc.
  composition jsonb not null default '{}',-- { "SiO2": 34.2, "Fe": 12.1, ... }
  hazard_classification text,
  location geography(point, 4326),
  processing_requirements text,
  available_from date,
  available_to date,
  status text not null default 'draft'
    check (status in ('draft','pending_review','active','matched','archived')),
  embedding vector(1536),                 -- generated from composition + description
  created_by uuid,                        -- Supabase auth.users.id
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Applications taxonomy (construction materials, bricks, cement, etc.)
create table applications (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  category text not null,
  description text,
  typical_composition_requirements jsonb default '{}'
);

-- Matches between a waste stream and an application (rule- or AI-derived)
create table waste_stream_applications (
  waste_stream_id uuid references waste_streams(id) on delete cascade,
  application_id uuid references applications(id) on delete cascade,
  match_score numeric,                    -- 0-1
  source text not null check (source in ('rule','ai')),
  reasoning text,                         -- Claude's explanation, stored for transparency
  created_at timestamptz not null default now(),
  primary key (waste_stream_id, application_id)
);

-- Buyer requirements (demand side)
create table buyer_requirements (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references organizations(id) on delete cascade,
  application_id uuid references applications(id),
  composition_needs jsonb default '{}',
  quantity_needed numeric,
  unit text,
  location geography(point, 4326),
  radius_km numeric default 200,
  embedding vector(1536),
  status text not null default 'active' check (status in ('active','fulfilled','archived')),
  created_at timestamptz not null default now()
);

-- Inquiries (buyer expresses interest in a waste stream)
create table inquiries (
  id uuid primary key default gen_random_uuid(),
  waste_stream_id uuid not null references waste_streams(id),
  buyer_org_id uuid not null references organizations(id),
  status text not null default 'open'
    check (status in ('open','negotiating','accepted','declined','closed')),
  created_at timestamptz not null default now()
);

create table inquiry_messages (
  id uuid primary key default gen_random_uuid(),
  inquiry_id uuid not null references inquiries(id) on delete cascade,
  sender_id uuid not null,                -- Supabase auth.users.id
  body text not null,
  created_at timestamptz not null default now()
);

-- Transactions (phase 2+)
create table transactions (
  id uuid primary key default gen_random_uuid(),
  inquiry_id uuid references inquiries(id),
  amount numeric,
  currency text default 'USD',
  payment_status text default 'pending'
    check (payment_status in ('pending','paid','failed','refunded')),
  logistics_status text default 'not_started'
    check (logistics_status in ('not_started','scheduled','in_transit','delivered')),
  created_at timestamptz not null default now()
);

-- Audit trail (compliance-sensitive: composition edits, verification changes)
create table audit_log (
  id uuid primary key default gen_random_uuid(),
  org_id uuid,
  actor_id uuid,                          -- Supabase auth.users.id
  entity_type text not null,
  entity_id uuid not null,
  action text not null,
  before jsonb,
  after jsonb,
  created_at timestamptz not null default now()
);
```

**Note on `user_id` / `created_by` / `actor_id` columns:** these no longer have a foreign key
to `auth.users` because that table lives inside Supabase's own schema, and FastAPI treats
Supabase purely as an identity provider (it trusts the `sub` claim in the JWT). The UUID
values still line up — Supabase's user IDs are just opaque UUIDs to Postgres from FastAPI's
side.

### 5.2 Extensions required
```sql
create extension if not exists postgis;
create extension if not exists vector;
create extension if not exists pgcrypto;
```

### 5.3 SQLAlchemy model conventions

*Like what you know:* a SQLAlchemy model class is the same idea as a Prisma model or a
TypeORM entity — a Python class whose attributes map to table columns.

- One module per table under `app/models/` (`organization.py`, `waste_stream.py`, etc.)
- A shared `Base` declarative class and small mixins (`TimestampMixin` for
  `created_at`/`updated_at`, `UUIDPrimaryKeyMixin` for the `id` column) so every model
  doesn't repeat the same three lines
- Relationships (`waste_stream.org`, `organization.waste_streams`) declared with
  SQLAlchemy's `relationship()`, mirroring the foreign keys above
- Every model gets a matching **Pydantic schema** in `app/schemas/` for API input/output —
  never return a raw SQLAlchemy model from an endpoint; convert it to its Pydantic schema
  first (Pydantic's `model_config = {"from_attributes": True}` makes this a one-liner)

---

## 6. Tenant Isolation (Application Layer)

This is the most important structural change from v0.1, so it gets its own section.

**Old approach (Supabase + RLS):** every table had a Postgres policy like
`org_id in (select org_id from org_members where user_id = auth.uid())`, enforced by the
database itself no matter what client code ran the query.

**New approach (FastAPI):** there is no RLS. Every tenant-scoped database query must
explicitly filter by the current user's organization. This is enforced through one shared
dependency, not repeated ad hoc in every endpoint:

```python
# app/api/deps.py  (conceptual — not yet built)

async def get_current_org(
    user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Organization:
    """Resolves the caller's organization from their JWT, or raises 403.
    Every tenant-scoped endpoint depends on this instead of trusting a
    client-supplied org_id."""
    ...

async def require_org_type(*allowed: str):
    """Dependency factory: require_org_type('mine') blocks buyer/admin tokens
    from hitting mine-only endpoints, e.g. creating a waste stream."""
    ...
```

Every endpoint that touches `waste_streams`, `inquiries`, etc. takes `org: Organization =
Depends(get_current_org)` and filters its query by `org.id` — never by an `org_id` passed in
the request body or query string. **The rule to enforce in code review:** if a query touches
a tenant-scoped table and doesn't reference `org.id` from this dependency, it's a bug.

This is a real trade-off versus RLS: the database will no longer stop a bug from leaking
data across tenants — only application code will. The mitigation is (a) centralizing the
scoping logic in one dependency used everywhere, (b) tests that specifically assert
cross-tenant access is denied (Section 9), and (c) never letting a raw `org_id` from the
client body override the JWT-derived one.

---

## 7. Application Structure

### 7.1 Backend (FastAPI)

```
backend/
  app/
    core/
      config.py          # Settings loaded from env vars (pydantic-settings)
      database.py         # Async SQLAlchemy engine/session
      security.py         # Supabase JWT verification
      logging.py
    models/                # SQLAlchemy ORM models (one file per table)
    schemas/               # Pydantic request/response models
    api/
      deps.py              # get_db, get_current_user, get_current_org, require_org_type
      v1/
        router.py
        endpoints/
          organizations.py
          waste_streams.py
          applications.py
          inquiries.py
          matching.py
    services/
      matching_service.py     # rules engine + pgvector query + Claude call
      classification_service.py
      claude_service.py       # thin wrapper around the anthropic SDK
      tasks.py                 # Celery task definitions
    main.py                    # FastAPI app instance, router registration, CORS
  alembic/
    env.py
    versions/
  tests/
    conftest.py               # test DB fixture, test client fixture
    test_waste_streams.py
    test_tenant_isolation.py   # explicitly asserts cross-tenant access fails
```

### 7.2 Frontend (React) — unchanged from v0.1

```
src/
  app/
    router.tsx              # createBrowserRouter, role-gated route trees
    providers.tsx
  features/
    auth/
    onboarding/
    mine-portal/
    buyer-portal/
    admin-portal/
    matching/
  components/
  lib/
    api-client.ts            # now points at FastAPI, not Supabase's data API
    queries/
    schemas/
  types/
```

---

## 8. Matching Engine Design

Unchanged in concept from v0.1 — only the runtime moves from a Supabase Edge Function to a
FastAPI service module + Celery task.

**Phase 1 — Rules engine (no AI):**
`applications.typical_composition_requirements` stores threshold ranges (e.g. cement clinker
substitute requires `CaO > 40%`, `SiO2 15–25%`). `matching_service.py` checks a new waste
stream's `composition` against all `applications` and inserts rows into
`waste_stream_applications` with `source = 'rule'`.

**Phase 2 — Embedding similarity:**
`classification_service.py` generates an embedding from a text description assembled from
composition + waste_type + processing_requirements, stores it on `waste_streams.embedding`.
Same for `buyer_requirements.embedding`. A pgvector cosine-distance query (`<=>` operator)
shortlists candidates before invoking Claude.

**Phase 3 — Claude reasoning layer:**
For shortlisted candidates, `claude_service.py` calls the Claude API with structured
composition + application data, requesting a ranked match with reasoning (JSON output).
Result stored in `match_score` + `reasoning` with `source = 'ai'`, surfaced in the UI as
"Why this match?"

**Where this runs:** classification/matching is triggered from the waste-stream-create
endpoint but executed as a **Celery background task**, not inline in the request — so
creating a listing responds immediately and matching happens asynchronously, with the UI
polling or receiving a notification when results are ready.

---

## 9. Testing Strategy

*Like what you know:* pytest here plays the same role Jest/Vitest plays in your React work.

- **Unit tests** for `services/` logic (rules engine thresholds, composition parsing) with
  no database involved
- **Integration tests** using a real (test) Postgres database via Docker Compose, exercising
  full API endpoints through `httpx.AsyncClient`
- **A dedicated `test_tenant_isolation.py`**: creates two orgs, asserts org A's token cannot
  read/write org B's waste streams via any endpoint. This is the test suite that replaces
  the safety net RLS used to provide — treat it as non-negotiable, not optional coverage
- Migrations tested by running `alembic upgrade head` against a throwaway database in CI

---

## 10. Local Development (Docker)

```bash
cp .env.example .env
docker compose up --build
```

This starts four services:

| Service | What it is | Port |
|---|---|---|
| `db` | Postgres 16 + PostGIS + pgvector | 5432 |
| `redis` | Redis (Celery broker) | 6379 |
| `backend` | FastAPI, auto-reloading on code changes | 8000 |
| `worker` | Celery worker processing matching/notification tasks | — |

*Like what you know:* this is the same idea as a `docker-compose.yml` you might use to spin
up Postgres + Redis for a Node app — the only difference is the `backend` service runs
`uvicorn` (Python's ASGI server, roughly the role `node` + Express plays) instead of `node`.

Interactive API docs are auto-generated at `http://localhost:8000/docs` (Swagger UI) — useful
while learning FastAPI, since you can call every endpoint from the browser without writing a
frontend request first.

---

## 11. Code Quality Standards

| Concern | Tool | Like what you know |
|---|---|---|
| Linting | Ruff | ESLint |
| Formatting | Black | Prettier |
| Type checking | mypy | TypeScript's compiler, but for Python type hints |
| Pre-commit enforcement | pre-commit hooks | Husky + lint-staged |
| API contracts | Pydantic schemas | Zod schemas |

**Conventions to hold the line on as the codebase grows:**
- Every function that touches the database or an external API is `async def` and awaited —
  mixing sync and async SQLAlchemy calls is a common source of subtle bugs
- Endpoints stay thin: request validation (Pydantic) → call a service function → return a
  response schema. Business logic lives in `services/`, not in `api/v1/endpoints/`
- No raw SQL strings in endpoint code — SQLAlchemy's query builder or well-named service
  functions only, so tenant-scoping filters aren't easy to accidentally omit
- Every new table gets an Alembic migration generated via `alembic revision --autogenerate`,
  reviewed by hand before applying (autogenerate doesn't always get indexes/constraints right)

---

## 12. Build Roadmap

| Phase | Scope |
|---|---|
| 0 | Repo scaffold, Docker Compose, FastAPI skeleton, Supabase Auth integration, `get_current_org` dependency |
| 1 | Mine portal: waste stream CRUD, Storage uploads, admin verification queue |
| 2 | Applications taxonomy + rules-based matching |
| 3 | Buyer portal: browse, requirements, inquiries |
| 4 | pgvector embeddings + similarity search |
| 5 | Claude-powered match reasoning (Celery background tasks) |
| 6 | Payments (Stripe Connect/Flutterwave) + logistics status tracking |
| 7 | Notifications, reporting/analytics dashboards |

**Suggested first real tenant:** the Samancor slag opportunity — build Phases 0–1 against it
as a live pilot before generalizing the buyer-side marketplace.

---

## 13. Glossary (Python/FastAPI ↔ what you already know)

| Term here | Closest equivalent you know |
|---|---|
| FastAPI | Express.js (with built-in validation + docs) |
| SQLAlchemy | Prisma / TypeORM |
| Alembic | Prisma Migrate |
| Pydantic | Zod |
| Celery + Redis | BullMQ + Redis |
| `async def` / `await` | JS `async`/`await` — same concept, Python just requires it more explicitly for DB calls |
| `pip` / `pyproject.toml` | `npm` / `package.json` |
| `uvicorn` | Node runtime + Express server combined (the process that actually serves requests) |
| Ruff / Black / mypy | ESLint / Prettier / TypeScript compiler |
| `Depends(...)` in FastAPI | Middleware / a custom Express `req` decorator, but resolved per-parameter |
