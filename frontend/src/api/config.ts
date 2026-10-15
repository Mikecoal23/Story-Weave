// Base URL of the backend; set VITE_API_URL in frontend/.env to change it
export const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

// true = use mock data. Flip a resource to false once its backend route works.
export const USE_MOCKS = {
  children: true,
  stories: true,
  sessions: true,
  dashboard: true,
}
