export const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';
// Companion service base paths (proxied by Vite dev server)
export const SCRAPER_BASE = import.meta.env.VITE_SCRAPER_BASE_URL || '/scraper';
export const AGENT_BASE = import.meta.env.VITE_AGENT_BASE_URL || '/agent-runtime';
export const ROLE_SKILLS_BASE = import.meta.env.VITE_ROLE_SKILLS_BASE_URL || '/role-skills';

export const ENDPOINTS = {
  ANALYSIS: {
    GENERATE: `${API_BASE}/generate-project`,
    GENERATE_FROM_SOURCES: `${API_BASE}/generate-project-from-sources`,
  },
  FEEDBACK: {
    SUBMIT: `${API_BASE}/submit-feedback`,
    UNREVIEWED: `${API_BASE}/unreviewed-outputs`,
    STATUS: `${API_BASE}/feedback-status`,
    ALL: `${API_BASE}/all-feedback`,
  },
  EVOLUTION: {
    RUN_ANALYSIS: `${API_BASE}/run-analysis`,
    PATTERN_REPORTS: `${API_BASE}/pattern-reports`,
    PREVIEW: `${API_BASE}/preview-evolution`,
    APPLY: `${API_BASE}/apply-evolution`,
    EVOLUTIONS: `${API_BASE}/prompt-evolutions`,
    CURRENT_PROMPT: `${API_BASE}/current-prompt`,
    REGENERATE: `${API_BASE}/run-regeneration`,
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
