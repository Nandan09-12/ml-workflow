"use client";

/**
 * useAuth - React hook for authentication
 */

import { useQuery } from "@tanstack/react-query";
import { apiGet, ApiError } from "@/lib/api/client";
import { AppUser, AuthContext } from "@/lib/types/auth";
import { isAdminUser } from "@/lib/utils/auth";

export interface UseAuthReturn extends AuthContext {
  isAdmin: () => boolean;
}

/**
 * Hook to fetch and manage current user authentication state
 * Uses React Query for caching and lifecycle management
 */
export function useAuth(): UseAuthReturn {
  const { data: user, isLoading, error } = useQuery({
    queryKey: ["auth", "me"],
    queryFn: async () => {
      try {
        return await apiGet<AppUser>("/me");
      } catch (requestError) {
        if (requestError instanceof ApiError && requestError.status === 401) {
          return null;
        }

        throw requestError;
      }
    },
    // Retry strategy: don't retry on 4xx auth errors, retry once on others
    retry: (failureCount, error) => {
      if (error instanceof ApiError && error.status >= 400 && error.status < 500) {
        return false;
      }
      return failureCount < 1;
    },
    // Cache for 5 minutes
    staleTime: 5 * 60 * 1000,
  });

  return {
    user: user || null,
    loading: isLoading,
    error: error instanceof Error ? error.message : null,
    isAdmin: () => (user ? isAdminUser(user) : false),
  };
}
