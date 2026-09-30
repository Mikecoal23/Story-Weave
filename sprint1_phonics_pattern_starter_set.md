# Sprint 1 — Phonics-Pattern Starter Set & Schema Implications

> **Purpose:** hand-off doc for the schema task (Michael, Component 1). This is the ratified-*pending-team-review* starter list the DB schema should be built around, plus the schema decisions the pattern model depends on.
>
> **Status:** DRAFT for the all-three phonics-pattern session. Everything in the starter set is backed by something already in our user research or dashboard mockups, so it's defensible — but the list isn't final until the team ratifies it together.
>
> **Amended 2026-09-30 (architecture review):** Sections 2 and 4 were revised to close a real gap — as originally written, this doc deferred *all* word→pattern attribution to Sprint 2's phoneme mapping, but Sprint 1's diagnostic pipeline needs to update `phonics_mastery` this sprint. The fix: a shared `vocabulary_word` / `vocabulary_word_pattern` table, at the *word* grain (not phoneme-position), which also replaces the standalone `sight_word` table below and doubles as Shokhina's Sprint 1 controlled-vocabulary source. See `planning.md`'s 2026-09-30 Decisions Log entries for the full rationale. The original Section 2 content is kept below, struck through, so the "why" of the original design isn't lost — only superseded.

---

## 1. Sprint 1 starter set (~9 patterns)

Small on purpose: just enough to build the diagnosis → generation loop around, with every pattern traceable to a research finding or a mockup. We grow into the full sequence (Section 3) over later sprints.

| Code | Label | Category | Example words | Why it's in the starter set | Suggested `sequence_order` |
|---|---|---|---|---|---|
| `digraph_sh` | SH | consonant digraph | ship, wish | Child named it; teacher's "shop"→"chop" example | 10 |
| `digraph_ch` | CH | consonant digraph | chip, much | Child named it; the "chop" confusion target | 20 |
| `digraph_th` | TH | consonant digraph | this, bath | Child named it as hard | 30 |
| `blend_bl` | BL | initial L-blend | blue, black | Named in dashboard mockup | 40 |
| `blend_cl` | CL | initial L-blend | clap, clock | Named in dashboard mockup | 50 |
| `blend_fr` | FR | initial R-blend | frog, from | Named in dashboard mockup | 60 |
| `silent_e_a` | a_e (silent-e) | VCe long vowel | cake, name | "Currently working on: silent e" in mockup | 70 |
| `vowel_team_ai_ay` | ai / ay | long-a vowel team | rain, play | "long a (ai, ay)" in mockup + suggested practice words | 80 |
| `final_blend_mp` | -MP | final blend | jump, lamp | Teacher's "jump"→"jum" example (final-sound integrity) | 90 |

**On `sequence_order` (amended 2026-09-30):** values are gapped by 10, not sequential 1–9. Section 3's full backlog implies short-vowel CVC patterns will eventually need a `sequence_order` *before* all nine of these (CVC is typically the most foundational phonics skill, and the backlog lists it as position 1) — but this team's own user research flagged digraphs (TH/CH/SH) as the actual struggle points for both tested children, which is why they're the Sprint 1 starter set instead of CVC. That's a deliberate, defensible choice, but it means CVC needs to be insertable *before* `digraph_sh`'s current position-10 slot later without renumbering every row that follows — hence the gaps. Confirm with the team that skipping CVC for Sprint 1 is intentional (it reads like it is, given the research, but worth a one-line "yes" from the group before Michael seeds these values).

---

## 2. Sight / irregular words

These can't be sounded out and, per the teacher, **must not count against any phonics pattern**. They are an *exclusion input* to scoring, not something a child can be "mastering."

Sprint 1 starter list (grows over time):

```
said, they, of, the, was, to, you
```

**Amended 2026-09-30 — modeled as a flag on the shared vocabulary table, not a separate table.** See Section 4, Implication #2 (revised) below for the current shape. The reasoning that a sight word must never be treated as a trainable `phonics_pattern` row still holds and is still enforced — it's just enforced by "zero associated pattern rows" instead of "lives in a different table."

~~Put sight/irregular words in a dedicated `sight_word` table (or a clearly-flagged separate list) — **not** as `phonics_pattern` rows.~~ *(superseded — see below)*

---

## 3. Full target sequence (backlog — informs `sequence_order`)

Roughly ordered easy → hard. This is the backlog we grow into, and it doubles as the canonical ordering Component 2 (adaptive difficulty engine, Sprint 3) will use for stretch-pattern selection. We don't build all of these in Sprint 1 — but the ordering should be reflected in `sequence_order` values as patterns get added.

1. Short vowels (CVC) — _not yet in the schema; reserve room before `digraph_sh`'s `sequence_order = 10`, e.g. seed at 1–9 or renumber when added, since gapped values don't help if the gap is on the wrong side_
2. Remaining digraphs (wh, ck, ng)
3. Full L / R / S initial blends
4. Remaining silent-e (i_e, o_e, u_e)
5. Remaining vowel teams (ee, ea, oa, ow, oo, igh)
6. r-controlled vowels (ar, or, er, ir, ur)
7. Diphthongs (oi, oy, ou, ow)
8. Final blends (nd, nt, st, nk)

---

## 4. Schema implications (decide these in the same session — the schema depends on them)

### #1 — `phonics_pattern` row shape

Each pattern row should carry at least:

- `phonics_pattern_id` — **surrogate integer primary key** (amended 2026-09-30 — not `code`). Every other table in the schema (caregiver, child, etc.) FKs by surrogate id; keeping this consistent means `code` can be edited later without a cascading FK rewrite.
- `code` — stable string identifier (e.g. `digraph_sh`), used in code/joins — `UNIQUE NOT NULL`, not the PK
- `label` — human-readable display label (e.g. "SH")
- `category` — grouping (e.g. `consonant digraph`, `initial L-blend`, `VCe long vowel`)
- `example_words` — a few representative words (a Postgres `text[]` column is fine here — these are illustrative only, not queried against, unlike the vocabulary table below)
- `sequence_order` — integer, gapped (see Section 1's note)

### #2 — Word→pattern attribution is a shared table, not per-component word lists (amended 2026-09-30)

~~Sight words live in their own table, not as pattern rows.~~ **Superseded.** The real requirement turned out to be broader: Sprint 1's diagnostic pipeline needs to attribute a *read word* to a *phonics pattern* to update `phonics_mastery` (see Implication #3 below for why this can't wait for phoneme-level mapping), and Shokhina's story generator needs a controlled vocabulary of allowed words *also keyed to patterns*, this same sprint. Rather than building two separate word lists that could quietly drift apart, both needs are met by one shared pair of tables:

- **`vocabulary_word`** — `id`, `word` (**normalized: lowercase, trimmed** — this has to match Speechace's transcribed text reliably, and casing drift like "The" vs. "the" would silently break matching), `is_sight_word boolean not null default false`, `created_at`.
- **`vocabulary_word_pattern`** — `vocabulary_word_id` FK, `phonics_pattern_id` FK, composite PK. Many-to-many on purpose: a word like "splash" legitimately exercises more than one pattern (a blend and — depending on the final pattern list — a digraph), so a single FK column on `vocabulary_word` would be wrong.

A sight word is simply a `vocabulary_word` row with `is_sight_word = true` and **zero** rows in `vocabulary_word_pattern` — which still fully satisfies this section's original, correct instinct: a sight word is never modeled as if it were itself a trainable phonics pattern. It just collapses what would otherwise be two separate lookups (an `is-this-a-sight-word` check and an `is-this-a-pattern-word` check) into one table Michael's scoring path queries once per word.

Shokhina's Sprint 1 controlled vocabulary (planning.md Stage 2: "a small hardcoded seed list keyed to the starter phonics patterns") should populate these tables directly, rather than living as a separate Python list — same data, two consumers, one source.

### #3 — Phoneme ↔ pattern mapping is deliberately OUT of scope for Sprint 1 — and here's what Sprint 1 does instead

Speechace scores *phonemes*. A "pattern" maps to one or more phonemes in position (e.g. `digraph_sh` → /ʃ/). Building that mapping is the **Sprint 2** error-flagging work — Sprint 1 only needs the pattern *rows to exist*.

**What changed 2026-09-30:** the original draft of this doc stopped there, but that leaves a real gap — Sprint 1's Stage 2 diagnostic pipeline is scoped to update `phonics_mastery` *this sprint*, and without some form of word↔pattern link, there's nothing to attribute a score to. The resolution is Implication #2 above: Sprint 1 attributes at the **word** grain via `vocabulary_word_pattern` (did the child correctly read a word known to belong to pattern X?), not at the **phoneme-position** grain (did the child correctly produce the specific phoneme in the specific slot that pattern X's phoneme mapping says to check?). This is strictly coarser than the real Sprint 2 system will be, but it's genuine, non-fabricated mastery data — not a placeholder — and it doesn't foreclose Sprint 2's work at all.

**The one thing to still get right now, unchanged from the original draft:** don't model a pattern as if it *is* a single phoneme (e.g. don't put a `phoneme` column directly on `phonics_pattern` as if it's 1:1). When Sprint 2 builds the real phoneme-level mapping, it will most likely be its own table — something like `phonics_pattern_phoneme (phonics_pattern_id, phoneme, position)` — sitting alongside `vocabulary_word_pattern`, not replacing it: word-level attribution (fast, available now) and phoneme-level attribution (precise, Sprint 2) can coexist, since a phoneme-level miscue can still roll up to "this word, which belongs to this pattern."

---

## 5. Quick checklist for the schema task

- [ ] Ratify the starter set (Section 1) as a team
- [ ] Confirm skipping CVC for Sprint 1 is intentional (Section 1 note)
- [ ] Ratify the sight-word list (Section 2) as a team
- [ ] `phonics_pattern` table: surrogate PK `phonics_pattern_id`, `code` as a separate `UNIQUE NOT NULL` column, `sequence_order` seeded per Section 1's gapped values (Implication #1)
- [ ] `vocabulary_word` + `vocabulary_word_pattern` tables created; sight words modeled as `is_sight_word = true` with zero pattern rows, **not** a separate table (Implication #2)
- [ ] Coordinate with Shokhina so her Sprint 1 controlled-vocabulary seed data goes directly into `vocabulary_word` / `vocabulary_word_pattern` rather than a separate hardcoded list
- [ ] Pattern↔phoneme relationship left open for Sprint 2, not collapsed to 1:1, and not confused with the word-level `vocabulary_word_pattern` table that Sprint 1 actually uses (Implication #3)
- [ ] Seed the starter patterns with `sequence_order` values consistent with Section 3's ordering
