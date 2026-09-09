# User Journeys

Forward-looking, across all 7 phases — unlike [roadmap.md](roadmap.md) and
[progress.md](progress.md), this doesn't describe what's built yet. It's the reference point
each phase's screens and endpoints should serve: for any new feature, ask which step below it
supports. Derived from [spec.md](spec.md) sections 1 and 12.

## Mine org (supply side)

1. **Sign up & get verified** — registers the org, submits registration details; platform
   admin reviews and sets `verification_status` to `verified` before the org can list anything
   (Phase 0 has the `organizations`/`org_members` tables this rests on; the verification queue
   UI is Phase 1).
2. **List a waste stream** — type, quantity, composition (lab data), location, availability
   window; uploads lab reports/certificates to Supabase Storage (Phase 1).
3. **See matches** — rule-based matches appear immediately after listing (Phase 2); richer
   AI-reasoned matches with an explanation ("Why this match?") follow once embeddings + Claude
   reasoning are online (Phases 4–5).
4. **Respond to inquiries** — a buyer expresses interest; the mine org negotiates via
   `inquiry_messages`, accepts or declines (Phase 3).
5. **Transact & track logistics** — once a deal is accepted, payment and delivery status are
   tracked through to `delivered` (Phase 6).
6. **See it in reports** — org-level dashboards: listings, match rates, inquiry volume
   (Phase 7).

## Buyer org (demand side)

1. **Sign up & get verified** — same admin-verification gate as mine orgs.
2. **Find supply** — either browse/search active `waste_streams` listings directly, or post a
   `buyer_requirement` (composition needs, quantity, location + radius) and let matching come
   to them (Phase 3).
3. **See matches** — same rule → embedding → AI-reasoning progression as the mine-org side,
   just matched against their requirement instead of a listing (Phases 2, 4–5).
4. **Inquire & negotiate** — opens an inquiry against a specific waste stream, messages back
   and forth, moves it to `accepted` or `declined` (Phase 3).
5. **Transact & track logistics** — payment + delivery tracking, same as the mine-org side
   (Phase 6).

## Platform admin

1. **Verify organizations** — review pending mine/buyer org registrations, set
   `verification_status` (`verified` / `rejected` / `suspended`) (Phase 1).
2. **Manage the applications taxonomy** — define/edit `applications` (construction materials,
   cement products, metal recovery, rehabilitation, etc.) and their
   `typical_composition_requirements`, which the Phase 2 rules engine checks listings against
   (Phase 2).
3. **Resolve disputes** — intervene on stuck/contested inquiries or transactions (Phase 6, once
   transactions exist to dispute).
4. **Oversight & reporting** — platform-wide view: verification queue health, match quality,
   transaction volume (Phase 7).

## Pilot framing

Per spec sections 1 and 12, the Samancor slag opportunity is the first real tenant: build the
mine-org journey through Phase 1 against that one real listing before generalizing the
buyer-side marketplace to arbitrary tenants.
