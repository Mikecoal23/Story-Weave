# StoryWeave — Product & Sprint Roadmap

_The durable, versioned plan for StoryWeave: an adaptive, phoneme-aware story generator for early readers. This is the working decision record and end-to-end roadmap — update it as work progresses, in the same PR as the work it describes. Initialized 2026-09-28, ahead of Sprint 1. Restructured 2026-10-09 at Sprint 1 close (see the Decisions Log entry for why)._

**How to read this file**

| If you want to know… | Read |
|---|---|
| What the product is and who owns what | §1 Scope & Team |
| What actually works in the repo *today* | §2 Current State |
| Which tools/libraries are settled and why | §3 Locked Stack |
| What's undecided and who has to decide it | §4 Open Questions |
| What happens when | §5 Sprint Calendar |
| What to build next | §6 Sprints → **Sprint 2** |
| Why any past choice was made | §7 Decisions Log |

**Two rules that keep this file honest:**
1. **Open work lives in exactly one place** — the sprint it's assigned to now. A closed sprint is a retrospective with no live checkboxes, so an unchecked box always means "still to do," never "moved" or "abandoned."
2. **Every choice gets a dated Decisions Log entry with its reasoning.** Decisions are reversed by a new entry, never by editing an old one.

For lightweight, session-to-session working state (velocity, active blockers, "what was I doing"), see `context_sync.md` — that file is git-ignored and never committed; this one is the source of truth.

---

## 1. Scope & Team

StoryWeave listens to a child (grades 1–3) read aloud, uses speech recognition to diagnose exactly which phonemes/words trip her up, and generates a brand-new short story built primarily from phonics patterns she has already mastered plus a small number of "stretch" patterns — repeating every session, so "finishing a book" always leads into a fresh, personalized one. A lightweight caregiver dashboard surfaces what a child is currently working on in plain language, with concrete at-home practice suggestions.

**Baseline scope (Variation 1 — Real-Time Adaptive Reader, per the finalized proposal):** diagnosis and story generation both happen live, within a single session. Two primary users: the child and their caregiver. An instructor/classroom view is an explicit **reach goal**, attempted only if the baseline is done early (Sprint 4).

| # | Component | Owner |
|---|---|---|
| 1 | Speech & Phoneme Diagnostic Pipeline | Michael |
| 2 | Adaptive Difficulty Engine | Shokhina |
| 3 | Constrained Story Generation Module | Shokhina |
| 4 | Child Read-Aloud Interface & Parent/Instructor Dashboard | Hailey |

---

## 2. Current State — as of 2026-10-09

_What is actually true in the repo right now, so nobody has to reconstruct it from checkboxes. Update this section at every sprint boundary._

### Works, verified by running it

| Layer | State |
|---|---|
| Local stack | Docker Compose Postgres + FastAPI boot together; `GET /health` → `{"status":"ok"}`; `/docs` serves |
| Database | 13-table schema at Alembic head `9cde937f7a48`, applied against **local Docker** Postgres and independently verified |
| API contract | All 8 planned routes registered and visible in `/openapi.json`; every one returns **501** |
| Service seams | All three stubbed with frozen signatures: `score_line_audio`, `process_line_score`, `select_difficulty_target` (all raise `NotImplementedError`) |
| Story generation | `generate_story_draft(patterns, interests, vocab_constraints) -> DraftStory` makes a **real** Anthropic Haiku 4.5 call; 3 pre-authored fallback templates exist with an automated vocabulary-drift test |
| Frontend | Child read-aloud flow (reader, controls, top bar, start/loading/finished), parent dashboard (home, sidebar, patterns-in-progress, try-at-home, week summary, practice tab, child picker), general login, shared PIN keypad — all on mock data |
| Tests | 12 passing, `ruff check` clean, all offline (the LLM is mocked) |

### Does not work yet

- **Nothing is connected to anything else.** No frontend call reaches the backend; no backend route reaches a service function.
- **Nothing points at Neon yet.** Neon is now the locked shared Postgres (2026-10-09, Open Question 9), but `backend/app/core/config.py` and `backend/.env.example` both still default to `localhost:5432` Docker Postgres, and the migration has only ever been applied against Docker. The `.agents/skills/neon-*` files, `neon.ts`, and the root `package.json` do **not** connect anything — see the Decisions Log entry for what's actually required.
- **Zero seeded rows.** `phonics_pattern`, `vocabulary_word`, `vocabulary_word_pattern` are empty tables, so there is no controlled vocabulary to validate against. Blocked on the all-three ratification session, which has now slipped two sprints.
- **No Speechace call exists.** Both scoring bodies are `NotImplementedError`.
- **No controlled-vocabulary validator, no regenerate loop, no fallback wiring.** The LLM can draft a story; nothing checks it.
- **`select_difficulty_target` has no body**, so there is no diagnosis → generation handoff.
- **Branch fragmentation:** no single branch has both the newest UI and the newest backend. `dev` has the newest backend with the old UI; `UXbranch` has the newest UI but merged `dev` before the scoring stubs and the generation work landed. `main` is stale behind both.

### The one-sentence summary

Three healthy, well-contracted components that have never spoken to each other, sitting on an unseeded database across three branches.

---

## 3. Locked Stack & Infrastructure Decisions

Quick-reference summary. Full rationale for each lives in §7 Decisions Log.

| Layer | Decision | Status |
|---|---|---|
| Database | PostgreSQL | Locked (pre-existing) |
| Hosted / shared database | **Neon** (serverless Postgres) — the team's shared integration + demo database, and the one place seeded vocabulary lives. Alembic migrations use Neon's **direct** endpoint; the app uses the **pooled** (`-pooler`) one. | **Locked** (2026-10-09, Open Question 9) |
| Backend web framework | FastAPI | **Locked** |
| Backend DB access | SQLAlchemy (sync ORM) + Alembic for migrations. Raw SQL via `op.execute()` remains available inside any migration, and raw queries remain available anywhere the ORM isn't a good fit. | **Locked** |
| Postgres driver | `psycopg` (v3, `[binary]` build) | **Locked** (2026-10-05) |
| Python dependency/env manager | `uv`, application-style (`package = false`), `required-version = ">=0.12.23"` | **Locked** |
| Frontend framework | Vite + React 19 + TypeScript (already scaffolded in `frontend/`) | Locked (pre-existing) |
| Frontend styling | **Plain CSS** — the Tailwind decision is reversed (2026-10-09) | **Locked** (2026-10-09, supersedes 2026-09-28) |
| Local dev database | Docker Compose (one `docker-compose.yml` at repo root) — **retained, with a narrowed job**: running the test suite and offline/throwaway work. Tests must not run against the shared Neon database. | **Locked** (narrowed 2026-10-09) |
| External APIs | Speechace (speech-to-text + phoneme pronunciation scoring), Open Library (book/vocab metadata), Merriam-Webster (dictionary/thesaurus for controlled-vocabulary checks) | Locked (pre-existing, per proposal) |
| Story-generation LLM | Anthropic Claude, Haiku 4.5 tier (`claude-haiku-4-5-20251001`), isolated behind `generate_story_draft(...)` | **Locked** (2026-10-07, Open Question 5) |
| Frontend routing | A `useState` screen switch — **no** `react-router-dom`. Does **not** imply a data-fetching choice (Open Question 1 is still open). | **Locked** (2026-10-08, Hailey) |
| Git integration branch | `dev` — feature branches target `dev`, not `main`. `main` is currently stale; don't branch from it until it's caught up. | **Locked** (2026-10-08) |
| Backend testing | `pytest` | **Locked** (in use, 12 tests) |
| Backend lint/format | Ruff (lint + format) | **Locked** (in use) |
| Frontend lint | ESLint (scaffolded in `frontend/`) | Locked (pre-existing) |
| Frontend testing | Vitest + React Testing Library | **Proposed** — confirm in Sprint 2 (§6) |

---

## 4. Open Questions Register

One table, newest first within each group. Resolved items move to §7 Decisions Log with a date rather than being deleted, so the "why" survives.

**On the numbering:** a retired number is never reused and never resequenced — it just disappears from this table. So "Open Question 9" means the same thing forever. That's why the numbers have gaps (3–7, 9 and 10 are resolved); the gaps are the feature, not a formatting error.

| # | Question | Owner | Blocks | Decide by |
|---|---|---|---|---|
| **1** | **Frontend state/data-fetching approach** — plain `fetch` + Context vs. TanStack Query vs. Redux/Zustand. Hailey's `useState`-routing call does **not** cover this; routing ≠ data-fetching. | Hailey | **Hard-blocks** every frontend/backend wiring task in Sprint 2 | **Sprint 2, day 1–3** (Gate G2) |
| **12** | **What is the login model** — a profile picker with no password, or real accounts? The 2026-09-30 decision (OQ6) chose a profile picker, but Hailey's general-login screen makes it concrete: does that screen list profiles to tap, or is it a credential form? Determines what the login screen calls and whether `caregiver` needs credential columns at all. | All three | The login screen's API wiring | **Sprint 2, day 1–3** |
| **14** | **`WordStatus` mapping** — Hailey's UI states (`neutral` / `correct` / `retry`) ↔ Michael's `WordScore.status` (`mastered` / `shaky` / `missed`). Undefined on both sides; the reader cannot render a score without it. Raised 2026-10-09 as its own question because it was buried as a checklist line and is a 10-minute decision blocking a core Sprint 2 path. | Michael + Hailey | The reader rendering real scores | **Sprint 2, day 1–3** (Gate G3) |
| **11** | **Should `GET /caregivers/{child_id}/dashboard` be renamed?** Caregiver-named but keyed on a child id, returning child data. Free to change now (it's a 501 stub nothing consumes), expensive once the UI calls it. Deliberately not decided unilaterally by the route's author. | All three | Nothing yet — but cost rises the day it's implemented | **Before the dashboard endpoint is written** (Sprint 2) |
| **13** | **PIN policy details** — (a) must a child's PIN differ from the parent's, enforced server-side? (b) what is the parent's own PIN-reset path? (c) what does a throttled/locked-out response look like, given the child side must never lock a child out while the parent side should? | Shokhina (routes/schema) + Hailey (UX) | The verify-route implementations | **Sprint 3** (moved with the PIN feature — see Sprint 2's scope cut) |
| **15** | **What's the working convention for one shared database?** Three people against one Neon database needs rules the local-Docker setup never required: who runs `alembic upgrade head` against it, what happens when two migrations are authored in the same week, whether each developer gets their own Neon branch (Neon supports cheap database branching — the bundled `neon-postgres-branches` skill covers it) or everyone shares one, and who owns re-seeding if the data gets mangled mid-sprint. Raised 2026-10-09 as the real remaining question once Neon was confirmed. | Michael (DB owner) + all three | Seeding (and therefore the validator) — it decides *where* the seed lands and who may re-run it | **Sprint 2, day 1–3** (fold into Gate G1, same meeting) |
| **2** | **Deployment/hosting target.** | All three | Nothing until Sprint 4 | Sprint 4 |
| **8** | **COPPA / children's-data considerations.** Recording a child's voice and storing a phonics profile triggers children's-online-privacy obligations (parental consent, data minimization, no behavioral tracking) *if* StoryWeave is ever used by real families outside the classroom demo. **Updated 2026-10-09:** the Neon decision makes this slightly less hypothetical — children's reading data now leaves the laptop and is stored with a third-party host, so the honest answer to "where does a child's data live" is no longer "only on our machines." Still not a semester-grading concern; use test/placeholder child names during usability sessions rather than real ones, which costs nothing and is the whole mitigation at this scale. | — | Nothing | Out of semester scope; awareness only |

**Resolved:** #3 audio capture, #4 Speechace pattern, #6 auth/session model, #7 sprint calendar (all 2026-09-30); #10 `uv.lock` revision (2026-10-06); #5 LLM provider (2026-10-07); #9 the Neon files / hosted database (2026-10-09). See §7.

---

## 5. Sprint Calendar

Dates come from the proposal's Gantt and have **not** moved. Only sprint *contents* have been recalibrated (2026-10-08 and 2026-10-09).

| Sprint | Dates | Mid-sprint review | Theme | Status |
|---|---|---|---|---|
| 1 | Sep 28 – Oct 9 | Oct 2 | Foundations: schema, contracts, seams, skeleton UI | **Closed** — partially delivered |
| 2 | **Oct 9 – Oct 23** | **Oct 16** | **Integration: make one path work end to end** | **Active** |
| 3 | Oct 23 – Nov 6 | Oct 30 | Adaptive engine, generation quality, PINs, usability testing | Not started |
| 4 | Nov 6 – Nov 20 | Nov 13 | Week 1: absorb slippage. Week 2: hard feature freeze, polish | Not started |
| Wrap-up | Nov 20 → | — | Project site, testing results, video, final presentation | Not started |

Per-sprint deliverables each include: mid-sprint review, Peer Eval N, Journal Entry N, and a sprint report.

---

## 6. Sprints

### Sprint 1 — CLOSED 2026-10-09 _(retrospective — no open work lives here)_

**Goal as written:** go from an empty scaffold to a thin but *real* vertical slice — a child reads a line, gets it scored against Speechace, sees it reflected in a caregiver dashboard, and finishes a session into a freshly generated story, even if every piece is rough.

**Outcome:** the foundations landed and are genuinely solid; the vertical slice did not. All four components exist in contract form, none are connected.

| Stage | Planned | Landed |
|---|---|---|
| 0 — Environment/scaffold | Runnable local stack verified by all three | **Mostly.** Backend, Docker, Alembic, `/health`, `.env.example` done. Frontend tooling, README rewrite, and the 3-person parity check did not — all rehomed into Sprint 2 below. |
| 1 — Schema, contracts, seams | Ratified pattern list, migration, route stubs, service seams | **Done except the ratification session.** 13-table migration applied and independently verified; all 8 route stubs registered; all three seams stubbed with frozen signatures. The pattern list was never ratified, so nothing is seeded. |
| 2 — First pass of everything | Working first pass of all four components | **Partial.** Component 3 has a real LLM call plus fallback content. Components 1 and 4 have contracts and UI but no behavior. |
| 3 — Testing/QA | First-pass test suite + integration | **Not started** beyond unit tests written alongside each chunk. Every planned test covered behavior that doesn't exist, so they moved with their features. |

**What each owner delivered:**

- **Michael:** backend scaffold, Docker Compose Postgres, SQLAlchemy/Alembic wiring, the full 13-table schema (migration `9cde937f7a48`), and the Component 1 scoring contracts and seams (`ScoreResult`/`WordScore`, `score_line_audio`, `process_line_score`). No Speechace call yet.
- **Hailey:** child read-aloud flow (reader, controls, top bar, start/loading/finished screens), parent dashboard (home, sidebar, patterns-in-progress, try-at-home, week summary, practice tab, child picker), general login, and a shared PIN keypad — all mock data, no API wiring, which was always the plan. Plus a route-by-route audit of the API contract against the real UI that surfaced four contract gaps and an entire missing feature area (PINs) **before a single endpoint existed**.
- **Shokhina:** this roadmap and its decision record; the phonics-pattern starter set and the shared `vocabulary_word`/`vocabulary_word_pattern` design the schema was built on; independent end-to-end verification of the schema branch; the frozen `DifficultyTarget` contract and Component 2 seam; the 8-route API contract in code; Open Questions 5 and 10 resolved; 3 fallback story templates with an automated vocabulary-drift guard; and `generate_story_draft()` calling Anthropic Haiku 4.5 behind an isolated boundary.

**The planning lesson, recorded on purpose.** Sprint 1 asked for a first pass of all four components *and* a working end-to-end integration in two weeks — while Sprint 2 separately listed "first real frontend/backend connection." That contradiction sat in the plan from the start and only became visible when the sprint closed with three healthy, entirely unconnected components. Two things follow, and both are now structural rather than hoped-for: integration gets its own sprint with a single stated goal (Sprint 2), and slack is **scheduled** rather than improvised (Sprint 4 week 1). See the 2026-10-08 and 2026-10-09 Decisions Log entries.

**Honest note for the sprint report:** the Oct 2 mid-sprint review's delivery was never recorded here either way. State plainly in the report whether it happened rather than letting the plan imply it did.

**Demo framing (Oct 9).** Real and demoable: the live schema, the API contract via `/docs`, constrained story generation against a real LLM, and the UI clickthrough on mock data. Not real: any connection between layers, real scoring, seeded vocabulary. The strongest "what was difficult / unexpected" material is duplicate work discovered twice, the unexpected payoff of contract-first stubs (Hailey could audit an API that didn't exist yet and find a whole missing feature area), an unheld 30-minute meeting being the single hardest blocker, a mid-sprint integration-branch change, and this sprint's own over-scoping. Showing the recalibration is a stronger story than claiming it all went to plan.

---

### Sprint 2 — Integration _(Oct 9 – Oct 23, mid-sprint review Oct 16)_ — **ACTIVE**

**The one goal:** _a child reads a line in the real UI, the real backend scores it, stores it, and generates a validated story from the stored profile — one path, end to end, on one branch, on one machine._

Everything below either serves that sentence or is explicitly cut. **Re-scoped 2026-10-09:** the previous draft of this sprint carried 30 open line items for three people in two weeks — more than Sprint 1 had when it over-committed. Cutting it is the whole point of having learned Sprint 1's lesson rather than just writing it down.

#### Definition of done — the only four things that count

1. `POST /sessions/{id}/lines/{n}/audio` accepts a real `MediaRecorder` blob and returns a real `ScoreResult`, persisted.
2. `POST /stories/generate` returns a validated, persisted story; `GET /stories/{id}` retrieves it.
3. The frontend calls both, from one branch, running on one machine.
4. `phonics_pattern` / `vocabulary_word` / `vocabulary_word_pattern` contain seeded rows **in Neon**, so all three developers read the same vocabulary.

If all four are true on Oct 23, the sprint succeeded even if nothing else below got done.

#### Gates — clear these in the first three days or the sprint is at risk

These are cheap, mostly meetings, and each one blocks somebody's main lane. They are first because Sprint 1's hardest blocker turned out to be an unheld meeting, not any piece of code.

- [ ] **G1 — Hold the all-three phonics-pattern ratification session.** Ratify the ~9 starter patterns and the sight-word list from `sprint1_phonics_pattern_starter_set.md`. Also settle `DRAFT_GLUE_WORDS` (the 16 basic function words the fallback templates needed to form sentences at all): fold them into the sight-word list, since they play the same role — ungraded, never pattern-attributed — or name a different "always-allowed" mechanism. **Has slipped two sprints.** Blocks G1-dependent seeding, the validator's real behavior, and re-validating the fallback templates. Cheapest high-impact item on the whole roadmap. *(all three)*
- [ ] **G2 — Resolve Open Question 1: frontend data-fetching.** Hard-blocks every wiring task in Hailey's lane. *(Hailey)*
- [ ] **G3 — Resolve Open Question 14: the `WordStatus` mapping.** A 10-minute decision that blocks the reader rendering any real score. *(Michael + Hailey)*
- [ ] **G4 — Consolidate branches.** Get one branch carrying both the newest UI and the newest backend. Measured 2026-10-09: `UXbranch` is missing exactly one commit from `dev` (Michael's `090d9a0` scoring stubs) and holds 7 commits `dev` doesn't (all UI); `shokhina/stage2-story-generator` is pushed and current but not merged into `dev` at all; `dev` is 6 ahead of `main`. So consolidation is two merges into `dev` — `UXbranch` and `shokhina/stage2-story-generator` — not a rebuild. Decide at the same time whether `main` ever gets caught up, and whether direct pushes to `dev` are the norm or were a one-off. Without this there is no shared place for an integration to happen. *(all three)*
- [ ] **G5 — Decide Open Question 11** (dashboard route naming) and **Open Question 12** (login model). Both are free today and costly the moment an endpoint or a login screen is wired. *(all three)*
- [ ] **G6 — Decide Open Question 15: the shared-database working convention.** Who applies migrations to Neon, Neon branch-per-developer vs. one shared database, and who owns re-seeding. Fold into the G1 meeting — it's the same conversation and it decides where the seed actually lands. *(Michael + all three)*

#### Michael — Component 1: make scoring real

- [ ] Implement the real `score_line_audio(audio_bytes, expected_line) -> ScoreResult` body: call Speechace with the line's audio and expected text, parse the phoneme-level response into a `ScoreResult`.
- [ ] Implement the real `process_line_score(...)` body: persist to `reading_attempt`, attribute each scored word to its pattern(s) via `vocabulary_word_pattern`, update `phonics_mastery`. **Word-level attribution, not phoneme-position** — phoneme↔pattern mapping stays deferred (Sprint 3), per the 2026-09-30 decision.
- [ ] Wire `POST /sessions/{session_id}/lines/{line_number}/audio` to call both synchronously, returning `{"status": "complete", "result": {...}}`.
- [ ] Sight-word handling: look the read word up in `vocabulary_word`; if `is_sight_word = true`, skip it — no pattern credit, no penalty.
**Michael — wire up Neon (small, but on the critical path)**

Pulled into Sprint 2 despite the scope cut, because it passes the same test everything else did: definition-of-done item 4 depends on it, and it *removes* work — the vocabulary gets seeded once instead of three times, and the demo stops depending on whose laptop has a healthy Docker container.

- [ ] Point `DATABASE_URL` at Neon. Per the bundled `neon-postgres` skill's own pooled-vs-direct table, **Alembic must use the direct endpoint** and the app should use the **pooled** (`-pooler`) one — migrations need session state that pgBouncer's transaction pooling doesn't preserve. This means `alembic/env.py` and `app/core/config.py` may need two different URLs, not one.
- [ ] Update `backend/.env.example` with a placeholder Neon URL and a comment naming which endpoint goes where. The real connection string contains a live password and belongs only in `.env` — which is correctly git-ignored today and must stay that way. Don't paste it into a PR, an issue, or a commit message; if it ever leaks, rotate it in the Neon console rather than hoping.
- [ ] Run `alembic upgrade head` against Neon and confirm all 13 tables plus `alembic_version` land, the same way the Docker run was verified.
- [ ] Decide the fate of the root-level `neon.ts`, `package.json`, and `package-lock.json`. `neon.ts` is an empty `defineConfig({})` stub and the two `@neon/*` packages are npm dependencies declared at the root of a repo whose backend is Python — so they aren't what connects us to Neon, and a stray root `package.json` can confuse tooling that expects the frontend's. Either wire them into something real and document how, or delete them and keep the `.agents/skills/` docs, which are the genuinely useful part.

#### Shokhina — Components 2 & 3: close the generation loop

Ordered as a dependency chain — each item unblocks the next, so work them top to bottom.

- [ ] **Seed the ratified patterns + vocabulary** into `phonics_pattern` / `vocabulary_word` / `vocabulary_word_pattern`, **in Neon**. Unblocked by G1 (the word list) and G6 (where it lands and who may re-run it); blocks everything after it, since "controlled vocabulary" is defined as the rows in these tables, not a separate Python list (2026-09-30 decision — one shared source so Michael's scoring path and the generator can't drift apart). Write it as an idempotent, re-runnable seed script rather than a one-off manual insert: it's a shared database now, the word list will change after the first ratification pass, and re-seeding must not mean dropping tables everyone else is working against.
- [ ] **Controlled-vocabulary validator** — reject any draft containing a word outside the seeded vocabulary.
- [ ] **Regenerate loop** — retry with feedback on rejection, max N attempts (default 2–3, tunable).
- [ ] **Template-fallback wiring** — fire one of the 3 existing `FALLBACK_TEMPLATES` after N consecutive rejections, so a session never dead-ends. The templates' content already exists; only the wiring is missing.
- [ ] **Re-validate the 3 fallback templates** against the actually-seeded vocabulary. They were authored against the starter-set doc's *illustrative* example words, so this pass is expected to find drift — that's why the automated test exists.
- [ ] **Naive `select_difficulty_target()` body** — reuse mastered patterns, pick N stretch patterns by `sequence_order`. The real adaptive engine replaces this body (and only the body) in Sprint 3.
- [ ] **Wire `POST /stories/generate` and `GET /stories/{id}`** to the pipeline.
- [ ] **List-children endpoint** — `GET /caregivers/{id}/children`, or children embedded in the caregiver-session response. Required by both the child picker and the parent child-dropdown, and the slice needs a real child id to generate against.

#### Hailey — Component 4: the first real wire

- [ ] Replace `LoadingScreen`'s timer with a real `POST /stories/generate` call and render the returned story in the reader. **This is the single most important frontend task in the sprint** — it is the first time any UI touches the backend.
- [ ] Mic button: `MediaRecorder` → webm blob → multipart upload to the per-line audio route, per the 2026-09-30 per-line capture decision.
- [ ] `ChildPicker` passes a child id (or the whole child object) rather than a name — sessions and story generation both require an id.
- [ ] Render real word states in the reader using the G3 mapping.
- [ ] Build the navigation flow: login → parent/child → dashboard or reader, with switch-reader and log-out paths. **PIN gates stay on mock behavior this sprint** (see the scope cut below), so build the flow with the gate as a pass-through seam.
- [ ] Second-pass dashboard against real data, *only if* the dashboard endpoint returns something before Oct 23. Otherwise this slides to Sprint 3 without penalty.

#### All three — the integration milestone (moved here from Sprint 1)

- [ ] Backend path end to end: a completed session's stored mastery profile + child interests → `select_difficulty_target()` → `generate_story_draft()` → validated story persisted and retrievable. Demonstrable via API calls before the frontend is connected.
- [ ] Joint smoke-run of the full path against the local stack, all three present.

#### Tests — carried from Sprint 1 Stage 3, now that the features exist

- [ ] Component 1: feed a known audio sample with pre-labeled miscues through `score_line_audio()`; assert flagged phonemes match the labels within tolerance. One or two samples is enough — the developmental-articulation sample set stays a Sprint 3 deliverable.
- [ ] Component 3: assert the validator rejects a story containing an out-of-vocabulary word before it is returned.
- [ ] Component 3: assert the template fallback fires after N rejections and returns a valid story.
- [ ] Integration: the end-to-end path runs clean.
- [ ] Confirm Vitest + React Testing Library (the last unconfirmed tooling default) with one smoke test, or formally drop frontend testing for the semester.

#### Stage 0 housekeeping — rehomed here because it was orphaned

These were unchecked in Sprint 1 and appeared in no carryover list, which meant they were silently lost. They are small; do them when a lane is blocked on a gate.

- [ ] `README.md` rewritten with real setup instructions: install `uv`, `docker compose up`, `alembic upgrade head`, run backend, run frontend.
- [ ] Frontend fetch/display of `/health` as a wiring smoke test — effectively free once G2 lands, and it de-risks the real wiring.
- [ ] **Environment parity check:** all three members independently run `docker compose up` + backend + frontend and confirm `/health` renders in the browser. This never happened, and an integration sprint is exactly when a machine-specific setup failure would cost the most.
- [x] Delete the superseded `shokhina-stage0-env-setup` remote branch — **done** (verified gone from `origin` 2026-10-09; `origin/michael-dev` and `origin/chore/storyweave-scaffold` are also gone, so everyone should `git fetch --prune` to clear stale local tracking refs).

#### Explicitly NOT in Sprint 2 — the scope cut

Cut on 2026-10-09 to protect the four definition-of-done items. Nothing here is cancelled; each has a named home.

- **Parent and child PINs → Sprint 3** (migration, verify routes, throttling, reset flows, creation-time acceptance). This is a full feature area — roughly a third of Shokhina's sprint — competing directly with the validator and route wiring that the vertical slice depends on. The PIN *design* and its security requirements stay locked exactly as decided on 2026-10-08; only the timing moves. Hailey's PIN screens already exist and keep working on mock behavior, so nothing visibly regresses, and the demo risk this sprint is "nothing is connected," not "no PIN."
- **List-stories endpoint → dropped, pending Hailey's confirmation.** Recommendation: drop the child start-screen story picker and have "Start" call `POST /stories/generate` directly. It removes an endpoint from an over-full sprint and it matches the product premise better — finishing a book is supposed to lead into a *fresh* story, not a library browse.
- **Tailwind → dropped entirely.** See the 2026-10-09 Decisions Log entry.
- **Adaptive difficulty engine, generation quality, Open Library / Merriam-Webster vocabulary expansion, decoding-vs-articulation classification → Sprint 3**, as already planned.

**Also due:** mid-sprint review Oct 16, Peer Eval 2, Journal Entry 2, sprint report, demo prep, and a `context_sync.md` refresh reflecting real velocity.

---

### Sprint 3 — Adaptive Engine, Generation Quality, PINs & Usability Testing _(Oct 23 – Nov 6, mid-sprint review Oct 30)_

**Status:** Not started. **Primary owner:** Shokhina (adaptive engine + generation quality + the testing plan, including the expanded child-tester panel).

This is the sprint where the product stops being "first pass" and starts being adaptive. **Capacity warning, stated up front:** this sprint now holds the work displaced from Sprint 2 *plus* its original usability-testing focus *plus* PINs, and most of it lands on one owner. Work it in the order below, and expect the tail to land in Sprint 4 week 1's absorption capacity — that is what the absorption week exists for, not a failure mode.

1. **Parent and child PINs** (moved from Sprint 2 — do these first; they're well-specified and they gate the usability sessions, where siblings reading under each other's profiles becomes a real problem):
   - Schema migration: `pin_hash` on `caregiver` and on `child`, hashed server-side, never stored or returned in plaintext — consistent with the existing hashed `caregiver_session.token_hash`.
   - `POST /caregivers/{id}/verify-pin` and `POST /children/{id}/verify-pin` — verification happens server-side only; the client never receives a PIN or hash to compare locally.
   - Attempt throttling/lockout on both verify routes with a defined throttled-response shape. A 4-digit PIN is 10,000 combinations, so client-side-only protection is not protection.
   - Accept a PIN at `POST /caregivers` and `POST /children` creation time.
   - Guarantee no list or read endpoint ever returns a PIN or its hash.
   - Reset flows for both: parent resets a child's PIN from the dashboard; the parent's own path per Open Question 13.
   - The child side never locks a child out (UI decision); the parent side does.
   - Resolve Open Question 13's sub-decisions before implementing the verify routes.
2. **Schema additions for the difficulty engine** — mastery-confidence scoring and spaced-repetition selection state.
3. **The real adaptive difficulty engine**, replacing the naive `select_difficulty_target()` body. The body only — `DifficultyTarget` is frozen.
4. **Generation quality + interest-matching**, including the Open Library / Merriam-Webster–driven vocabulary expansion.
5. **Decoding-vs-articulation classification + articulation-flag honoring** (Michael) — deferred out of Sprint 1 per the proposal.
6. **Moderated usability sessions with children**, and revisions from that feedback. Michael validates the diagnostic pipeline against the child tester with a lisp and implements the resulting revisions; Hailey supports the sessions and implements dashboard revisions.
7. Mid-sprint review (Oct 30) + Peer Eval 3 + Journal Entry 3 + demo prep.

---

### Sprint 4 — Absorption, then Polish & Final Testing _(Nov 6 – Nov 20, mid-sprint review Nov 13)_

**Status:** Not started. **Primary owner:** Hailey (frontend polish, full integration and testing lead).

**Deliberately split in half at the mid-sprint review (2026-10-08).**

**Week 1 — Nov 6 to Nov 13: absorption.** Reserved capacity for whatever has slipped out of Sprints 2 and 3, rather than pretending nothing will. Also the decision point on the instructor-view reach goal: build it **only if** the baseline is genuinely complete by the Nov 13 review, and decide it *there* rather than drifting into it.

**Week 2 — Nov 13 to Nov 20: polish and final testing only. A hard feature freeze.** No new features, no absorbed carryover.

- Hailey: child + caregiver frontend polish; full-integration testing lead.
- Michael + Shokhina: final integration support; last revisions to the diagnostic pipeline and the difficulty engine/generator respectively.
- Full-path testing against the local stack with all three present.
- Peer Eval 4 + Journal Entry 4 + final sprint report.

**If the Nov 13 review shows the baseline is not complete,** week 2's freeze applies anyway and the reach goal is formally dropped. The freeze exists so there is always a working thing to present — the direct lesson from Sprint 1.

---

### Wrap-Up & Final Presentation _(skeleton)_

Per the proposal's Gantt: GitHub homepage/project website, testing results presentation, video screening, final presentations.

---

## 7. Decisions Log

Chronological, oldest first. Every locked decision in §3 has an entry here with its rationale; resolved Open Questions move here, dated. **Decisions are reversed by adding a new entry, never by editing an old one** — a superseded entry stays, marked as superseded, so the original reasoning survives.

### 2026-09-28 — initial stack

- **Backend web framework: FastAPI.** Chosen over Flask/Django. Rationale: native async fits StoryWeave's I/O-bound integrations with three external APIs (Speechace, Open Library, Merriam-Webster); Pydantic gives free request/response validation, which matters for Component 3's controlled-vocabulary payloads and Component 1's phonics-mastery payloads; auto-generated OpenAPI docs materially help a 3-person team splitting work by component build against a shared, always-accurate contract.
- **DB access layer: SQLAlchemy (sync) + Alembic.** Chosen over async SQLAlchemy and over pure raw SQL. Rationale: autogenerated migrations save real time across a schema that's expected to grow every sprint; sync keeps the mental model simpler for a small team without a clear async-Python need, since FastAPI runs sync DB calls in a thread pool transparently and Postgres latency is not this app's bottleneck (Speechace's API latency is). Raw SQL is not lost: `op.execute()` inside any Alembic migration, and raw queries anywhere in the app, remain fully available whenever the ORM isn't the right tool.
- **Python dependency/env manager: `uv`.**
- **Frontend styling: Tailwind CSS.** Chosen over a component library (MUI/Chakra) or plain CSS. Rationale: fastest path to a custom, playful child-facing UI without fighting a component library's default look; compiles to plain CSS under the hood, so it is a workflow choice, not a capability constraint. — **Superseded 2026-10-09; see that entry.**
- **Local dev Postgres: Docker Compose.** Chosen over a hosted free-tier DB or natively-installed Postgres per machine. Rationale: identical environment for all three teammates and CI, easy to reset, no per-machine version drift, no internet dependency during development.

### 2026-09-30 — architecture review

- **Audio capture & upload: per-line discrete recording.** `MediaRecorder` starts/stops once per line; one blob uploaded per line via `POST /sessions/{id}/lines/{n}/audio`. Chosen over continuous-session-recording-sliced-by-timestamp and over true WebSocket streaming. Rationale: matches the team's own user research directly (both test children wanted feedback after a line, not mid-sentence); Component 4's mic-as-largest-first-tap-target design already assumes a per-line tap-to-record rhythm; avoids inventing audio-slicing logic or streaming infrastructure for a real-time-mid-word feedback capability the product explicitly isn't building toward. _(Resolves Open Question 3.)_
- **Speechace integration pattern: synchronous, built for a contained future migration.** The scoring call happens in-request, not via a queue. Chosen over a Celery/RQ-style background job because at this project's real scale (a handful of known families) a queue solves a concurrency/retry problem that doesn't exist yet, and adds a broker + worker process to every teammate's local setup during an already-tight Sprint 1. **Explicit design commitment so this stays cheap to change later:** the Speechace call lives in one isolated service function (`score_line_audio(audio_bytes, expected_line) -> ScoreResult`), and persisting that result lives in a second, separate function (`process_line_score(...)`) the endpoint calls immediately after. A future move to queued execution changes only *how* those two functions are invoked (direct call vs. `.delay()`), not their logic. The audio endpoint's response also carries a `status` field from day one (`{"status": "complete", "result": {...}}`) so a future `{"status": "pending", "job_id": ...}` variant is an additive contract change, not a breaking one. Revisit if real usage shows Speechace latency spiking badly enough to hurt the UX. _(Resolves Open Question 4.)_
- **Auth/session model: lightweight profile-picker now, schema shaped for real auth by end of project.** No passwords or login screen for Sprint 1 — a caregiver creates/selects a profile and gets an opaque session token with no credential check. But the schema is built as if real auth were coming, because the team wants it by project end:
  - `caregiver` includes an `email` column (nullable, unused for login now) so it needs no shape change when login is added.
  - A `caregiver_session` table exists from day one — opaque token, `caregiver_id` FK, `created_at`/`expires_at` — minted on profile creation/selection with no password check. Real auth later just inserts a password check *before* minting the same token; the session concept and its relationship to `caregiver`/`child` doesn't change.
  - `child` rows are FK'd to a real `caregiver_id` from the start (not a bare device-picker), so multi-child support and the dashboard's "which child" scoping are already correct, and real auth is additive rather than a relationship rework.

  Chosen over building real auth in Sprint 1 (unnecessary security surface — password hashing, reset flow, rate-limiting — for a component the grading rubric doesn't touch, at the cost of Sprint 1's runway) and over a single hardcoded demo child (wouldn't support the team's own multi-child usability testing). _(Resolves Open Question 6; **amended 2026-10-08** by the PIN decision, and reopened in part as Open Question 12.)_
- **Story generation engine: LLM primary with a template-stitched fallback.** The primary path is an LLM call that drafts a short story from the target phonics patterns, the child's interests, and the allowed controlled vocabulary; a validator checks the draft and retries with feedback on failure. If the validator rejects N drafts in a row (default 2–3, tunable), the system falls back to a small set of pre-authored, guaranteed-valid template stories rather than dead-ending the session. Chosen over LLM-only (no safety net if a regeneration loop never lands — risky in front of real kids during usability testing) and over pure template/slot-based (would inherently maximize the "repetitive content" complaint the team's own app-store review scrape flagged as one of the two most common frustrations). Rationale: matches the architecture already diagrammed in proposal Figure 5 (generate → validate → regenerate-if-invalid → approve — a loop that only makes sense with a non-deterministic generator), directly answers the repetitiveness finding, and gives a hard guarantee that a session always ends in a valid, pattern-labeled story — which also satisfies the caregiver-interview finding that generated text must be validated and labeled before a caregiver trusts it.
- **Sprint calendar confirmed live.** The proposal's schedule is accurate: Sprint 1 mid-sprint review is Oct 2, 2026. The thinner-slice contingency noted earlier is retired. _(Resolves Open Question 7.)_
- **Component 2 seam defined ahead of its build.** `select_difficulty_target(child_id) -> DifficultyTarget` is introduced in Sprint 1 with a naive placeholder body (reuse mastered patterns + pick N stretch patterns by sequence order) so the diagnosis→generation path can be wired end to end before the real adaptive engine exists. Component 2 (Sprint 3) replaces the function body only; `DifficultyTarget` is the frozen contract between Components 2 and 3 and does not change. _(Signature amended 2026-10-05.)_
- **Sprint 1 mastery attribution is word→pattern, not phoneme→pattern; `vocabulary_word`/`vocabulary_word_pattern` replaces the standalone `sight_word` table.** Caught during architecture review: `sprint1_phonics_pattern_starter_set.md` correctly defers phoneme↔pattern mapping to Sprint 2 (Speechace scores phonemes; mapping a phoneme-in-position to a `phonics_pattern` is real work). But the first-pass diagnostic pipeline still needs to update `phonics_mastery` this sprint, and the story generator needs a controlled-vocabulary word list this sprint too. Rather than building two separate word lists that could drift, or inventing phoneme-level attribution early, both needs are met by one shared table: `vocabulary_word (word, is_sight_word)` + a many-to-many `vocabulary_word_pattern (vocabulary_word_id, phonics_pattern_id)` junction. Michael's scoring path attributes a read word to a pattern by looking it up here (word-level, not phoneme-position-level); the generator reads the same table as its controlled vocabulary. A sight word is now a row with `is_sight_word = true` and zero junction rows, which still satisfies the starter-set doc's correct concern that a sight word must never be modeled as a trainable phonics pattern — it just collapses two lookup tables into one. Phoneme-level attribution remains Sprint 3 scope.
- **`phonics_pattern` gets a surrogate PK and gapped `sequence_order` values.** `phonics_pattern_id` (serial) is the PK with `code` as a separate `UNIQUE NOT NULL` column, matching every other table's surrogate-key convention and avoiding a cascading FK rewrite if a `code` ever changes. `sequence_order` is seeded in multiples of 10 rather than 1..9, because the starter-set doc's own backlog implies short-vowel CVC patterns will eventually need to be inserted *before* the digraph/blend-first starter set — sequential integers would force a renumbering migration; gapped integers absorb it for free. Nothing reads `sequence_order` until Component 2 (Sprint 3), so this is zero-cost insurance.
- **`caregiver_session` token must be cryptographically random.** Since Sprint 1 ships session tokens with no password check gating them, the token *is* the entire access boundary today. Generate it with something like `secrets.token_urlsafe(32)` — never sequential, never derived from caregiver/child data. `expires_at` is stored per the schema plan but is **not enforced** by any Sprint 1 task; noted explicitly so nobody later assumes expiry is real before it's actually checked somewhere.

### 2026-10-05 — Stage 0/1 build, and a duplicate-work discovery

- **Backend is a `uv` *application* (`package = false`), not the `src/`-layout library `uv init` defaults to.** `uv init` scaffolds a publishable library (a `src/storyweave_backend/` package, a `[project.scripts]` entry point, a `[build-system]` section) — the wrong shape for a FastAPI service with a fixed `backend/app/...` layout. Set `[tool.uv] package = false` and deleted the generated `src/` tree so `app/` stays the one backend package root: no build backend, no packaging metadata to maintain for something never installed as a dependency elsewhere.
- **Postgres driver: `psycopg` v3, `[binary]` build.** Chosen over `psycopg2` (legacy, no longer recommended for new SQLAlchemy 2.x projects) and over the non-binary `psycopg` build (requires local libpq headers / a C toolchain per machine — unnecessary friction for a team that just needs `uv sync` to work identically everywhere). Revisit only if a deployment target specifically prefers building from source.
- **`backend/conftest.py` exists solely to make `app` importable by `pytest`.** `backend/tests/` intentionally has no `__init__.py`, so pytest's default import mode puts `tests/` on `sys.path`, not `backend/` — `from app.main import app` failed with `ModuleNotFoundError` until a `conftest.py` was added at the `backend/` root. Pytest always adds a `conftest.py`'s own directory to `sys.path`, so this one empty file is what makes `backend/` importable from any test module, without switching to `src/`-layout or adding `__init__.py` files to `tests/`. Pure plumbing — flagged here only so a future contributor doesn't delete it as "an empty file that does nothing."
- **`pydantic-settings` added ahead of use.** Added in the first Stage 0 commit even though nothing read it yet, because the very next commit needed a typed settings object to load `DATABASE_URL`, `SPEECHACE_API_KEY`, and `MERRIAM_WEBSTER_API_KEY`. Bundling the dependency bump with the scaffold commit avoids a second one-line commit purely for tooling.
- **Discovered and verified Michael's `origin/database` branch already supersedes Stage 0's backend scaffold and most of Stage 1.** After building the Stage 0 scaffold independently (on a now-abandoned `shokhina-stage0-env-setup` branch) and attempting to push it, a GitHub branch-protection error on an unrelated stale `dev` branch led to fetching and inspecting all remote branches — which surfaced `origin/database`, pushed the same day, containing a complete `docker-compose.yml`, `backend/.env.example`, `pydantic-settings`-based config, sync SQLAlchemy engine/session, a full Alembic migration, and a complete Stage 1 schema (`Caregiver`, `CaregiverSession` using a hashed `token_hash` rather than a raw token, `Child`, `PhonicsPattern`, `VocabularyWord`/`VocabularyWordPattern`, `Story`/`StoryPattern`/`StoryLine`, `ReadingSession`, `PhonicsMastery`, `ReadingAttempt`, `ArticulationFlag`) — independently matching this file's own Stage 1 schema plan and the starter-set doc's word→pattern decision almost exactly, in several places with a cleaner implementation than planned here (e.g. the hashed session token, `pythonpath = ["."]` in `pytest.ini_options` instead of a `conftest.py` workaround for the same import problem).

  Rather than assume it worked or silently merge it, it was checked out into an isolated git worktree and actually run: `pytest` passed, `ruff check` was clean (`ruff format --check` failed only on missing trailing newlines — cosmetic), a real local Docker Postgres was booted and `alembic upgrade head` applied the migration cleanly, producing all 13 planned tables plus `alembic_version`, and the FastAPI app booted against that live database and served `/health` end to end. One genuine gap: the migration creates empty tables with **no seed data**, because the all-three ratification session hadn't happened. That remains real, unclaimed work; the schema and scaffold around it do not.

  Decision: the duplicate Stage 0 scaffold commit was abandoned rather than merged alongside Michael's, since his version is a strict superset — same stack choices arrived at independently (a good sign the choices were sound), plus the real schema. `origin/database`'s first commit (`42a6f3f`) is treated as the authoritative Stage 0/Stage 1 backend foundation; its second commit (`673eddc`, Neon AI-skill-file scaffolding, assumed unrelated at the time) is *not* assumed to be part of that and is tracked as Open Question 9. — **Resolved 2026-10-09: the Neon files were intentional and Neon is the team's shared hosted Postgres; see that entry.**

  While investigating, a similar situation was found on the frontend: `origin/UXbranch` already had a working skeleton UI styled with plain CSS, built before Tailwind was ever introduced. This didn't change any locked decision at the time, but it meant Stage 0's Tailwind/Vitest item carried a real coordination cost (asking Hailey to restyle existing components), not just an unclaimed-config cost. _(Resolved 2026-10-09 by dropping Tailwind.)_
- **`DifficultyTarget` is a frozen Pydantic model with integer pattern ids.** Fields: `child_id: UUID`, `reinforce_pattern_ids: tuple[int, ...]` (mastered patterns to reuse), `stretch_pattern_ids: tuple[int, ...]` (new patterns, in `sequence_order`). Chosen over a plain dict (no validation, easy to misspell a key) and over a mutable model (Component 3 must not be able to edit the target it was handed). Integer `phonics_pattern_id`s over string `code`s, to match the surrogate-key convention used for every FK. Tuples, not lists, so the value is immutable end to end. New optional fields may be added later; changing or renaming an existing field needs a new entry here first.
- **`select_difficulty_target` takes `session` as its first parameter.** Deviates from the original `(child_id)` signature in the 2026-09-30 entry. Reason: the real body must read the DB, and adding a session parameter later would change the signature Component 3 calls, forcing a coordinated edit. Passing the session explicitly (rather than opening one inside the function) keeps the function testable and avoids a hidden second connection pool. The stub raises `NotImplementedError` rather than returning an empty target, so the generator can't silently run on fake data.
- **Route stubs return 501 and do not invent request/response bodies.** Every planned route is registered (so the OpenAPI schema shows the team's contract and Hailey can build against real paths), but none has a body except `POST /sessions/{session_id}/lines/{line_number}/audio`, whose response is `{status: "complete", result}` as specified on 2026-09-30. Its `result` was typed `dict | None` until Michael defined `ScoreResult`. Reason: bodies for the other routes aren't specified anywhere, and making them up would create a contract nobody agreed to.
- **`POST` audio upload uses `python-multipart`.** Required by FastAPI's `UploadFile`, which the per-line `MediaRecorder` blob upload needs. The only new runtime dependency this adds.
- **Route-stub tests check the OpenAPI schema, not `app.routes`.** FastAPI's `include_router` wraps routers, so `app.routes` doesn't list the paths flat. The OpenAPI schema is what teammates consume, so it's the honest thing to test.
- **Lint and format scope.** Ruff check passes repo-wide. Ruff format check already failed on Michael's `alembic/` files and `app/api/routes/health.py` (missing trailing newlines) before this work. Those were left untouched, because reformatting another owner's files inside a feature PR would blur the review. New files are formatted.
- **Dashboard path kept as `/caregiver/{child_id}/dashboard` (singular), pending PR review.** The other caregiver routes are plural. The singular may be a typo from the 2026-09-30 route list, but it was kept for consistency with what the team had written, with the rename deferred to review. — **Superseded 2026-10-06.**

### 2026-10-06

- **Dashboard path renamed to `/caregivers/{child_id}/dashboard` (plural).** Settles the inconsistency above: every caregiver-rooted route is now plural. `backend/app/api/routes/dashboard.py` and its test updated; verified live (renamed path returns 501, old singular path returns a plain 404). The *naming* question — caregiver-rooted but keyed on a child id — is separate and is now Open Question 11.
- **Open Question 10 resolved: accept the `uv.lock` revision bump, pin a `uv` floor instead of reverting it.** `[tool.uv] required-version = ">=0.12.23"` added to `backend/pyproject.toml`. Chosen over rolling the lockfile back to revision 3, which would just hand the same bump to whoever adds the next dependency. With the pin, `uv sync`/`uv run` on an older `uv` fails with a clear version message instead of a confusing lockfile-parse error, and the fix for whoever hits it is one command: `uv self update`.

### 2026-10-07

- **Open Question 5 resolved: Anthropic Claude, Haiku 4.5 tier, for `generate_story_draft()`.** Shokhina's call, as Component 3 owner. Haiku over Sonnet: the generation loop (draft → validate → regenerate-with-feedback, max N attempts) can call the model several times per story, and Haiku's lower cost and latency per call is favored over Sonnet's likely-higher first-attempt pass rate — on the reasoning that the validator exists specifically to catch exactly the kind of misses a cheaper model makes more often. If the real reject rate against the seeded vocabulary turns out too high in practice, revisit the tier, not the architecture. `anthropic` added as a backend dependency; `ANTHROPIC_API_KEY` and `ANTHROPIC_STORY_MODEL` (default `claude-haiku-4-5-20251001`) added to `backend/.env.example` and `Settings`.
- **3 fallback story templates authored against the *starter set*, not the real (still-unseeded) `vocabulary_word` table.** `backend/app/services/story_templates.py`. Since `vocabulary_word` has zero seeded rows (blocked on the ratification session), these can't be validated against the real controlled vocabulary yet. Decision: draft them now, scoped strictly to the starter-set doc's 18 documented pattern-example words + its 7 sight words, plus a small, explicitly-listed set of 16 basic grammatical words (`DRAFT_GLUE_WORDS`: "a", "after", "and", "ate", "by", "can", "fell", "fun", "go", "had", "has", "i", "in", "is", "like", "sat") needed to form sentences at all, none of which are in the ratified-pending starter set. A test (`tests/test_story_templates.py`) mechanically enforces that every template line uses only this documented word set, so vocabulary drift is caught automatically rather than by manual re-reading. **Action carried to the ratification session (Sprint 2, Gate G1):** either fold `DRAFT_GLUE_WORDS` into the sight-word list (same role — ungraded, never pattern-attributed) or confirm a different "always-allowed" mechanism; either way these 3 templates need a final pass against whatever `vocabulary_word` actually ends up seeded with, since the starter set's "example words" column was documented as illustrative, not as the full word list.

### 2026-10-08 — Sprint 1 close-out decisions

- **Scoring service seam and result contract.** `ScoreResult` contains per-word `expected_word`, optional `recognized_word`, and `status` (`mastered`, `shaky`, or `missed`), matching what `reading_attempt` persists. `process_line_score(session, reading_session_id, story_line_id, score_result)` owns persistence and mastery updates. Both bodies remain to-build (now Sprint 2).
- **`dev` is the team's integration branch, not `main`.** PR #7 merged into `dev` rather than `main` (its merge commit's first parent is `ab440d5`, the stale first-repo-commit tip `dev` had been sitting at since the project started), and Michael then pushed his scoring stubs directly onto `dev`. Hailey's `UXbranch` subsequently merged `dev` into itself, so her branch carries that history forward too. Confirmed as intentional rather than reverted: `dev` is now *the* branch feature work targets. Consequences recorded honestly — `main` is stale and should not be branched from until it is caught up, and the earlier "never use the `dev` branch name" guidance (from the 2026-10-05 branch-protection incident) is obsolete. Still open: whether `main` ever gets fast-forwarded to match, and whether direct pushes to `dev` without a PR are the new norm or were a one-off (now Gate G4).
- **Sprint plan recalibrated: Sprint 1 over-scoped, integration gets its own sprint, Sprint 4 split in half.** Sprint 1 asked for a first pass of all four components *and* a working end-to-end integration inside two weeks, while Sprint 2 separately listed "first real frontend/backend connection" — a contradiction in the original plan that only became visible when Sprint 1 closed with three healthy but entirely unconnected components. Changes: (1) the end-to-end integration milestone and all of Sprint 1's Stage 3 component tests move to **Sprint 2**, re-scoped from "adaptive engine + generation quality" into an explicit **integration sprint**; (2) the displaced adaptive-difficulty and generation-quality work moves to **Sprint 3**, alongside its existing usability-testing focus; (3) **Sprint 4** is split at its mid-sprint review — week 1 is reserved capacity for absorbing slippage plus the go/no-go on the instructor reach goal, and week 2 is a hard feature freeze for polish and final testing only. Rationale for the freeze specifically: Sprint 1's lesson is that a plan with no reserved slack produces a demo with nothing connected, so slack is now scheduled rather than improvised. Unchanged: the proposal's sprint calendar and review dates — only contents moved, not deadlines.
- **Parent and child PINs adopted as real scope; amends the auth/session decision.** Came out of Hailey's route-by-route audit of the API contract against her built UI, which surfaced an entire feature area absent from this plan: a 4-digit parent PIN gating the caregiver dashboard, and a per-child 4-digit PIN so siblings can't read under each other's profiles. Adopted as real scope rather than parked, because the UI for it already exists and the alternative is a dashboard anyone can tap into. This **amends** the 2026-09-30 auth decision rather than overriding it: the lightweight profile-picker model stands, with PINs as an added gate. Security requirements fixed now, not left to implementation: PINs are hashed server-side (consistent with the hashed `caregiver_session.token_hash`), verification happens only through dedicated server-side verify routes, no endpoint ever returns a PIN or its hash, and both verify routes are throttled — a 4-digit PIN is 10,000 combinations, so client-side comparison would be trivially bypassable and an unthrottled server route only slightly less so. PINs are a sibling-mix-up guard and a child-proof gate, explicitly **not** real authentication. Sub-decisions tracked as Open Question 13. _(Scheduled into Sprint 2 originally; **moved to Sprint 3 on 2026-10-09** — timing only, design unchanged.)_
- **Frontend routing: a `useState` screen switch, no `react-router-dom`.** Hailey's call, as Component 4 owner. The app is a small fixed set of screens (login → role → PIN → dashboard or reader) with no URL-sharing or deep-linking requirement, so a router's cost isn't repaid. Recorded here because it constrains how the PIN gates and the child/parent flows get built, and because it is routinely mistaken for resolving Open Question 1 — it does not; the state/data-fetching choice is still open.
- **No separate child login; child identity comes from a picker plus a per-child PIN.** Hailey's call, from the same audit. The child side had no notion of *which* child was reading, but sessions and story generation both require a child id. Rejected a child login screen (grades 1–3, and the caregiver is present at setup) in favor of: the selected child lives in app state, the child side gets its own picker, and a per-child PIN prevents siblings reading under the wrong profile. Depends on the list-children endpoint and the `ChildPicker` id-vs-name fix, both Sprint 2 items.
- **`generate_story_draft()` contract and implementation.** `patterns: Sequence[PhonicsPattern]` (full rows, not bare ids — the prompt needs `code`/`label`/`example_words` to instruct the model, not just a surrogate key), `interests: tuple[str, ...]` (free-text child interest tags), `vocab_constraints: frozenset[str]` (the allowed-word set). Returns `DraftStory` (`backend/app/schemas/stories.py`), deliberately the same shape as `FallbackStoryTemplate` (`title`, `theme`, `pattern_codes`, `lines`) so the not-yet-built validator and regenerate loop can treat an LLM draft and a fallback template identically. The call (`backend/app/services/story_generation.py`) asks the model for strict JSON and parses it directly — no retry-on-malformed-JSON handling, since that folds into the regenerate loop rather than being duplicated here. Tests mock `anthropic.Anthropic` rather than calling the real API, so the suite stays offline, deterministic, and free. This function does **not** validate its own output against `vocab_constraints` — that's the separate validator, still to build.

### 2026-10-09 — Sprint 1 closed; plan restructured and Sprint 2 cut

- **This file restructured; a closed sprint no longer carries live checkboxes.** The problem being fixed: Sprint 1's section held its original Stage 0–3 checklists with mixed `[x]`/`[ ]`/`[→]` markers *and* a close-out table *and* a carryover list, while Sprint 2 separately repeated every unfinished item. So each open item existed in two places, and an unchecked box could mean "to do," "moved," or "abandoned" with no way to tell which. Worse, five Stage 0 items (Tailwind, Vitest, the README rewrite, the frontend `/health` fetch, the 3-person parity check) were unchecked in Sprint 1 and appeared in *no* carryover list — silently lost. Changes: a closed sprint becomes a retrospective with no checkboxes; open work lives in exactly one place; a new §2 Current State records what actually runs today so nobody reconstructs it from checkbox archaeology; the Open Questions register became one table with owners and decide-by dates; a §5 calendar table was added; and the Decisions Log was reordered properly chronologically (several 2026-10-05 entries had drifted below 2026-10-08 ones). No decision content was changed or deleted — only reordered and, where superseded, marked as such.
- **Sprint 2 scope cut: PINs move to Sprint 3, the list-stories endpoint is dropped.** Sprint 2 as drafted on 2026-10-08 carried **30 open line items** for three people in two weeks — more than Sprint 1 had when it over-committed, which would have repeated the exact mistake the 2026-10-08 recalibration was written to fix. The cut is driven by one test: does this item serve "one path works end to end"? PINs do not — they're a well-specified feature area worth roughly a third of one owner's sprint, competing directly with the validator and route wiring the slice depends on, and Hailey's PIN screens keep working on mock behavior in the meantime, so nothing visibly regresses. They move to Sprint 3, where they also arrive *before* the usability sessions, which is when siblings reading under each other's profiles becomes a live problem rather than a hypothetical. The list-stories endpoint is dropped rather than deferred: having "Start" call `POST /stories/generate` directly removes an endpoint from an over-full sprint *and* matches the product premise better — finishing a book is meant to lead into a fresh story, not a library browse. Open Question 13's decide-by moves to Sprint 3 with the feature. Sprint 2 also gained explicit **gates** (G1–G5) at the top, because Sprint 1's single hardest blocker turned out to be an unheld 30-minute meeting, not any piece of code — so the meetings are now scheduled work with a deadline rather than something that happens when someone remembers.
- **Open Question 14 raised: the `WordStatus` mapping.** Promoted from a buried checklist line to a numbered open question. Hailey's UI word states (`neutral`/`correct`/`retry`) and Michael's `WordScore.status` (`mastered`/`shaky`/`missed`) have never been mapped to each other, and the reader cannot render a real score without that mapping. It's a 10-minute decision sitting on the critical path of the sprint's main goal, which is exactly the kind of thing that deserves a number and an owner rather than a bullet.
- **Open Question 9 resolved: Neon is the team's hosted, shared Postgres. Docker Compose stays, with a narrowed job.** Confirmed by Shokhina 2026-10-09: the Neon files landed in `673eddc` on purpose, and Neon is what the team is using as its shared database. That's a good call and it lands at a useful moment — a single shared database means the ratified phonics vocabulary gets seeded **once** rather than three times, which is directly on the critical path of Sprint 2's definition of done, and it makes a joint demo stop depending on whose laptop has a healthy Docker container.

  **This amends, not replaces, the 2026-09-28 Docker Compose decision.** That decision's rationale (identical environment, easy reset, no internet dependency) is still correct — for *tests*. A test suite that mutates a database all three developers are working against is a bad trade at any scale. So the two now have separate jobs: **Neon is the shared integration, seeding, and demo database; Docker Compose is for running the test suite and offline/throwaway work.** Keeping both is cheap because `DATABASE_URL` is the only thing that differs.

  **An honest correction about the files, because it changes what work is left.** The `673eddc` commit's ~5,800 lines are `.agents/skills/neon-*/SKILL.md` files plus `skills-lock.json` — AI-assistant skill documentation vendored from `neondatabase/agent-skills`, which teach a coding agent how to use Neon. They're genuinely useful (the pooled-vs-direct guidance below came straight out of them) but they are documentation, not connectivity. Alongside them, `neon.ts` is an empty `defineConfig({})` stub and the root `package.json` declares two `@neon/*` **npm** packages in a repo whose backend is Python. None of it connects the app to Neon. What actually connects the app is `DATABASE_URL`, and as of today `backend/app/core/config.py` and `backend/.env.example` both still default to `localhost:5432` Docker Postgres, and the migration has only ever been applied against Docker. So "we're using Neon" is a confirmed *decision* with the wiring still unstarted — recorded plainly so nobody assumes the shared database is live when it isn't. The wiring is now a Sprint 2 task in Michael's lane.

  **Two technical requirements fixed now rather than discovered later.** (1) **Alembic must use Neon's direct endpoint, not the pooled one.** Per the pooled-vs-direct table in the repo's own `.agents/skills/neon-postgres/SKILL.md`, schema migrations, `pg_dump`/`pg_restore`, and anything needing `SET` or session state require a direct connection, while web applications should use the pooled (`-pooler`) endpoint. Practically: `alembic/env.py` and the app may need two different URLs. Migrations that half-apply through a transaction pooler are an unpleasant and avoidable way to lose an afternoon. (2) **A Neon connection string is a live credential.** `.env` is correctly git-ignored and untracked today and must stay that way; the string never goes in a PR, issue, or commit message, and `.env.example` carries a placeholder only. If it leaks, rotate it in the Neon console rather than hoping.

  **What's genuinely still open** is the working convention a shared database needs and local Docker never did — who applies migrations, branch-per-developer vs. one shared database, who owns re-seeding. Tracked as Open Question 15 rather than assumed, and folded into the same meeting as the phonics ratification session since it decides where the seed lands. Neon's cheap database branching (see the bundled `neon-postgres-branches` skill) is the obvious candidate answer, but it's Michael's call as DB owner. Noted as a side effect: Open Question 8 (COPPA) is now marginally less hypothetical, since children's reading data leaves the laptop — not a semester-scope change, but the honest answer to "where does a child's data live" has changed.
- **Tailwind CSS dropped; plain CSS is the locked styling choice.** Reverses the 2026-09-28 Tailwind decision. Rationale: Tailwind was chosen as the fastest path to a custom child-facing UI *before any UI existed*. Hailey has since built roughly fifteen components — the full child read-aloud flow, the parent dashboard and its tabs, login, and the PIN keypad — in plain CSS, and they work. Tailwind compiles to plain CSS and was always documented here as a workflow choice with no capability gain, so adopting it now buys nothing and costs a restyle of the entire existing UI, paid during the sprint whose whole purpose is connecting layers. Keeping it "locked but not installed" was worse than either outcome: it sat in the locked-stack table for two sprints implying future work nobody had scheduled, and it made a real Stage 0 checklist item permanently unstartable. Revisit only if the UI is ever rebuilt from scratch.
