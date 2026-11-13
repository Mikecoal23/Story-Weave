# StoryWeave Testing Plan

_Hailey Hudson, Shokhina Jalilova, Michael Viera._

StoryWeave is an adaptive reading app for children in grades 1 to 3. A child reads a short story aloud one line at a time; each word is scored (Azure Speech) and turns mint (read right) or coral (shaky or missed). The child's per-pattern mastery picks the phonics patterns of the next story, and an LLM writes that story using only words from our controlled vocabulary. A caregiver sees progress on a dashboard.

## 1. Functional testing

### 1.1 Unit testing

Clear-box tests of single functions with every outside service replaced, written with **pytest**. Azure Speech and the Anthropic SDK are always replaced with unittest.mock / pytest monkeypatch, so no test spends money or needs a network.

What is covered:

- **Scoring (Component 1, Michael):** turning Azure's per-word result into mastered / shaky / missed; word normalisation (punctuation and case ignored, apostrophes kept); audio conversion errors.
- **Difficulty engine (Component 2, Shokhina):** confidence(), is_mastered() and pick_patterns() are pure functions, so they are tested with plain numbers and no database. **Boundary values** are chosen on purpose. Other cases: a new child, sparse data, ties, a mastered pattern that slips back, and every pattern mastered.
- **Story generation (Component 3, Shokhina):** the vocabulary validator accepts seeded words and rejects unseeded ones (title included); the retry loop feeds rejected words back and stops after 3 attempts; an empty or oversized draft is rejected; the best-matching fallback template is chosen when the LLM fails.
- **Contracts:** the frozen DifficultyTarget cannot be changed after it is made and rejects wrong types.
- **Seed data:** no word is in two conflicting lists, ending forms are generated correctly, and the list of words with no pattern is tracked.

### 1.2 Integration testing

Tests that cross a boundary, still with pytest:

- **Backend routes:** FastAPI's TestClient calls the real routes (POST /caregivers, POST /caregivers/session, POST /children, POST /sessions, the audio upload, POST /stories/generate, GET /stories/{id}, GET /children/{id}/dashboard). Bad or missing input returns the right error (404 unknown child, 409 email taken, 422 bad body).
- **Backend to database:** tests run on a **local Docker Postgres** inside a throwaway schema that is rolled back after each test (tests/support.py), so nothing is left behind. They refuse to run against any non-local host, and they skip with a message naming what was not tested if Postgres is not running, so a skip is never mistaken for a pass. Examples: a scored line saves reading_attempt rows and updates phonics_mastery; the engine reads fixed mastery rows and picks the expected patterns; the dashboard reads them back.
- **Backend to speech and LLM services:** routine runs use mocked responses (no cost). Real calls are made by hand with short probe scripts kept outside the repo, for example the before-and-after measurements of the LLM pass rate below.

### 1.3 Functional testing (manual, black box)

A checklist run in the browser against the full local stack (Docker database, backend, frontend), treating the app as a black box:

| # | Check | Pass when |
|---|---|---|
| F1 | Create an account and log in by email | A new caregiver lands on the entry screen; a taken email shows a message; logging back in works |
| F2 | Add a child (grade 1 to 3) | The child appears in "Who is reading?"; grade 0 or 4 is refused |
| F3 | Start a story | A story appears within the time in N1 below, its words all from the vocabulary |
| F4 | Read a line aloud | Each word turns mint or coral |
| F5 | Skip or misread a word on purpose | That word turns coral |
| F6 | Finish the story | "Great reading! You read N lines" appears, with New story and Done |
| F7 | Log out, log back in, open the dashboard | The reading is still counted: sessions this week, last story, pattern bars, words to try at home |
| F8 | Deny the microphone | "Please allow the microphone to read aloud." appears and nothing breaks |
| F9 | Read the same patterns well several times | The next story moves on to new patterns (the engine adapts) |

## 2. Nonfunctional testing

### 2.1 Usability (moderated sessions with children) — the main user test

**Goal:** most test readers in the target age range can finish a story without help, and caregivers can read the dashboard.

**Panel** (placeholder names):

| Placeholder | Who | Grade / role | Notes |
|---|---|---|---|
| Child A | child tester | grade 1 | — |
| Child B | child tester | grade 1 | has a lisp: tells us whether articulation is being scored as a reading mistake |
| Child C (if available) | child tester | kinder | — |
| Caregiver A, Caregiver B | caregivers | parent / guardian | at least 2; each comes with a child |
| Adult A, Adult B | adult testers | no child | read as a child would, and try the caregiver tasks |

**Setup:** one laptop running everything locally (Docker database, backend, frontend), so a child's reading results stay on that laptop and never reach the shared database. Child profiles are created beforehand with placeholder names. Mic check before the child sits down.

**Consent and data:**

- The caregiver is present the whole time and agrees first; the child is asked if they want to play and can stop at any moment.
- The child's voice is sent to Azure to be scored and is **not kept**: the audio lives in a temporary folder only while it is scored. What is stored is each word's result and the child's placeholder name, grade and interests.
- Session data is kept on the laptop for now, for analysis; when to delete it is still to be decided.

**Roles:** Shokhina leads the sessions. A note-taker and someone watching the laptop are filled in per session.

**Session script (about 20 minutes per child):**

1. Welcome (2 min): who we are, "we're testing the app, not you".
2. Warm-up (2 min): read one practice line together.
3. Task 1 (6 min): press Start and read a whole story alone. The moderator only helps if asked twice or the child is stuck for 30 seconds.
4. Task 2 (5 min): press New story and read a second story (shows whether the next story adapts).
5. Child questions (2 min): Was it easy or hard? What did the colours mean? Would you read another one?
6. Caregiver task (3 min, caregiver alone): open the dashboard and say what the child is working on and which words to practise.

**What the note-taker records, per child:**

- Finished the story? Number of times they asked for help, and where.
- Signs of frustration or boredom.
- For each word, the note-taker's own judgement (right / wrong) next to the colour the app showed. This is the human check for 2.3.
- Whether the story came from the LLM or a fallback, and how long it took to appear.
- Caregiver: could they answer both dashboard questions without help?

**Pass mark:** at least 2 of 3 children finish a story without help, and at least 2 caregivers answer both dashboard questions. Findings and the changes they lead to go in the Decisions Log in planning.md.

### 2.2 Performance

- **Feedback within about 5 seconds** of finishing a line: timed with a stopwatch and the browser's network panel during the functional run and the sessions.
- **Story ready in reasonable time:** a live LLM call takes about 2 s; each call times out after 15 s, there are at most 3 attempts, and then a pre-written story is used, so a child is never left waiting with nothing.

### 2.3 Accuracy

- **Word scoring:** the app's mint/coral match the note-taker's human check on most words, including slow or hesitant reading. Reported as the share of words where the two agree, per child. Child B (the lisp) shows whether a clearly-read word is flagged because of articulation.
- **Story generation:** the share of stories that pass the vocabulary check from the LLM rather than a fallback, measured before and after each change (5+ runs each).

### 2.4 Security and privacy

- .env files are git-ignored and only .env.example files are committed.
- Children's audio is not stored (2.1). Placeholder names in every session.
- Database tests refuse to run on anything but a local database.
- PINs (planned): a wrong PIN is rejected, repeated guesses are throttled on the parent side, and no endpoint returns a PIN or its hash.

### 2.5 User acceptance

The caregivers and adult testers in 2.1 act as our acceptance testers: after the session, would they let their child use it, and what is missing? Their answers feed Sprint 4's polish work.

## 3. Tools and methods

| Tool | Used for |
|---|---|
| pytest | All backend unit and integration tests (uv run pytest in backend/) |
| pytest.mark.parametrize | Boundary-value tables (for example the mastery cases) |
| unittest.mock, monkeypatch | Replacing Azure Speech and the Anthropic SDK |
| FastAPI TestClient | Calling real routes in integration tests |
| Docker Compose Postgres | The local test database; throwaway schemas per test |
| Neon temporary branches | Testing a migration or re-seed before the shared database |
| Swagger UI (/docs) | Manual checks of single routes |
| ruff | Lint and format checks on the backend |
| TypeScript (tsc -b) and ESLint | Frontend type and lint checks (npm run build, npm run lint) |
| Browser developer tools, stopwatch | Timing for performance checks |
| Probe scripts (kept outside the repo) | Live before/after measurements of the LLM |
| Note-taking sheet | Usability sessions and the human accuracy check |

**Methods:** clear-box unit tests; black-box functional checks; boundary-value testing; mocking of paid outside services; regression testing (the whole suite runs before every pull request, and every bug found gets a test); before-and-after measurement for any change to story generation; moderated user testing with a think-aloud style ("tell me what you're thinking").

## 4. Why this coverage is enough

- **Every component has automated tests at its own level, and the seams between them are tested too.** Scoring, the difficulty engine, generation and the dashboard each have unit tests, and the routes that join them are tested against a real database. The two contracts between components (DifficultyTarget, the scoring result) have their own tests, so one person's change can't silently break another's.
- **The risky logic is tested at its edges.** The engine's thresholds, the validator's accept/reject line and the retry limit are where bugs hide, so those are where the boundary tests are.
- **People check what automated tests cannot.** Whether a 7-year-old can use it, whether the colours make sense, and whether Azure agrees with a human on a child's voice can only be learned from the sessions in 2.1, which is why they are the centre of the nonfunctional plan.
