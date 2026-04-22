"use client";

import { useQuery } from "@tanstack/react-query";
import { apiGet, ApiError } from "@/lib/api/client";
import { queryKeys } from "@/lib/query/keys";
import type { NoSubmissionYetRecord, ApiNoSubmissionYetItem, HookPagination } from "@/lib/types/domain";

export interface NoSubmissionYetParams {
  work_date: string;
  page?: number;
  page_size?: number;
}

interface ApiNoSubmissionYetResponse {
  work_date: string;
  note: string;
  items: ApiNoSubmissionYetItem[];
  count: number;
  pagination: { page: number; page_size: number; total: number; total_pages: number };
}

export interface NoSubmissionYetResult {
  items: NoSubmissionYetRecord[];
  pagination: HookPagination;
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
}

function mapItem(item: ApiNoSubmissionYetItem): NoSubmissionYetRecord {
  return {
    id: item.id,
    fullName: item.full_name,
    email: item.email,
    approvedRole: "DRIVE_TESTER",
    lastSubmissionDate: null,
    lastWorkorderCode: null,
  };
}

function buildQueryString(params: NoSubmissionYetParams): string {
  const p = new URLSearchParams();
  p.append("work_date", params.work_date);
  if (params.page) p.append("page", String(params.page));
  if (params.page_size) p.append("page_size", String(params.page_size));
  return `?${p.toString()}`;
}

export function useNoSubmissionYet(params: NoSubmissionYetParams): NoSubmissionYetResult {
  const qs = buildQueryString(params);

  const query = useQuery({
    queryKey: queryKeys.noSubmissionYet(params.work_date),
    queryFn: async () =>
      await apiGet<ApiNoSubmissionYetResponse>(`/admin/dashboard/no-submission-yet${qs}`),
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
