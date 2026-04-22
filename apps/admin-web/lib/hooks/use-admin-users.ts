"use client";

import { useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiGet, ApiError } from "@/lib/api/client";
import { queryKeys } from "@/lib/query/keys";
import { users as mockUsers } from "@/lib/mock/data";
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
  isFallback: boolean;
}

const mockPagination: HookPagination = {
  page: 1,
  pageSize: 20,
  total: mockUsers.length,
  totalPages: 1,
};

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
  const fallbackUsedRef = useRef(false);
  const qs = buildQueryString(params);

  const filterRecord: Record<string, string> = {};
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined) filterRecord[k] = String(v);
  });

  const query = useQuery({
    queryKey: queryKeys.users(
      Object.keys(filterRecord).length > 0 ? filterRecord : undefined,
    ),
    queryFn: async () => {
      fallbackUsedRef.current = false;
      try {
        return await apiGet<ApiUsersListResponse>(`/admin/users${qs}`);
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
      items: mockUsers,
      pagination: mockPagination,
      isLoading: false,
      isError: false,
      error: null,
      isFallback: true,
    };
  }

  const items = (query.data?.items ?? []).map(mapItem);
  const raw = query.data?.pagination;
  const pagination: HookPagination = raw
    ? { page: raw.page, pageSize: raw.page_size, total: raw.total, totalPages: raw.total_pages }
    : mockPagination;

  return {
    items,
    pagination,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    isFallback: fallbackUsedRef.current,
  };
}
