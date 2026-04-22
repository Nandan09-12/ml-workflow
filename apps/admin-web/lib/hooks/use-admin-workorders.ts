"use client";

import { useQuery } from "@tanstack/react-query";
import { apiGet, ApiError } from "@/lib/api/client";
import { queryKeys } from "@/lib/query/keys";
import type { WorkorderRecord, ApiWorkorderItem, HookPagination } from "@/lib/types/domain";

export interface AdminWorkordersParams {
  workorder_code?: string;
  region?: string;
  status?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  page_size?: number;
}

interface ApiWorkordersListResponse {
  items: ApiWorkorderItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface AdminWorkordersResult {
  items: WorkorderRecord[];
  pagination: HookPagination;
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
}

function mapItem(item: ApiWorkorderItem): WorkorderRecord {
  return {
    id: item.id,
    workorderCode: item.workorder_code,
    region: item.region,
    status: item.status,
    totalGrids: item.total_grids,
    completedGrids: item.completed_grids,
    skippedGrids: item.skipped_grids,
    remainingGrids: item.remaining_grids,
    progressPercent: item.progress_percent,
    createdAt: item.created_at,
    updatedAt: item.updated_at,
  };
}

function buildQueryString(params: AdminWorkordersParams): string {
  const p = new URLSearchParams();
  if (params.workorder_code) p.append("workorder_code", params.workorder_code);
  if (params.region) p.append("region", params.region);
  if (params.status) p.append("status", params.status);
  if (params.date_from) p.append("date_from", params.date_from);
  if (params.date_to) p.append("date_to", params.date_to);
  if (params.page) p.append("page", String(params.page));
  if (params.page_size) p.append("page_size", String(params.page_size));
  const qs = p.toString();
  return qs ? `?${qs}` : "";
}

export function useAdminWorkorders(params: AdminWorkordersParams): AdminWorkordersResult {
  const qs = buildQueryString(params);

  const filterRecord: Record<string, string> = {};
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined) filterRecord[k] = String(v);
  });

  const query = useQuery({
    queryKey: queryKeys.workorders(
      Object.keys(filterRecord).length > 0 ? filterRecord : undefined,
    ),
    queryFn: async () => await apiGet<ApiWorkordersListResponse>(`/admin/workorders${qs}`),
    retry: (failureCount, error) => {
      if (error instanceof ApiError && error.status >= 400 && error.status < 500) {
        return false;
      }
      return failureCount < 1;
    },
    staleTime: 2 * 60 * 1000,
  });

  const items = (query.data?.items ?? []).map(mapItem);
  const raw = query.data;
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
