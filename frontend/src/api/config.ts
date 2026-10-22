// Base URL of the backend; set VITE_API_URL in frontend/.env to change it
export const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

// Placeholder until login exists: replace with the id of a real row in the caregivers table
export const CAREGIVER_ID = '343fe841-7cc3-4fd2-b8be-15edcb543398'

// true = use mock data. Flip a resource to false once its backend route works.
export const USE_MOCKS = {
  children: false,
  stories: true,
  sessions: false,
  dashboard: true,
}
