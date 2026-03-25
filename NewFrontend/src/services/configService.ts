/**
 * Configuration Service
 * Fetches service URLs from the config server
 * Provides fallback to environment variables
 * Caches config to avoid repeated requests
 */

export interface ServicesConfig {
  AUTH_API: string;
  AGENT_API: string;
  SKILL_API: string;
  INTERVIEW_API: string;
  RECOMMENDATION_API: string;
}

// Fallback config from environment or hardcoded defaults
const FALLBACK_CONFIG: ServicesConfig = {
  AUTH_API: import.meta.env.VITE_AUTH_API || 'http://localhost:8182',
  AGENT_API: import.meta.env.VITE_AGENT_API || 'http://localhost:8002',
  SKILL_API: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  INTERVIEW_API: import.meta.env.VITE_INTERVIEW_API || 'http://localhost:8188',
  RECOMMENDATION_API: import.meta.env.VITE_RECOMMENDATION_API || 'http://localhost:8001',
};

// Config cache
let configCache: ServicesConfig | null = null;
let configPromise: Promise<ServicesConfig> | null = null;

/**
 * Fetch configuration from config server
 * Uses cache if available
 */
export async function getConfig(): Promise<ServicesConfig> {
  // Return cached config if available
  if (configCache) {
    return configCache;
  }

  // Return existing promise if fetch is in progress
  if (configPromise) {
    return configPromise;
  }

  // Fetch config from server
  configPromise = fetchConfigFromServer();

  try {
    configCache = await configPromise;
    return configCache;
  } catch (error) {
    console.warn('Failed to fetch config from server, using fallback:', error);
    configCache = FALLBACK_CONFIG;
    return FALLBACK_CONFIG;
  } finally {
    configPromise = null;
  }
}

/**
 * Fetch configuration from the config server
 */
async function fetchConfigFromServer(): Promise<ServicesConfig> {
  const configServerUrl = import.meta.env.VITE_CONFIG_SERVER_URL || 'http://localhost:8099';
  
  try {
    const response = await fetch(`${configServerUrl}/config`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Config server returned ${response.status}`);
    }

    const config = await response.json();
    console.log('Loaded config from server:', config);
    return config as ServicesConfig;
  } catch (error) {
    console.error('Error fetching config from server:', error);
    throw error;
  }
}

/**
 * Get specific service URL
 */
export async function getServiceUrl(serviceName: keyof ServicesConfig): Promise<string> {
  const config = await getConfig();
  return config[serviceName];
}

/**
 * Get all service URLs
 */
export async function getAllServices(): Promise<ServicesConfig> {
  return getConfig();
}

/**
 * Reset cache (useful for testing or when ports change)
 */
export function resetConfigCache(): void {
  configCache = null;
  configPromise = null;
}

/**
 * Initialize config on app startup
 * Pre-loads config to avoid delays in first requests
 */
export async function initializeConfig(): Promise<void> {
  try {
    await getConfig();
    console.log('Config service initialized');
  } catch (error) {
    console.warn('Config initialization failed, will use fallback:', error);
  }
}
