# StoryWeave

StoryWeave is a read-aloud practice app for early readers. The repository uses a React + TypeScript client, a FastAPI backend, and PostgreSQL.

## Prerequisites

- Python 3.12 or later
- `uv` for Python dependencies and commands
- Node.js 22.12 or later
- Docker Desktop with Docker Compose
- FFmpeg (required to convert browser-recorded audio for Azure Speech)

## Start the database

From the repository root, copy `.env.example` to `.env`, then start PostgreSQL:

```sh
docker compose up -d db
```

The database is available locally at `localhost:5432`. The committed credentials are for local development only.

For the shared Neon database, set `DATABASE_URL` to the pooled `-pooler` endpoint
for application traffic and `DATABASE_URL_UNPOOLED` to the direct endpoint for
Alembic migrations. The Neon URL examples in `backend/.env.example` are placeholders;
keep real connection strings and Azure Speech credentials only in the ignored
`backend/.env` file.

## Set up the backend

```sh
cp backend/.env.example backend/.env
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

The API health endpoint is `http://localhost:8000/health`; interactive API docs are at `http://localhost:8000/docs`.
Line scoring uses Azure Speech Pronunciation Assessment; configure `AZURE_SPEECH_KEY`
and `AZURE_SPEECH_REGION` in `backend/.env`.

## Run checks

From `backend/`:

```sh
uv run pytest
uv run ruff check .
```

From `frontend/`:

```sh
npm install
npm run lint
npm run build
```

## Data handling

Raw audio is processed per line and is not stored in PostgreSQL. The initial schema stores derived reading attempts and mastery data. This scaffold does not implement authentication, consent flows, retention policies, or COPPA/FERPA compliance; do not use it with real children's data until those protections are designed and reviewed.
