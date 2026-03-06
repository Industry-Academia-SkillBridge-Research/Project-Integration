import { useEffect, useState } from 'react';
import { fetchJobsByRole } from '@/services/industryConnectService';
import type { LinkedInJobResult } from '@/types/industryConnect';

interface UseJobsByRoleResult {
  jobs: LinkedInJobResult[];
  isLoading: boolean;
  error: string | null;
}

export function useJobsByRole(roleKey: string | null): UseJobsByRoleResult {
  const [jobs, setJobs] = useState<LinkedInJobResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!roleKey) {
      setJobs([]);
      setIsLoading(false);
      setError(null);
      return;
    }

    let cancelled = false;
    setIsLoading(true);
    setError(null);
    setJobs([]);

    fetchJobsByRole(roleKey)
      .then((data) => {
        if (!cancelled) setJobs(data);
      })
      .catch((err) => {
        if (!cancelled)
          setError(err instanceof Error ? err.message : 'Failed to fetch jobs');
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [roleKey]);

  return { jobs, isLoading, error };
}
