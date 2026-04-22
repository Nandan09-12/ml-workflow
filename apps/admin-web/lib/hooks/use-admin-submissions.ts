"use client";

import { useQuery } from "@tanstack/react-query";
import { apiGet, ApiError } from "@/lib/api/client";
import { queryKeys } from "@/lib/query/keys";
import type { SubmissionRecord, ApiSubmissionItem, HookPagination } from "@/lib/types/domain";

export interface AdminSubmissionsParams {
  work_date?: string;
  date_from?: string;
  date_to?: string;
  region?: string;
  tester?: string;
  workorder_code?: string;
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
}

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
    versionNumber: item.version_number,
  };
}

function buildQueryString(params: AdminSubmissionsParams): string {
  const p = new URLSearchParams();
  if (params.work_date) p.append("work_date", params.work_date);
  if (params.date_from) p.append("date_from", params.date_from);
  if (params.date_to) p.append("date_to", params.date_to);
  if (params.region) p.append("region", params.region);
  if (params.tester) p.append("tester", params.tester);
  if (params.workorder_code) p.append("workorder_code", params.workorder_code);
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
  const qs = buildQueryString(params);

  const filterRecord: Record<string, string> = {};
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined) filterRecord[k] = String(v);
  });

  const query = useQuery({
    queryKey: queryKeys.dailySubmissions(
      Object.keys(filterRecord).length > 0 ? filterRecord : undefined,
    ),
    queryFn: async () => await apiGet<ApiSubmissionsListResponse>(`/admin/submissions${qs}`),
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
