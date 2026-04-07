// Thisaravi-backend API configuration
export const API_BASE = import.meta.env.VITE_THISARAVI_API_URL || 'http://localhost:8185';
// Companion service base paths
export const SCRAPER_BASE = import.meta.env.VITE_SCRAPER_BASE_URL || 'http://localhost:8000';
export const AGENT_BASE = import.meta.env.VITE_AGENT_BASE_URL || 'http://localhost:8003';
export const ROLE_SKILLS_BASE = import.meta.env.VITE_ROLE_SKILLS_BASE_URL || 'http://localhost:8181';

export const ENDPOINTS = {
  ANALYSIS: {
    GENERATE: `${API_BASE}/generate-project`,
  },
  FEEDBACK: {
    MY_OUTPUTS: `${API_BASE}/my-outputs`,
  },
  // Companion services (scraper endpoints now served by gaps-analyzer via Neo4j)
  SCRAPER: {
    SEARCH: `${API_BASE}/search-jobs`,
  },
  AGENT: {
    CANDIDATES: `${AGENT_BASE}/candidates`,
  },
  ROLE_SKILLS: {
    ROLES: `${API_BASE}/roles`,
    JOBS_BY_ROLE: (roleKey: string) => `${API_BASE}/jobs-by-role?role_key=${encodeURIComponent(roleKey)}`,
  },
} as const;

export const MODEL_PROVIDERS = [
  { value: 'ollama', label: 'Ollama (Finetuned)' },
  { value: 'gemini', label: 'Gemini (Cloud)' },
  { value: 'ollama_generic', label: 'Ollama (Generic)' },
] as const;
