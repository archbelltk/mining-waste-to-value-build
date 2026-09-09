# Roadmap

Source of truth for scope: [spec.md](spec.md) section 12. This file tracks what's actually
been built, checked off as phases complete — not a redesign of the spec's plan.

## Phase 0 — Repo scaffold ✅ (this pass)

- [x] Repo structure (`backend/`, `frontend/`, `docs/`)
- [x] Docker Compose: `db` (Postgres 16 + PostGIS + pgvector), `redis`, `backend`, `worker`
- [x] FastAPI skeleton (`app/main.py`, CORS, versioned router)
- [x] `GET /health` — verifies DB connectivity
- [x] Supabase Auth JWT verification (`core/security.py`) — real verification logic,
      placeholder credentials until a Supabase project exists (see [how-it-works.md](how-it-works.md))
- [x] `get_current_org` / `require_org_type` dependencies (`api/deps.py`)
- [x] `organizations` + `org_members` models and initial Alembic migration
- [x] `GET /organizations/me` — exercises the full auth → tenant-scoping chain
- [x] Celery app instance wired to Redis (no tasks registered yet)
- [x] pytest + httpx test client against a throwaway test database
- [x] Frontend: Vite + React 18 + React Router, TanStack Query, Tailwind v4, shadcn/ui
      conventions, Supabase client, lucide-react icons
- [x] Landing page proving frontend → FastAPI connectivity end to end

## Phase 1 — Mine portal

- [ ] `waste_streams` table + model + Pydantic schemas
- [ ] Waste stream CRUD endpoints (create/list/update, scoped by `get_current_org`)
- [ ] Supabase Storage wiring for lab reports / certificates
- [ ] Admin verification queue (org verification workflow)
- [ ] Mine portal UI: create/list waste streams
- [ ] `test_tenant_isolation.py` — non-negotiable per spec section 9

## Phase 2 — Applications taxonomy + rules-based matching

- [ ] `applications` + `waste_stream_applications` tables
- [ ] `matching_service.py` rules engine (composition threshold checks)
- [ ] Triggered as a Celery background task on waste-stream create

## Phase 3 — Buyer portal

- [ ] `buyer_requirements` + `inquiries` + `inquiry_messages` tables
- [ ] Browse/search listings, post requirements, inquire
- [ ] Buyer portal UI

## Phase 4 — pgvector embeddings + similarity search

- [ ] `classification_service.py` — embeddings from composition + description
- [ ] pgvector cosine-distance shortlist query

## Phase 5 — Claude-powered match reasoning

- [ ] `claude_service.py` — ranked match + reasoning via the Claude API
- [ ] Runs as a Celery background task; "Why this match?" surfaced in UI

## Phase 6 — Payments + logistics

- [ ] `transactions` table
- [ ] Stripe Connect / Flutterwave / PayFast integration
- [ ] Logistics status tracking

## Phase 7 — Notifications, reporting, analytics

- [ ] Notification delivery (Celery-driven)
- [ ] Reporting/analytics dashboards

**Suggested first real tenant:** the Samancor slag opportunity (spec section 1, section 12) —
build Phases 0–1 against it before generalizing the buyer-side marketplace.
