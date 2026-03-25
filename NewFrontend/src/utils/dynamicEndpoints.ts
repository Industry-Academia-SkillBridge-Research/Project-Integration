/**
 * Dynamic API Endpoint Helper
 * Provides functions to get endpoint URLs dynamically
 * Eliminates hardcoded port dependencies
 */

import { getConfig } from '@/services/configService';

/**
 * Build a full endpoint URL dynamically
 */
export async function buildEndpoint(path: string, serviceType: 'auth' | 'agent' | 'skill' | 'interview' | 'recommendation'): Promise<string> {
  const config = await getConfig();
  
  const serviceMap = {
    auth: config.AUTH_API,
    agent: config.AGENT_API,
    skill: config.SKILL_API,
    interview: config.INTERVIEW_API,
    recommendation: config.RECOMMENDATION_API,
  };
  
  const baseUrl = serviceMap[serviceType];
  return `${baseUrl}${path.startsWith('/') ? path : '/' + path}`;
}

/**
 * Fallback endpoint builder using environment variables
 */
export function buildEndpointFallback(path: string, serviceType: 'auth' | 'agent' | 'skill' | 'interview' | 'recommendation'): string {
  const servicePorts = {
    auth: import.meta.env.VITE_AUTH_API || 'http://localhost:8182',
    agent: import.meta.env.VITE_AGENT_API || 'http://localhost:8002',
    skill: import.meta.env.VITE_API_URL || 'http://localhost:8000',
    interview: import.meta.env.VITE_INTERVIEW_API || 'http://localhost:8188',
    recommendation: import.meta.env.VITE_RECOMMENDATION_API || 'http://localhost:8001',
  };
  
  const baseUrl = servicePorts[serviceType];
  return `${baseUrl}${path.startsWith('/') ? path : '/' + path}`;
}

/**
 * Get authentication API base URL
 */
export async function getAuthAPI(): Promise<string> {
  const config = await getConfig();
  return config.AUTH_API;
}

/**
 * Get agent/CV processing API base URL
 */
export async function getAgentAPI(): Promise<string> {
  const config = await getConfig();
  return config.AGENT_API;
}

/**
 * Get skill backend API base URL
 */
export async function getSkillAPI(): Promise<string> {
  const config = await getConfig();
  return config.SKILL_API;
}

/**
 * Get interview training API base URL
 */
export async function getInterviewAPI(): Promise<string> {
  const config = await getConfig();
  return config.INTERVIEW_API;
}

/**
 * Get recommendation engine API base URL
 */
export async function getRecommendationAPI(): Promise<string> {
  const config = await getConfig();
  return config.RECOMMENDATION_API;
}
