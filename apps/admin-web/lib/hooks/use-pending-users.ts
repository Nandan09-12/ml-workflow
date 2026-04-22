"use client";

import { useQuery } from "@tanstack/react-query";
import { apiGet, ApiError } from "@/lib/api/client";
import { queryKeys } from "@/lib/query/keys";
import type { UserRecord, ApiUserItem } from "@/lib/types/domain";

interface ApiPendingUsersResponse {
  items: ApiUserItem[];
  count: number;
}

export interface PendingUsersResult {
  items: UserRecord[];
  count: number;
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
}

function mapItem(item: ApiUserItem): UserRecord {
  return {
    id: item.id,
    fullName: item.full_name,
    email: item.email,
    requestedRole: item.requested_role,
    approvedRole: item.approved_role,
    accountStatus: item.account_status,
    createdAt: item.created_at,
    lastLogin: null,
    approvedAt: item.approved_at,
  };
}

export function usePendingUsers(): PendingUsersResult {
  const query = useQuery({
    queryKey: queryKeys.pendingUsers,
    queryFn: async () => await apiGet<ApiPendingUsersResponse>("/admin/users/pending"),
    retry: (failureCount, error) => {
      if (error instanceof ApiError && error.status >= 400 && error.status < 500) {
        return false;
      }
      return failureCount < 1;
    },
    staleTime: 2 * 60 * 1000,
  });

  const items = (query.data?.items ?? []).map(mapItem);

  return {
    items,
    count: query.data?.count ?? items.length,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
  };
}
