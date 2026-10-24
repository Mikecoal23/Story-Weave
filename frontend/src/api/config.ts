// Base URL of the backend; set VITE_API_URL in frontend/.env to change it
export const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

// Placeholder until login exists: the fixture caregiver from backend/scripts/dev_fixtures.py,
// which has the same id on every machine (run `uv run python -m scripts.dev_fixtures` once)
export const CAREGIVER_ID = 'f1000000-0000-4000-8000-000000000001'

// true = use mock data. Flip a resource to false once its backend route works.
export const USE_MOCKS = {
  children: false,
  stories: false,
  sessions: false,
  dashboard: true,
}
