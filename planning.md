# StoryWeave — Product & Sprint Roadmap

_The durable, versioned plan for StoryWeave: an adaptive, phoneme-aware story generator for early readers. This is the working decision record and end-to-end roadmap — update it as work progresses, in the same PR as the work it describes. Initialized 2026-09-28, ahead of Sprint 1._

For lightweight, session-to-session working state (velocity, active blockers, "what was I doing"), see `context_sync.md` — that file is git-ignored and never committed; this one is the source of truth.

---

## Scope

StoryWeave listens to a child (grades 1–3) read aloud, uses speech recognition to diagnose exactly which phonemes/words trip her up, and generates a brand-new short story built primarily from phonics patterns she has already mastered plus a small number of "stretch" patterns — repeating every session, so "finishing a book" always leads into a fresh, personalized one. A lightweight caregiver dashboard surfaces what a child is currently working on in plain language, with concrete at-home practice suggestions.

**Baseline scope (Variation 1 — Real-Time Adaptive Reader, per the finalized proposal):** diagnosis and story generation both happen live, within a single session. Two primary users: the child and their caregiver. An instructor/classroom view is an explicit **reach goal**, attempted only if the baseline is done early (Sprint 4).

Four functional components, one primary owner each (per the proposal's team-fit section):

| # | Component | Owner |
|---|---|---|
| 1 | Speech & Phoneme Diagnostic Pipeline | Michael |
| 2 | Adaptive Difficulty Engine | Shokhina |
| 3 | Constrained Story Generation Module | Shokhina |
| 4 | Child Read-Aloud Interface & Parent/Instructor Dashboard | Hailey |

---

## Locked Stack & Infrastructure Decisions

These were walked through and confirmed on 2026-09-28, before Sprint 1 work starts. Full rationale for each lives in the **Decisions Log** at the bottom of this file; this table is the quick-reference summary.

| Layer | Decision | Status |
|---|---|---|
| Database | PostgreSQL | Locked (pre-existing) |
| Backend web framework | FastAPI | **Locked** |
| Backend DB access | SQLAlchemy (sync ORM) + Alembic for migrations. Raw SQL via `op.execute()` remains fully available inside any migration, and raw queries remain available anywhere the ORM isn't a good fit. | **Locked** |
| Postgres driver | `psycopg` (v3, `[binary]` build) | **Locked** (2026-10-05) |
| Python dependency/env manager | `uv` | **Locked** |
| Frontend framework | Vite + React 19 + TypeScript (already scaffolded in `frontend/`) | Locked (pre-existing) |
| Frontend styling | Tailwind CSS | **Locked** |
| Local dev database | Docker Compose (one `docker-compose.yml` at repo root; identical Postgres for all three of you and CI) | **Locked** |
| External APIs | Speechace (speech-to-text + phoneme pronunciation scoring), Open Library (book/vocab metadata), Merriam-Webster (dictionary/thesaurus for controlled-vocabulary checks) | Locked (pre-existing, per proposal) |

**Proposed defaults — not yet explicitly confirmed, low-risk to change later:**

| Layer | Proposed default | Confirm by |
|---|---|---|
| Backend testing | `pytest` | End of Sprint 1 |
| Frontend testing | Vitest + React Testing Library | End of Sprint 1 |
| Backend lint/format | Ruff (lint + format) | Sprint 1, Stage 0 |
| Frontend lint | ESLint (already scaffolded in `frontend/`) | — |

---

## Open Questions Register

Consolidated, numbered, grouped by area. Resolved items move to the Decisions Log (below) with a date rather than being deleted, so the "why" survives. A retired number is never reused and never resequenced — it simply disappears from this list — so a reference to "Open Question N" stays unambiguous across the file's whole history instead of drifting as items resolve.

### A. Stack / infrastructure
1. **Frontend state/data-fetching approach** (plain `fetch` + Context vs. TanStack Query vs. Redux/Zustand). Owner: Hailey (Component 4). *Blocks:* Sprint 1 Stage 2 frontend tasks, not Stage 0/1. Still open.
2. **Deployment/hosting target.** Not needed until closer to Sprint 4. Still open.
9. **What is the `673eddc` "added neon connectivity for db" commit on `origin/database` for?** It adds ~5,800 lines of Neon AI-assistant "skill" documentation files, `neon.ts`, `package.json`, etc. at the repo root — not wired into the Python backend at all (the actual DB connection still points at local Docker Postgres, untouched by this commit). Looks like it may have come from an AI coding tool auto-installing skill files rather than an intentional product decision, but that's Michael's branch and his call to clarify, not something to assume or silently exclude. Owner: Michael. *Blocks:* merging `origin/database` into `main` cleanly — flagged 2026-10-05 after discovering and verifying the rest of that branch's work (backend scaffold + full Stage 1 schema) independently duplicated what Sprint 1 Stage 0/1 had planned. Still open.

### C. Components 2 & 3 — Difficulty engine + story generation
5. **LLM provider for the story generator** (Anthropic Claude vs. OpenAI GPT vs. other). Narrower than it may look next to the Decisions Log entry below: the *architecture* (LLM-primary + template-stitched fallback, validated against controlled vocabulary) is already decided — this item is only "which vendor," a cost/key-management choice isolated behind `generate_story_draft(...)` so it can be settled without reworking the pipeline. Owner: Shokhina (Component 3). *Blocks:* the real (non-stub) story-generator task in Sprint 1 Stage 2 (its gating line item references this question by number). Requires an API key added to `.env.example` once chosen. Still open.

### F. Future / non-blocking, flagged for awareness
8. **COPPA / children's-data considerations.** If StoryWeave is ever used by real families outside the classroom demo, recording a child's voice and storing a phonics profile triggers children's-online-privacy obligations (parental consent flow, data minimization, no behavioral tracking). Not a Sprint 1/2 concern for a semester project's grading — flagged now so it isn't a surprise if scope ever expands past the class.

**Status, in one line:** only #1, #2, #5, #8, and #9 remain open. #3 (audio capture), #4 (Speechace integration pattern), #6 (auth/session model), and #7 (sprint calendar) all resolved 2026-09-30 — see the Decisions Log below for each.

---

## Sprints

### Sprint 1 — Foundations: DB Schema, First-Pass Pipeline, Story Generator, Dashboards (end-to-end)

**Status:** Not started.
**Per the proposal's Table 1/2.** Mid-sprint review target: **Oct 2, 2026** (see Open Question 7 — confirm this is still accurate).
**Primary owners:** All three jointly own the phonics-pattern-list session and the end-to-end connection; Michael owns DB schema + first-pass ASR; Shokhina owns first-pass story generator; Hailey owns first-pass skeleton UI for both dashboards.

**Goal:** Go from an empty scaffold to a thin but *real* vertical slice: a child can read a line, get it scored against Speechace, see it reflected in a caregiver-facing dashboard, and finish a session into a freshly generated story — even if every piece is rough.

#### Stage 0 — Environment Setup
_Blocks everything else. Nobody starts Stage 1 work until this is done and every team member has verified they can run the full stack locally._

- [x] Scaffold backend as a `uv`-managed project: `pyproject.toml` + FastAPI app skeleton under `backend/app` — **superseded 2026-10-05.** Built independently on `shokhina-stage0-env-setup` (branch abandoned), then discovered Michael had already built the same thing plus the full Stage 1 schema on `origin/database` — verified working (see new Decisions Log entry, 2026-10-05: "Discovered and verified Michael's `database` branch"). Treat this item as done via `database`, pending its merge to `main`.
- [x] SQLAlchemy engine/session setup under `backend/app/db`, Alembic initialized and pointed at the Docker Compose Postgres — **done on `origin/database`, verified 2026-10-05** (migration applies cleanly against a live local Postgres; see Decisions Log)
- [x] `docker-compose.yml` at repo root — **done on `origin/database`, verified 2026-10-05** (booted for real, healthy)
- [x] `backend/.env.example` documenting every required env var — **done on `origin/database`**
- [ ] Frontend: install and configure Tailwind CSS on top of the existing Vite + React 19 + TS scaffold; verify one Tailwind utility class actually renders — **still open, but flagged 2026-10-05:** Hailey's `origin/UXbranch` already has a working Stage 2 skeleton UI (child read-aloud screen, parent dashboard) styled with plain CSS, built before Tailwind was ever added. Introducing Tailwind now means asking her to redo that styling — a team conversation, not a solo task, even though no one else has touched Tailwind/Vitest config itself.
- [x] Backend lint/format: Ruff — **locked, no longer a proposed default** — confirmed working on both the (abandoned) `shokhina-stage0-env-setup` scaffold and independently on `origin/database`
- [x] Backend test framework: `pytest`, with one smoke test — **locked** — confirmed working on `origin/database` (`tests/test_health.py`, passing)
- [ ] Frontend test framework: Vitest + React Testing Library, with one smoke test — **locked** — still open, same Hailey-coordination note as the Tailwind item above
- [x] `GET /health` endpoint in FastAPI returning 200 — **done on `origin/database`, verified 2026-10-05** end-to-end against a live Postgres (not just `TestClient`)
- [ ] Minimal frontend fetch/display of `/health` as a wiring smoke test — still open
- [ ] `README.md` rewritten with real setup instructions: install `uv`, `docker compose up`, `alembic upgrade head`, run backend, run frontend — still open
- [ ] **Environment parity check:** all three team members independently run `docker compose up` + backend + frontend locally and confirm `/health` renders in the browser

**Deliverables expected from Stage 0:**
- Runnable local stack (Docker Postgres + FastAPI backend + Vite/React frontend) verified independently by all three members
- `/health` endpoint rendering in the browser
- Committed `docker-compose.yml`, `.env.example`, updated `README.md`, locked lint/test tooling with smoke tests passing

#### Stage 1 — Core Architecture
_Depends on Stage 0. Open Questions 3, 4, and 6 are now resolved (see Decisions Log, 2026-09-30) — this stage implements those decisions rather than re-deciding them._

- [ ] **All three:** joint session to scope the initial phonics-pattern list — the concrete set of patterns (e.g. consonant blends, silent-e, digraphs like TH/CH/SH per the team's own user research) both the diagnostic pipeline and the story generator will target this sprint — **still the real blocker as of 2026-10-05: the schema below is built and verified, but no starter patterns or vocabulary words are seeded into it yet, because this ratification session hasn't happened**
- [x] **Michael:** design and write the initial DB schema migration(s) — **done and verified 2026-10-05** on `origin/database` (migration `9cde937f7a48_initial_storyweave_schema.py`), pending merge to `main`. All tables below exist and match; see Decisions Log for full verification detail:
  - `caregiver` (id, display_name, email _nullable, unused for login yet_, created_at)
  - `caregiver_session` (id/token — generated with `secrets.token_urlsafe(32)` or equivalent, never sequential/guessable, since it's the entire access boundary with no password check yet — caregiver_id FK, created_at, expires_at _not enforced in Sprint 1, see note below_) — this table is the seam real auth will attach to later
  - `child` (id, caregiver_id FK, display_name, interests, created_at)
  - `reading_session`, `phonics_mastery` (per child × pattern)
  - `phonics_pattern` (surrogate integer PK `phonics_pattern_id`, `code` UNIQUE NOT NULL, `label`, `category`, `example_words`, `sequence_order` seeded with gapped values — e.g. multiples of 10 — so a pattern can be inserted between two existing ones later without a renumbering migration) — per `sprint1_phonics_pattern_starter_set.md`
  - `vocabulary_word` (id, `word` normalized lowercase+trimmed, `is_sight_word` boolean default false, created_at) + `vocabulary_word_pattern` (`vocabulary_word_id` FK, `phonics_pattern_id` FK, composite PK) as a many-to-many junction — **added 2026-09-30, supersedes the standalone `sight_word` table originally proposed in the phonics starter-set doc.** This is the single shared word→pattern lookup both Michael's scoring path and Shokhina's Sprint-1 controlled-vocabulary seed list read from (a sight word has zero rows in the junction table by definition, so it's still never modeled as if it were a trainable pattern — see Decisions Log for the full rationale)
  - `story`, `story_line`
  - `reading_attempt` / miscue log (per line, per word — attributed to a pattern via `vocabulary_word_pattern`, not via phoneme position; phoneme-level attribution is explicitly Sprint 2, see `sprint1_phonics_pattern_starter_set.md` §4)
  - `articulation_flag` (per child, per phoneme/pattern — lets a caregiver/teacher mark a known articulation variant, e.g. a lisp, so the scorer treats it as expected rather than a phonics miss)
- [x] **Michael:** apply the schema via Alembic against the local Docker Postgres; commit the migration files — **done and verified 2026-10-05** (re-ran `alembic upgrade head` against a fresh local Postgres independently; applied cleanly, all 13 tables + `alembic_version` created)
- [ ] **Michael:** stub the `score_line_audio(audio_bytes, expected_line) -> ScoreResult` and `process_line_score(...)` service functions (bodies can be minimal/fake for now — the real Speechace call is a Stage 2 task) so the synchronous-call boundary decided above is in place before any endpoint calls into it
- [ ] **Shokhina:** stub `select_difficulty_target(child_id) -> DifficultyTarget` with a placeholder body and the frozen `DifficultyTarget` contract (real naive first-pass body is a Stage 2 task) — moved here from a stray "Stage 1 deliverable" that had no corresponding task
- [ ] **Team:** define the initial REST API contract as FastAPI route stubs (even unimplemented):
  - `POST /caregivers` (create profile)
  - `POST /caregivers/{id}/session` (mint a `caregiver_session` token — no password check yet)
  - `POST /children` (create child under a caregiver)
  - `POST /sessions` (start a reading session for a child)
  - `POST /sessions/{id}/lines/{n}/audio` (per-line audio blob upload → synchronous scoring; response includes a `status` field from day one, e.g. `{"status": "complete", "result": {...}}`, to keep a future `{"status": "pending", "job_id": ...}` variant additive rather than breaking)
  - `GET /stories/{id}`, `POST /stories/generate`
  - `GET /caregiver/{child_id}/dashboard`

**Deliverables expected from Stage 1:**
- Ratified phonics-pattern starter list + sight-word list (from the all-three session) — sight words are now modeled as `vocabulary_word.is_sight_word`, not a separate table (see 2026-09-30 amendment)
- Applied Alembic migration creating the full first-pass schema (caregiver/session/child, sessions, patterns, vocabulary words + word→pattern junction, mastery, stories/lines, attempts, articulation flags)
- REST API contract as route stubs
- Service-function seams stubbed (`score_line_audio`, `process_line_score`, `select_difficulty_target`) so Stage 2 fills bodies, not shapes

#### Stage 2 — Feature Implementation
_Depends on Stage 1. This is the "first pass of everything" stage: each owner builds their component's first working version, then all three wire the diagnosis→generation path end to end. First-pass means working, not polished or adaptive — the adaptive difficulty engine (Component 2) and the decoding-vs-articulation classifier are explicitly deferred to later sprints per the proposal._

**Gating item (do first):**
- [ ] **Resolve Open Question 5 — LLM provider** (Anthropic vs. OpenAI vs. other). Blocks Shokhina's story-generator task below. Add the chosen provider's key to `backend/.env.example`.

**Michael — Component 1, first-pass diagnostic pipeline:**
- [ ] Implement the real `score_line_audio(audio_bytes, expected_line) -> ScoreResult` body: call Speechace with the line's audio + expected text, parse the phoneme-level response into a `ScoreResult` (per-word/per-phoneme: mastered / shaky / missed)
- [ ] Implement `process_line_score(...)`: persist the `ScoreResult` to `reading_attempt` / miscue log, then attribute each scored word to a pattern via `vocabulary_word_pattern` (word → one or more patterns) and update `phonics_mastery` for that child accordingly — **not** phoneme-position attribution, which is deliberately deferred to Sprint 2 (see `sprint1_phonics_pattern_starter_set.md` §4 and the 2026-09-30 Decisions Log entry)
- [ ] Wire `POST /sessions/{id}/lines/{n}/audio` to call both synchronously and return `{"status": "complete", "result": {...}}`
- [ ] Sight-word handling: scoring looks up the read word in `vocabulary_word`; if `is_sight_word = true`, skip it (no pattern credit/penalty, no `vocabulary_word_pattern` rows to attribute)
- [ ] _Explicitly NOT in Sprint 1:_ decoding-vs-articulation classification, articulation-flag honoring (Sprint 2)

**Shokhina — Component 3, first-pass story generator:**
- [ ] Implement `select_difficulty_target(child_id) -> DifficultyTarget` with the naive first-pass body (reuse mastered patterns + pick N stretch patterns by `sequence_order`) — this is the Component 2 seam; real engine replaces the body in Sprint 3
- [ ] Implement `generate_story_draft(patterns, interests, vocab_constraints) -> DraftStory` calling the chosen LLM behind the isolated boundary
- [ ] Implement the controlled-vocabulary validator (rejects a draft containing any word outside the current controlled vocabulary) + the regenerate loop (retry with feedback, max N attempts)
- [ ] Implement the template-fallback path: on N consecutive validator rejections, return a pre-authored, guaranteed-valid story (author ~2–3 fallback templates for Sprint 1)
- [ ] Controlled vocabulary for Sprint 1 = the rows in the shared `vocabulary_word` / `vocabulary_word_pattern` tables (Michael's Stage 1 migration), seeded by the team from the starter phonics-pattern session — **not** a separate hardcoded Python list, so Michael's scoring path and Shokhina's generator read the same word→pattern data and can't drift apart (2026-09-30 amendment). Full Open Library + Merriam-Webster–driven vocabulary expansion is still Sprint 2/3 (proposal: "improving generation quality and interest-matching in Sprint 3")
- [ ] Wire `POST /stories/generate` and `GET /stories/{id}` to the pipeline

**Hailey — Component 4, first-pass skeleton UI (unconnected):**
- [ ] Child read-aloud screen skeleton (Figure 1): story-text area, mic button as the single largest first-tap target, "Next line," listening indicator — laid out with mock/placeholder story data
- [ ] Caregiver dashboard skeleton (Figure 2): phoneme-mastery-progress area, "Currently working on," "Suggested at-home practice" — mock data
- [ ] _Skeleton only — first frontend/backend connection is a Sprint 2 task per the proposal, so OQ1 (frontend data library) does not block this stage_

**All three — end-to-end connection (the Sprint 1 integration milestone):**
- [ ] Wire the backend path end to end: a completed session's stored mastery profile + child interests → `select_difficulty_target()` → `generate_story_draft()` → validated story persisted and retrievable. Demonstrable via API calls even before the frontend is connected
- [ ] Joint smoke-run of the full path against the local stack

**Deliverables expected from Stage 2:**
- A working (first-pass) diagnostic endpoint: real audio in → phoneme-level scores stored, profile updated
- A working (first-pass) generation endpoint: produces a validated, pattern-labeled story, with a fallback that never dead-ends
- Two skeleton frontend screens (child read-aloud, caregiver dashboard) rendering with mock data
- A demonstrable end-to-end backend path (diagnosis → difficulty target → generated story), exercisable via API
- `select_difficulty_target()` seam in place with its naive body and frozen `DifficultyTarget` contract
- LLM provider decided and keyed in `.env.example`

#### Stage 3 — Testing / QA & Sprint Review
_Depends on Stage 2. First-pass tests per the proposal's "How we will evaluate it" sections, plus the two graded checkpoints: the Oct 2 mid-sprint review and the Sprint 1 review/demo._

**Component tests (first-pass):**
- [ ] Component 1: unit test feeding a known audio sample with pre-labeled miscues through `score_line_audio()`, asserting flagged phonemes match the labels within tolerance (one or two samples is enough for Sprint 1; the developmental-articulation sample set is a Sprint 2/3 deliverable)
- [ ] Component 3: automated test asserting the validator rejects a story containing an out-of-vocabulary word before it is returned
- [ ] Component 3: test asserting the template fallback fires after N rejections and returns a valid story
- [ ] Integration: end-to-end path (audio → stored score → difficulty target → generated story) runs without error
- [ ] Stage 0 smoke tests (`/health`, one backend + one frontend test) still green

**Mid-sprint review — Oct 2, 2026 (confirmed live):**
- [ ] Prepare and present mid-sprint review
- [ ] Peer Eval 1
- [ ] Journal Entry 1

**Sprint 1 review & demo:**
- [ ] Demo the end-to-end path together
- [ ] Sprint Report

**Deliverables expected from Stage 3:**
- Passing first-pass test suite covering diagnosis accuracy (sample-level), vocabulary validation, fallback behavior, and end-to-end integration
- Mid-sprint review delivered (Oct 2) with Peer Eval 1 + Journal Entry 1 submitted
- Sprint 1 demo delivered + Sprint Report submitted
- Updated `context_sync.md` reflecting real velocity and any newly surfaced blockers

---

### Sprint 2 — Adaptive Difficulty Engine, Generation Quality, Dashboard v2 _(skeleton — detailed once Sprint 1 closes)_

**Status:** Not started. Mid-sprint review target per proposal: **Oct 16, 2026** (confirm alongside Open Question 7).
**Primary owners:** Michael (continued speech/ASR refinement), Shokhina (adaptive difficulty engine + generation quality/interest-matching).

- Stage 0 — Core Architecture: schema additions for the difficulty engine's mastery-confidence scoring + spaced-repetition selection state
- Stage 1 — Feature Implementation: first-pass adaptive difficulty engine (Shokhina); improved story generation quality + interest-matching (Shokhina); second-pass dashboards (Hailey); first real frontend/backend connection (Hailey); continued ASR pipeline refinement including the decoding-vs-articulation logic (Michael)
- Stage 2 — Testing/QA + mid-sprint review

### Sprint 3 — Usability Testing & Revision _(skeleton)_

**Status:** Not started. Mid-sprint review target per proposal: **Oct 30, 2026**.
**Primary owner:** Shokhina (finalizes the testing plan, including the expanded child-tester panel).

- Moderated usability sessions with children; revisions based on that feedback
- Michael: validates the diagnostic pipeline specifically against the child tester with a lisp; implements resulting revisions
- Hailey: supports usability sessions; implements resulting dashboard revisions

### Sprint 4 — Polish, Full Integration, Final Testing _(skeleton)_

**Status:** Not started. Mid-sprint review target per proposal: **Nov 13, 2026**.
**Primary owner:** Hailey (child + caregiver frontend polish, full integration and testing lead).

- Michael + Shokhina: support final integration and usability testing; last revisions to the diagnostic pipeline and the difficulty engine/generator respectively
- Hailey: builds the instructor reach-goal view **only if the baseline is done early**

### Wrap-Up & Final Presentation _(skeleton)_

Per the proposal's Gantt: GitHub homepage/project website, testing results presentation, video screening, final presentations.

---

## Decisions Log

Chronological. Every locked stack decision above gets an entry here with its rationale; entries from the Open Questions Register move here once resolved, dated.

- **2026-09-28 — Backend web framework: FastAPI.** Chosen over Flask/Django. Rationale: native async fits StoryWeave's I/O-bound integrations with three external APIs (Speechace, Open Library, Merriam-Webster); Pydantic gives free request/response validation, which matters for Component 3's controlled-vocabulary payloads and Component 1's phonics-mastery payloads; auto-generated OpenAPI docs materially help a 3-person team splitting work by component build against a shared, always-accurate contract.
- **2026-09-28 — DB access layer: SQLAlchemy (sync) + Alembic.** Chosen over async SQLAlchemy and over pure raw SQL. Rationale: autogenerated migrations save real time across a schema that's expected to grow every sprint; sync (vs. async) keeps the mental model simpler for a small team without a clear async-Python need, since FastAPI runs sync DB calls in a thread pool transparently and Postgres latency is not this app's bottleneck (Speechace's API latency is). Raw SQL is not lost: `op.execute()` inside any Alembic migration, and raw queries anywhere in the app, remain fully available whenever the ORM isn't the right tool.
- **2026-09-28 — Python dependency/env manager: `uv`.**
- **2026-09-28 — Frontend styling: Tailwind CSS.** Chosen over a component library (MUI/Chakra) or plain CSS. Rationale: fastest path to a custom, playful child-facing UI without fighting a component library's default look; compiles to plain CSS under the hood, so it is a workflow choice, not a capability constraint — anything achievable in plain CSS remains achievable.
- **2026-09-28 — Local dev Postgres: Docker Compose.** Chosen over a hosted free-tier DB or natively-installed Postgres per machine. Rationale: identical environment for all three teammates and CI, easy to reset, no per-machine version drift, no internet dependency during development.
- **2026-09-30 — Audio capture & upload approach: per-line discrete recording.** `MediaRecorder` starts/stops once per line; one blob uploaded per line via `POST /sessions/{id}/lines/{n}/audio`. Chosen over continuous-session-recording-sliced-by-timestamp and true WebSocket streaming. Rationale: matches the team's own user research directly (both test children wanted feedback after a line, not mid-sentence); Component 4's mic-as-largest-first-tap-target design already assumes a per-line tap-to-record rhythm; avoids inventing audio-slicing logic or streaming infrastructure for a real-time-mid-word feedback capability the product explicitly isn't building toward.

- **2026-09-30 — Speechace integration pattern: synchronous, built for a contained future migration.** The scoring call happens in-request (`await`ed inside the FastAPI endpoint), not via a queue. Chosen over a Celery/RQ-style background job because at this project's real scale (a handful of known families) a queue solves a concurrency/retry problem that doesn't exist yet, and adds a broker + worker process to every teammate's local setup during an already-tight Sprint 1. **Explicit design commitment so this stays cheap to change later:** the Speechace call itself lives in one isolated service function (`score_line_audio(audio_bytes, expected_line) -> ScoreResult`), and persisting that result to the phonics-mastery tables lives in a second, separate function (`process_line_score(...)`) that the endpoint calls immediately after. A future move to queued execution only changes *how* those two functions are invoked (direct call vs. `.delay()` from a task) — not their logic. The audio-upload endpoint's response shape also includes a `status` field from day one (`{"status": "complete", "result": {...}}`) so a future `{"status": "pending", "job_id": ...}` variant is an additive contract change, not a breaking one. Revisit if real usage shows Speechace latency spikes badly enough to hurt the UX.

- **2026-09-30 — Auth/session model: lightweight profile-picker now, schema shaped for real auth by end of project.** No passwords or login screen for Sprint 1 — a caregiver creates/selects a profile and gets an opaque session token, no credential check gates it yet. But the schema is built as if real auth were coming (because the team wants it by project end, even though it isn't required by end of Sprint 1):
  - `caregiver` table includes an `email` column (nullable, unused for login right now) so it doesn't need a shape change when login is added.
  - A `caregiver_session` table exists from day one — opaque token, `caregiver_id` FK, `created_at`/`expires_at` — minted on profile creation/selection with no password check. Real auth later just inserts a password check *before* minting this same token; the session concept and its relationship to `caregiver`/`child` doesn't change.
  - `child` rows are FK'd to a real `caregiver_id` from the start (not a bare device-picker with no caregiver entity), so multi-child support and the caregiver dashboard's "which child" scoping are already correct, and adding real auth later is additive rather than a relationship rework.
  Chosen over building real auth in Sprint 1 (unnecessary security surface — password hashing, reset flow, rate-limiting — for a component the grading rubric doesn't touch, at the cost of Sprint 1's actual runway) and over a single hardcoded demo child (wouldn't support the team's own multi-child usability testing).

- **2026-09-30 — Story generation engine: LLM primary with a template-stitched fallback.** The primary path is an LLM call that drafts a short story from the target phonics patterns, the child's stated interests, and the allowed controlled vocabulary; a validator checks the draft against controlled-vocabulary rules and retries with feedback on failure. If the validator rejects N drafts in a row (default 2–3, tunable), the system falls back to a small set of pre-authored, guaranteed-valid template stories rather than dead-ending the session. Chosen over LLM-only (no safety net if a regeneration loop never lands — risky in front of real kids during usability testing) and over pure template/slot-based (would inherently maximize the "repetitive content" complaint that the team's own app-store review scrape flagged as one of the two most common frustrations). Rationale: matches the architecture already diagrammed in proposal Figure 5 (generate → validate → regenerate-if-invalid → approve — a loop that only makes sense with a non-deterministic generator), directly answers the repetitiveness finding, and gives a hard guarantee that a session always ends in a valid, pattern-labeled story — which also satisfies the caregiver-interview finding that generated text must be validated and labeled before a caregiver trusts it.

- **2026-09-30 — Sprint calendar confirmed live.** The proposal's schedule is accurate: Sprint 1 mid-sprint review is Oct 2, 2026. Sprint 1 scope stays as written (schema + first-pass ASR + first-pass story generator + both skeleton dashboards + end-to-end connection). The thinner-slice contingency noted earlier is retired — no longer needed.

- **2026-09-30 — Component 2 seam defined ahead of its build.** `select_difficulty_target(child_id) -> DifficultyTarget` is introduced in Sprint 1 with a naive placeholder body (reuse mastered patterns + pick N stretch patterns by sequence order) so the diagnosis→generation path can be wired end to end before the real adaptive difficulty engine exists. Component 2 (Sprint 3) replaces the function body only; `DifficultyTarget` is the frozen contract between Components 2 and 3 and does not change.

- **2026-09-30 — Sprint 1 mastery attribution is word→pattern, not phoneme→pattern; `vocabulary_word`/`vocabulary_word_pattern` replaces the standalone `sight_word` table.** Caught during architecture review: `sprint1_phonics_pattern_starter_set.md` correctly defers phoneme↔pattern mapping to Sprint 2 (Speechace scores phonemes; mapping a phoneme-in-position to a `phonics_pattern` is real work, and the doc was right not to pull it into Sprint 1). But Stage 2's first-pass diagnostic pipeline still needs to update `phonics_mastery` *this* sprint, and Shokhina's story generator already needs a controlled-vocabulary word list *this* sprint too (Stage 2: "a small hardcoded seed list keyed to the starter phonics patterns"). Rather than building two separate word lists that could drift, or inventing phoneme-level attribution early, both needs are met by one shared table: `vocabulary_word (word, is_sight_word)` + a many-to-many `vocabulary_word_pattern (vocabulary_word_id, phonics_pattern_id)` junction. Michael's scoring path attributes a read word to a pattern by looking it up in this table (word-level, not phoneme-position-level); Shokhina's generator reads the same table as its controlled vocabulary instead of a separate hardcoded list. This supersedes the phonics starter-set doc's original standalone `sight_word` table — a sight word is now just a row with `is_sight_word = true` and zero `vocabulary_word_pattern` rows, which still satisfies the doc's original (correct) concern that a sight word must never be modeled as if it were itself a trainable phonics pattern; it just collapses two lookup tables scoring would otherwise have to check into one. Phoneme-level attribution remains untouched as Sprint 2 scope.
- **2026-09-30 — `phonics_pattern` gets a surrogate PK and gapped `sequence_order` values.** `phonics_pattern_id` (serial) is the primary key with `code` as a separate `UNIQUE NOT NULL` column, matching every other table's surrogate-key convention and avoiding a cascading FK rewrite if a `code` ever needs to change. `sequence_order` is seeded in multiples of 10 (10, 20, 30…) rather than 1..9, because the phonics starter-set doc's own backlog (§3) implies short-vowel CVC patterns will eventually need to be inserted *before* Sprint 1's digraph/blend-first starter set — sequential integers would force a renumbering migration at that point; gapped integers absorb it for free. Nothing reads `sequence_order` until Component 2 (Sprint 3), so this is a zero-cost insurance policy, not a current blocker.
- **2026-09-30 — `caregiver_session` token must be cryptographically random.** Since Sprint 1 ships session tokens with no password check gating them (see the auth/session model decision above), the token itself is the entire access boundary today. It must be generated with something like Python's `secrets.token_urlsafe(32)` — never sequential, never derived from caregiver/child data. `expires_at` is stored on the table per the original schema plan but is **not enforced** by any Sprint 1 task; noted explicitly here so nobody later assumes expiry is real before it's actually checked somewhere.

- **2026-10-05 — Backend is a `uv` *application* (`package = false`), not the `src/`-layout library `uv init` defaults to.** Running `uv init` scaffolds a publishable library (a `src/storyweave_backend/` package, a `[project.scripts]` entry point, a `[build-system]` section). That's the wrong shape for a FastAPI service that already has a fixed `backend/app/...` layout agreed in this file. Set `[tool.uv] package = false` in `pyproject.toml` and deleted the generated `src/` tree so `app/` stays the one and only backend package root — no build backend, no packaging metadata to maintain for something that's never installed as a dependency elsewhere.
- **2026-10-05 — Postgres driver: `psycopg` v3, `[binary]` build.** Chosen over `psycopg2` (legacy, no longer the recommended driver for new SQLAlchemy 2.x projects) and over the non-binary `psycopg` build (requires local libpq headers/a C toolchain per teammate machine — unnecessary friction for a 3-person team that just needs `uv sync` to work identically everywhere). The binary wheel is the standard low-friction choice for local dev and CI; revisit only if a future deployment target specifically prefers building from source.
- **2026-10-05 — `backend/conftest.py` exists solely to make `app` importable by `pytest`.** `backend/tests/` intentionally has no `__init__.py` (per Stage 0's plan), which means pytest's default import mode inserts `tests/` itself onto `sys.path`, not `backend/` — so `from app.main import app` failed with `ModuleNotFoundError: No module named 'app'` until a `conftest.py` was added at the `backend/` root. Pytest always adds a `conftest.py`'s own directory to `sys.path`, so this one-line empty file is what makes `backend/` (and therefore `app/`) importable from any test module, without switching the project to `src/`-layout or adding `__init__.py` files to `tests/`. Pure plumbing — flagged here only so a future contributor doesn't delete it as "an empty file that does nothing."
- **2026-10-05 — `pydantic-settings` added as a dependency ahead of use.** Added to `backend/pyproject.toml` in the first Stage 0 commit (backend scaffold) even though nothing reads it yet, because the very next commit (Docker Compose + `.env.example`) needs a typed settings object to load `DATABASE_URL`, `SPEECHACE_API_KEY`, and `MERRIAM_WEBSTER_API_KEY` from the environment. Bundling the dependency bump with the scaffold commit avoids a second "add one more pyproject.toml line" commit purely for tooling.

- **2026-10-05 — Discovered and verified Michael's `origin/database` branch already supersedes Stage 0's backend scaffold and most of Stage 1.** After building the Stage 0 backend scaffold independently (on a now-abandoned `shokhina-stage0-env-setup` branch) and attempting to push it, a GitHub branch-protection error on an unrelated stale `dev` branch led to fetching and inspecting all remote branches — which surfaced `origin/database`, pushed the same day, containing a complete `docker-compose.yml`, `backend/.env.example`, `pydantic-settings`-based config, sync SQLAlchemy engine/session, a full Alembic migration, and a complete Stage 1 schema (`Caregiver`, `CaregiverSession` using a hashed `token_hash` rather than a raw token, `Child`, `PhonicsPattern`, `VocabularyWord`/`VocabularyWordPattern`, `Story`/`StoryPattern`/`StoryLine`, `ReadingSession`, `PhonicsMastery`, `ReadingAttempt`, `ArticulationFlag`) — independently matching this file's own Stage 1 schema plan and `sprint1_phonics_pattern_starter_set.md`'s word→pattern decision almost exactly, in several places with a cleaner implementation than planned here (e.g. the hashed session token, `pythonpath = ["."]` in `pytest.ini_options` instead of a `conftest.py` workaround for the same import problem).

  Rather than assume it worked or silently merge/rewrite it, it was checked out into an isolated git worktree and actually run: `pytest` passed, `ruff check` was clean (`ruff format --check` only failed on missing trailing newlines — cosmetic, not functional), a real local Docker Postgres was booted and `alembic upgrade head` applied the migration cleanly, producing all 13 planned tables plus `alembic_version`, and the FastAPI app booted against that live database and served `/health` correctly end to end. One genuine gap was found: the migration creates empty tables with **no seed data** — the starter phonics patterns and vocabulary words from `sprint1_phonics_pattern_starter_set.md` are not yet inserted, because the "all-three ratification session" for that list (Stage 1's first checklist item) hasn't happened yet. That remains real, unclaimed work; the schema and scaffold around it do not.

  Decision: the duplicate Stage 0 backend-scaffold commit was abandoned rather than merged alongside Michael's, since his version is a strict superset (same stack choices — `psycopg` v3 binary, `pydantic-settings`, Ruff config — arrived at independently, plus the real schema). `origin/database`'s first commit (`42a6f3f`) is treated as the authoritative Stage 0/Stage 1 backend foundation pending its own PR into `main`; its second commit (`673eddc`, unrelated Neon AI-skill-file scaffolding) is *not* assumed to be part of that and is tracked as Open Question 9 for Michael to clarify before any merge. See also `context_sync.md` for the full session narrative.

  While investigating, a similar situation was found on the frontend side: `origin/UXbranch` (Hailey's) already has a working Stage 2 skeleton UI (child read-aloud screen, parent dashboard) styled with plain CSS — built before Tailwind was ever introduced. This doesn't change any decision already locked in this file, but it means Stage 0's still-open Tailwind/Vitest item now has a real coordination cost (asking Hailey to restyle existing components), not just an unclaimed-config cost, and shouldn't be started solo without talking to her first.
