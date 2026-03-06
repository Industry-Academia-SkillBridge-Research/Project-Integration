import { useEffect, useState } from 'react';
import { fetchRoles } from '@/services/industryConnectService';
import type { RoleInfo } from '@/types/industryConnect';

interface UseRolesResult {
  roles: RoleInfo[];
  isLoading: boolean;
  error: string | null;
}

export function useRoles(): UseRolesResult {
  const [roles, setRoles] = useState<RoleInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setError(null);

    fetchRoles()
      .then((data) => {
        if (!cancelled) {
          setRoles(data);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to fetch roles');
        }
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return { roles, isLoading, error };
}
