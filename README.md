# StoryWeave

StoryWeave helps children in grades 1–3 practise reading aloud. A child reads a story one line at a time, the app listens and scores each word, and the next story is written for that child: it practises the phonics patterns they have mastered plus a couple of new ones, using only words they are ready to read.

Team: Michael (speech scoring), Shokhina (difficulty engine and story generation), Hailey (child and parent interface).

## How it works

One reading session, step by step, and where each step lives in the code:

1. **Pick a reader.** A caregiver's children are listed from the database.
   `GET /caregivers/{id}/children` in `backend/app/api/routes/caregivers.py`
2. **Choose what to practise.** The difficulty engine looks at the child's mastery so far and picks the patterns for the next story: the ones they've mastered, plus the next two to learn.
   `backend/app/services/difficulty.py`
3. **Write the story.** Claude (Haiku 4.5) writes a short story using those patterns. Every word is checked against our approved vocabulary of 316 words. If a word isn't allowed, the model gets up to 3 tries, told each time which words were rejected. If all three fail, the child gets a pre-written story instead, so they never see an error.
   `POST /stories/generate` → `backend/app/services/story_pipeline.py`, `story_generation.py`, `vocabulary_validator.py`, `story_templates.py`
4. **Read a line aloud.** The browser records the line and uploads it. Azure Speech scores each word as `mastered`, `shaky` or `missed`.
   `POST /sessions/{id}/lines/{n}/audio` → `backend/app/services/scoring.py`
5. **Update what the child knows.** Each scored word updates the child's mastery of its phonics pattern, which feeds step 2 for the next story.
   `process_line_score` in `backend/app/services/scoring.py`

## What works today

- **Working:** the whole loop above, in the browser, against a real database, Azure Speech and Claude. After a child reads a line, each word turns mint (read well) or coral (try again).
- **Still sample data:** the parent dashboard. Login (`admin` / `123`) and the PINs (`1234`) are placeholders until Sprint 3.
- **Known limitation:** Claude almost always uses words outside our vocabulary, so for now nearly every child gets one of the pre-written stories. Fixing that is the first generation task in Sprint 3.

## What's in the repo

| Path | What it is |
|---|---|
| `backend/app/api/routes/` | The HTTP routes |
| `backend/app/services/` | The logic: scoring, difficulty, story generation |
| `backend/app/models/entities.py` | Database tables |
| `backend/alembic/` | Database migrations |
| `backend/scripts/` | Scripts to load the vocabulary and demo data |
| `backend/tests/` | Backend tests |
| `frontend/src/` | React app: `child-ui/` (reading), `parent-dashboard/`, `api/` (calls to the backend) |
| `planning.md` | Our plan, open questions and every decision with its reason |

## Setup (first time)

You need Python 3.12+, [`uv`](https://docs.astral.sh/uv/), Node.js 22.12+, Docker Desktop and FFmpeg (`brew install ffmpeg` on a Mac).

### 1. Start the database

From the repo root:

```sh
docker compose up -d db
```

This runs Postgres in Docker on `localhost:5432`. The default username and password are for local development only. Copying `.env.example` to `.env` lets you change them, but you don't need to.

### 2. Set up the backend

```sh
cd backend
cp .env.example .env
uv sync
uv run alembic upgrade head
```

- `cp .env.example .env` creates your private settings file. It is git-ignored, so keys never get committed.
- `uv sync` installs the Python packages.
- `alembic upgrade head` creates the 13 tables.

Then add your keys to `backend/.env`:

| Setting | Needed for | Without it |
|---|---|---|
| `ANTHROPIC_API_KEY` | Claude writing stories | You always get a pre-written story |
| `AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION` | Scoring a read line | The audio route returns 502 |

### 3. Load the vocabulary and demo data

Still in `backend/`:

```sh
uv run python -m scripts.seed_vocabulary
uv run python -m scripts.dev_fixtures
```

- `seed_vocabulary` loads the 9 phonics patterns and 316 approved words. It's safe to run again.
- `dev_fixtures` adds one caregiver, two children (Mia and Leo) and one story, always with the same ids, so the frontend and the demo commands below work on every machine.
- Both scripts refuse to touch a database that isn't on your machine unless you add `--allow-remote`, and `--dry-run` shows what would change without saving it.

The fixed ids:

| | id |
|---|---|
| Caregiver | `f1000000-0000-4000-8000-000000000001` |
| Mia | `f1000000-0000-4000-8000-0000000000a1` |
| Leo | `f1000000-0000-4000-8000-0000000000a2` |
| Story ("Ship Wish", Mia's) | `f1000000-0000-4000-8000-0000000000b1` |

### 4. Run it

Backend, in `backend/`:

```sh
uv run uvicorn app.main:app --reload
```

Open `http://localhost:8000/docs` to see and try every route.

Frontend, in a second terminal, in `frontend/`:

```sh
npm install
npm run dev
```

Open `http://localhost:5173` and log in with `admin` / `123`. Choose **Child → Mia**, enter PIN `1234` and press Start. The story takes a few seconds while Claude is asked. Click the mic, read the line, then click again to stop; the words change colour once the line is scored. Which parts use real data and which use sample data is set by `USE_MOCKS` in `frontend/src/api/config.ts`.



## Checks

From `backend/`:

```sh
uv run pytest
uv run ruff check .
```

The database tests need the Docker database running. Without it they are skipped, and each skip says what wasn't tested. No test calls the real Azure or Claude APIs.

From `frontend/`:

```sh
npm run lint
npm run build
```

## Shared database (Neon)

The team also shares a hosted Postgres on Neon, which has the same vocabulary and demo data. Its connection strings live only in ignored `.env` files. The app uses the pooled URL (`DATABASE_URL`) and migrations use the direct one (`DATABASE_URL_UNPOOLED`); `backend/.env.example` shows the format. Tests never run against Neon. Check with the team before running scripts or migrations against it.

## Data handling

Recordings are processed one line at a time and are never stored; the database keeps only the word results and mastery scores. There is no real authentication, consent flow or data-retention policy yet, so don't use StoryWeave with real children's data until those are designed and reviewed.
