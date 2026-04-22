"use client";

import { useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiGet, ApiError } from "@/lib/api/client";
import { queryKeys } from "@/lib/query/keys";
import { submissions as mockSubmissions } from "@/lib/mock/data";
import type { SubmissionRecord, ApiSubmissionItem, HookPagination } from "@/lib/types/domain";

export interface AdminSubmissionsParams {
  work_date?: string;
  date_from?: string;
  date_to?: string;
  status?: string;
  shift?: string;
  file_submission_pending?: boolean;
  page?: number;
  page_size?: number;
}

interface ApiSubmissionsListResponse {
  items: ApiSubmissionItem[];
  pagination: { page: number; page_size: number; total: number; total_pages: number };
}

export interface AdminSubmissionsResult {
  items: SubmissionRecord[];
  pagination: HookPagination;
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
  isFallback: boolean;
}

const mockPagination: HookPagination = {
  page: 1,
  pageSize: 20,
  total: mockSubmissions.length,
  totalPages: 1,
};

function mapItem(item: ApiSubmissionItem): SubmissionRecord {
  return {
    id: item.id,
    workDate: item.work_date,
    testerName: item.submitter_name_snapshot,
    testerEmail: item.submitter_email_snapshot,
    workorderCode: item.workorder_summary?.workorder_code ?? "",
    region: item.workorder_summary?.region ?? "NE_UP",
    shift: item.shift,
    ticketNumber: item.ticket_number ?? "",
    completedGrids: item.completed_grids,
    skippedGrids: item.skipped_grids,
    forceTestedGrids: item.force_tested_grids,
    status: item.status,
    workorderStatus: item.workorder_summary?.status ?? "ACTIVE",
    fileState: item.file_submission_pending ? "FILE_PENDING" : "ATTACHED",
    startedAt: item.started_at,
    endedAt: item.ended_at,
    updatedAt: item.updated_at,
    fileSubmissionPending: item.file_submission_pending,
  };
}

function buildQueryString(params: AdminSubmissionsParams): string {
  const p = new URLSearchParams();
  if (params.work_date) p.append("work_date", params.work_date);
  if (params.date_from) p.append("date_from", params.date_from);
  if (params.date_to) p.append("date_to", params.date_to);
  if (params.status) p.append("status", params.status);
  if (params.shift) p.append("shift", params.shift);
  if (params.file_submission_pending !== undefined)
    p.append("file_submission_pending", String(params.file_submission_pending));
  if (params.page) p.append("page", String(params.page));
  if (params.page_size) p.append("page_size", String(params.page_size));
  const qs = p.toString();
  return qs ? `?${qs}` : "";
}

export function useAdminSubmissions(params: AdminSubmissionsParams): AdminSubmissionsResult {
  const fallbackUsedRef = useRef(false);
  const qs = buildQueryString(params);

  const filterRecord: Record<string, string> = {};
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined) filterRecord[k] = String(v);
  });

  const query = useQuery({
    queryKey: queryKeys.dailySubmissions(
      Object.keys(filterRecord).length > 0 ? filterRecord : undefined,
    ),
    queryFn: async () => {
      fallbackUsedRef.current = false;
      try {
        return await apiGet<ApiSubmissionsListResponse>(`/admin/submissions${qs}`);
      } catch (error) {
        if (error instanceof ApiError) {
          if (error.status >= 500) {
            fallbackUsedRef.current = true;
            return null;
          }
          throw error;
        }
        // Network error — fallback
        fallbackUsedRef.current = true;
        return null;
      }
    },
    staleTime: 2 * 60 * 1000,
  });

  if (query.data === null) {
    return {
      items: mockSubmissions,
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
