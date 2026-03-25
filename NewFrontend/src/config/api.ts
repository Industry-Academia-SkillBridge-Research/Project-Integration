/**
 * API Configuration
 * Now uses dynamic configuration from config server
 * Automatically fetches service URLs at runtime
 */

import { getConfig, ServicesConfig } from '@/services/configService';

// Fallback config for immediate use
export const API_CONFIG_FALLBACK = {
  // Advanced Recommendation System (Port 8001)
  RECOMMENDATION_API: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001',
  
  // Agent Runtime - Gap Analysis (Port 8002)  
  AGENT_RUNTIME_API: import.meta.env.VITE_JOB_GAP_API_URL || 'http://localhost:8002',
  
  // AI Explainer - Now running locally on Agent Runtime (Port 8002)
  EXPLAINER_API: import.meta.env.VITE_EXPLAINER_API_URL || 'http://localhost:8002',
  
  // Nipuni Backend - Transcript-based Skill Validation (Port 8000)
  NIPUNI_API: import.meta.env.VITE_NIPUNI_API_URL || 'http://localhost:8000',
} as const;

/**
 * Get dynamic API configuration
 * Fetches from config server, falls back to environment variables
 */
export async function getAPIConfig() {
  try {
    const config = await getConfig();
    return {
      RECOMMENDATION_API: config.RECOMMENDATION_API,
      AGENT_RUNTIME_API: config.AGENT_API,
      EXPLAINER_API: config.AGENT_API,
      NIPUNI_API: config.SKILL_API,
    };
  } catch (error) {
    console.warn('Using fallback API config:', error);
    return API_CONFIG_FALLBACK;
  }
}

/**
 * Build endpoints dynamically based on config
 */
export async function buildEndpoints() {
  const config = await getAPIConfig();
  
  return {
    // Agent Runtime Endpoints
    AGENT: {
      RUN: `${config.AGENT_RUNTIME_API}/agent/run`,
      RUN_FROM_PDF: `${config.AGENT_RUNTIME_API}/agent/run-from-pdf`,
      HEALTH: `${config.AGENT_RUNTIME_API}/health`,
      SKILL_EXPLAIN: `${config.AGENT_RUNTIME_API}/runtime/skill-explain`,
      PREDICT_EXPLAIN: `${config.AGENT_RUNTIME_API}/runtime/predict-explain`,
    },
    
    // Job Gap Analysis Endpoints
    JOB_GAP: {
      ANALYZE: `${config.AGENT_RUNTIME_API}/job-gap/analyze`,
      HEALTH: `${config.AGENT_RUNTIME_API}/job-gap/health`,
    },
    
    // Advanced Recommendation System Endpoints
    RECOMMENDATION: {
      BASE: config.RECOMMENDATION_API,
      
      // Role endpoints
      ROLES: `${config.RECOMMENDATION_API}/roles`,
      ROLE_SKILLS: (roleKey: string) => 
        `${config.RECOMMENDATION_API}/roles/${roleKey}/skills`,
      
      // Candidate endpoints
      CANDIDATE_ROLES: (candidateId: string) => 
        `${config.RECOMMENDATION_API}/candidates/${candidateId}/roles`,
      CANDIDATE_SKILLS: (candidateId: string) => 
        `${config.RECOMMENDATION_API}/candidates/${candidateId}/skills`,
      
      // Gap Analysis endpoints
      SKILL_CONFIDENCE: (candidateId: string, roleKey: string) =>
        `${config.RECOMMENDATION_API}/candidates/${candidateId}/roles/${roleKey}/skill-confidence`,
      SKILL_GAP: (candidateId: string, roleKey: string) =>
        `${config.RECOMMENDATION_API}/candidates/${candidateId}/roles/${roleKey}/skill-gap`,
      PROJECT_RELEVANCE: (candidateId: string, roleKey: string) =>
        `${config.RECOMMENDATION_API}/candidates/${candidateId}/roles/${roleKey}/project-relevance`,
      
      // Admin
      CACHE_CLEAR: `${config.RECOMMENDATION_API}/cache/clear`,
    },
    
    // Colab Explainer Endpoints
    EXPLAINER: {
      EXPLAIN: `${config.EXPLAINER_API}/explainer/explain`,
      HEALTH: `${config.EXPLAINER_API}/explainer/health`,
      INFO: `${config.EXPLAINER_API}/explainer/info`,
    },
  };
}

/**
 * Static endpoints built from fallback config
 * Used for immediate/synchronous access
 */
export const API_CONFIG = API_CONFIG_FALLBACK;

export const ENDPOINTS = {
  // Agent Runtime Endpoints (Port 8002)
  AGENT: {
    RUN: `${API_CONFIG.AGENT_RUNTIME_API}/agent/run`,
    RUN_FROM_PDF: `${API_CONFIG.AGENT_RUNTIME_API}/agent/run-from-pdf`,
    HEALTH: `${API_CONFIG.AGENT_RUNTIME_API}/health`,
    SKILL_EXPLAIN: `${API_CONFIG.AGENT_RUNTIME_API}/runtime/skill-explain`,
    PREDICT_EXPLAIN: `${API_CONFIG.AGENT_RUNTIME_API}/runtime/predict-explain`,
  },
  
  // Job Gap Analysis Endpoints (Port 8002)
  JOB_GAP: {
    ANALYZE: `${API_CONFIG.AGENT_RUNTIME_API}/job-gap/analyze`,
    HEALTH: `${API_CONFIG.AGENT_RUNTIME_API}/job-gap/health`,
  },
  
  // Advanced Recommendation System Endpoints (Port 8001)
  RECOMMENDATION: {
    BASE: API_CONFIG.RECOMMENDATION_API,
    
    // Role endpoints
    ROLES: `${API_CONFIG.RECOMMENDATION_API}/roles`,
    ROLE_SKILLS: (roleKey: string) => 
      `${API_CONFIG.RECOMMENDATION_API}/roles/${roleKey}/skills`,
    
    // Candidate endpoints
    CANDIDATE_ROLES: (candidateId: string) => 
      `${API_CONFIG.RECOMMENDATION_API}/candidates/${candidateId}/roles`,
    CANDIDATE_SKILLS: (candidateId: string) => 
      `${API_CONFIG.RECOMMENDATION_API}/candidates/${candidateId}/skills`,
    
    // Gap Analysis endpoints
    SKILL_CONFIDENCE: (candidateId: string, roleKey: string) =>
      `${API_CONFIG.RECOMMENDATION_API}/candidates/${candidateId}/roles/${roleKey}/skill-confidence`,
    SKILL_GAP: (candidateId: string, roleKey: string) =>
      `${API_CONFIG.RECOMMENDATION_API}/candidates/${candidateId}/roles/${roleKey}/skill-gap`,
    PROJECT_RELEVANCE: (candidateId: string, roleKey: string) =>
      `${API_CONFIG.RECOMMENDATION_API}/candidates/${candidateId}/roles/${roleKey}/project-relevance`,
    
    // Admin
    CACHE_CLEAR: `${API_CONFIG.RECOMMENDATION_API}/cache/clear`,
  },
  
  // Colab Explainer Endpoints
  EXPLAINER: {
    EXPLAIN: `${API_CONFIG.EXPLAINER_API}/explainer/explain`,
    HEALTH: `${API_CONFIG.EXPLAINER_API}/explainer/health`,
    INFO: `${API_CONFIG.EXPLAINER_API}/explainer/info`,
  },
} as const;

/**
 * Predefined roles
 */
export const ROLES = [
  { key: 'ai_ml_engineer', label: 'AI/ML Engineer' },
  { key: 'data_analyst', label: 'Data Analyst' },
  { key: 'data_engineer', label: 'Data Engineer' },
  { key: 'data_scientist', label: 'Data Scientist' },
  { key: 'devops_engineer', label: 'DevOps Engineer' },
  { key: 'software_engineer', label: 'Software Engineer' },
  { key: 'web_developer', label: 'Web Developer' },
] as const;

/**
 * HTTP request headers
 */
export const REQUEST_HEADERS = {
  JSON: {
    'Content-Type': 'application/json',
  },
  NGROK_SKIP: {
    'Content-Type': 'application/json',
    'ngrok-skip-browser-warning': 'true', // Skip ngrok browser warning page
  },
  MULTIPART: {
    // Don't set Content-Type for FormData - browser sets it with boundary
  },
} as const;

/**
 * Default request options
 */
export const DEFAULT_OPTIONS = {
  TOP_K: 25,
  TOP_N: 5,
  INCLUDE_XAI: true,
  MAX_NEW_TOKENS: 250,
  TEMPERATURE: 0.5,
} as const;
