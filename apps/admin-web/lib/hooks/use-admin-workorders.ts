"use client";

import { useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiGet, ApiError } from "@/lib/api/client";
import { queryKeys } from "@/lib/query/keys";
import { workorders as mockWorkorders } from "@/lib/mock/data";
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
  isFallback: boolean;
}

const mockPagination: HookPagination = {
  page: 1,
  pageSize: 20,
  total: mockWorkorders.length,
  totalPages: 1,
};

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
  const fallbackUsedRef = useRef(false);
  const qs = buildQueryString(params);

  const filterRecord: Record<string, string> = {};
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined) filterRecord[k] = String(v);
  });

  const query = useQuery({
    queryKey: queryKeys.workorders(
      Object.keys(filterRecord).length > 0 ? filterRecord : undefined,
    ),
    queryFn: async () => {
      fallbackUsedRef.current = false;
      try {
        return await apiGet<ApiWorkordersListResponse>(`/admin/workorders${qs}`);
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
      items: mockWorkorders,
      pagination: mockPagination,
      isLoading: false,
      isError: false,
      error: null,
      isFallback: true,
    };
  }

  const items = (query.data?.items ?? []).map(mapItem);
  const raw = query.data;
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
