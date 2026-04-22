"use client";

import { useQuery } from "@tanstack/react-query";
import { apiGet, ApiError } from "@/lib/api/client";
import { queryKeys } from "@/lib/query/keys";
import type { UserRecord, ApiUserItem, HookPagination } from "@/lib/types/domain";

export interface AdminUsersParams {
  requested_role?: string;
  account_status?: string;
  page?: number;
  page_size?: number;
}

interface ApiUsersListResponse {
  items: ApiUserItem[];
  pagination: { page: number; page_size: number; total: number; total_pages: number };
}

export interface AdminUsersResult {
  items: UserRecord[];
  pagination: HookPagination;
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

function buildQueryString(params: AdminUsersParams): string {
  const p = new URLSearchParams();
  if (params.requested_role) p.append("requested_role", params.requested_role);
  if (params.account_status) p.append("account_status", params.account_status);
  if (params.page) p.append("page", String(params.page));
  if (params.page_size) p.append("page_size", String(params.page_size));
  const qs = p.toString();
  return qs ? `?${qs}` : "";
}

export function useAdminUsers(params: AdminUsersParams): AdminUsersResult {
  const qs = buildQueryString(params);

  const filterRecord: Record<string, string> = {};
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined) filterRecord[k] = String(v);
  });

  const query = useQuery({
    queryKey: queryKeys.users(
      Object.keys(filterRecord).length > 0 ? filterRecord : undefined,
    ),
    queryFn: async () => await apiGet<ApiUsersListResponse>(`/admin/users${qs}`),
    retry: (failureCount, error) => {
      if (error instanceof ApiError && error.status >= 400 && error.status < 500) {
        return false;
      }
      return failureCount < 1;
    },
    staleTime: 2 * 60 * 1000,
  });

  const items = (query.data?.items ?? []).map(mapItem);
  const raw = query.data?.pagination;
  const pagination: HookPagination = raw
    ? { page: raw.page, pageSize: raw.page_size, total: raw.total, totalPages: raw.total_pages }
    : { page: 1, pageSize: params.page_size ?? 20, total: 0, totalPages: 0 };

  return {
    items,
    pagination,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
  };
}
