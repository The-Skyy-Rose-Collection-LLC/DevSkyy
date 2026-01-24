'use client';

import { useState, useEffect, useCallback, useRef } from 'react';

interface UseQueryOptions<T> {
  /** Callback on successful fetch */
  onSuccess?: (data: T) => void;
  /** Callback on error */
  onError?: (error: Error) => void;
  /** Whether to enable the query (default: true) */
  enabled?: boolean;
  /** Refetch interval in ms (default: none) */
  refetchInterval?: number;
  /** Initial data */
  initialData?: T;
  /** Stale time in ms before refetch (default: 0) */
  staleTime?: number;
}

interface UseQueryResult<T> {
  data: T | null;
  error: Error | null;
  loading: boolean;
  refetch: () => Promise<void>;
  isStale: boolean;
}

/**
 * Generic data fetching hook with caching and refetch support.
 *
 * @example
 * const { data: users, loading, error, refetch } = useQuery(
 *   'users',
 *   () => api.users.getList(),
 *   { refetchInterval: 30000 }
 * );
 */
export function useQuery<T>(
  key: string,
  fetcher: () => Promise<T>,
  options?: UseQueryOptions<T>
): UseQueryResult<T> {
  const [data, setData] = useState<T | null>(options?.initialData ?? null);
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(!options?.initialData);
  const [lastFetched, setLastFetched] = useState<number>(0);

  const fetcherRef = useRef(fetcher);
  const optionsRef = useRef(options);

  // Update refs on each render
  fetcherRef.current = fetcher;
  optionsRef.current = options;

  const isStale =
    options?.staleTime !== undefined
      ? Date.now() - lastFetched > options.staleTime
      : true;

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await fetcherRef.current();
      setData(result);
      setLastFetched(Date.now());
      optionsRef.current?.onSuccess?.(result);
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error);
      optionsRef.current?.onError?.(error);
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial fetch
  useEffect(() => {
    if (options?.enabled !== false) {
      refetch();
    }
  }, [key, refetch, options?.enabled]);

  // Refetch interval
  useEffect(() => {
    if (!options?.refetchInterval || options?.enabled === false) {
      return;
    }

    const intervalId = setInterval(() => {
      refetch();
    }, options.refetchInterval);

    return () => clearInterval(intervalId);
  }, [options?.refetchInterval, options?.enabled, refetch]);

  return { data, error, loading, refetch, isStale };
}

export default useQuery;
