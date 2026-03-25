/**
 * useConfig Hook
 * Provides easy access to service configuration in React components
 */

import { useEffect, useState } from 'react';
import { getConfig, ServicesConfig } from '@/services/configService';

export function useConfig() {
  const [config, setConfig] = useState<ServicesConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const loadConfig = async () => {
      try {
        const loadedConfig = await getConfig();
        setConfig(loadedConfig);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Failed to load config'));
        // Config service provides fallback, so config will still work
        const fallbackConfig = await getConfig();
        setConfig(fallbackConfig);
      } finally {
        setLoading(false);
      }
    };

    loadConfig();
  }, []);

  return { config, loading, error };
}
