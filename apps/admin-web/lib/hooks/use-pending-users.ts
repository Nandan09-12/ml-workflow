"use client";

import { useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiGet, ApiError } from "@/lib/api/client";
import { queryKeys } from "@/lib/query/keys";
import { pendingUsers as mockPendingUsers } from "@/lib/mock/data";
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
  isFallback: boolean;
}

// Map mock PendingUserRecord → UserRecord for fallback
const mockFallbackUsers: UserRecord[] = mockPendingUsers.map((u) => ({
  id: u.id,
  fullName: u.fullName,
  email: u.email,
  requestedRole: u.requestedRole,
  approvedRole: null,
  accountStatus: "PENDING_APPROVAL" as const,
  createdAt: u.requestedAt,
  lastLogin: null,
  approvedAt: null,
}));

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
  const fallbackUsedRef = useRef(false);

  const query = useQuery({
    queryKey: queryKeys.pendingUsers,
    queryFn: async () => {
      fallbackUsedRef.current = false;
      try {
        return await apiGet<ApiPendingUsersResponse>("/admin/users/pending");
      } catch (error) {
        if (error instanceof ApiError) {
          if (error.status >= 500) {
            fallbackUsedRef.current = true;
            return null;
          }
          throw error;
        }
        fallbackUsedRef.current = true;
        return null;
      }
    },
    staleTime: 2 * 60 * 1000,
  });

  if (query.data === null) {
    return {
      items: mockFallbackUsers,
      count: mockFallbackUsers.length,
      isLoading: false,
      isError: false,
      error: null,
      isFallback: true,
    };
  }

  const items = (query.data?.items ?? []).map(mapItem);

  return {
    items,
    count: query.data?.count ?? items.length,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    isFallback: fallbackUsedRef.current,
  };
}
