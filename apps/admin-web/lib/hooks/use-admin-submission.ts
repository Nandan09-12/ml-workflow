"use client";

import { useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiGet, ApiError } from "@/lib/api/client";
import { queryKeys } from "@/lib/query/keys";
import { submissions as mockSubmissions } from "@/lib/mock/data";
import type { SubmissionRecord, ApiSubmissionItem } from "@/lib/types/domain";

export interface AdminSubmissionResult {
  submission: SubmissionRecord | null;
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
  isFallback: boolean;
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

export function useAdminSubmission(submissionId: string): AdminSubmissionResult {
  const fallbackRef = useRef<SubmissionRecord | null>(null);

  const { data, isLoading, isError, error } = useQuery({
    queryKey: queryKeys.dailySubmission(submissionId),
    queryFn: async () => {
      const res = await apiGet<ApiSubmissionItem>(`/admin/submissions/${submissionId}`);
      return res;
    },
    enabled: Boolean(submissionId),
    retry: (count, err) => {
      if (err instanceof ApiError && err.status >= 400 && err.status < 500) return false;
      return count < 2;
    },
  });

  if (isError) {
    const err = error as Error;
    const is4xx = err instanceof ApiError && err.status >= 400 && err.status < 500;
    if (!is4xx && !fallbackRef.current) {
      const found = mockSubmissions.find((s) => s.id === submissionId) ?? null;
      fallbackRef.current = found;
    }
    return {
      submission: is4xx ? null : fallbackRef.current,
      isLoading: false,
      isError: true,
      error: err,
      isFallback: !is4xx,
    };
  }

  if (data) fallbackRef.current = null;

  return {
    submission: data ? mapItem(data) : null,
    isLoading,
    isError: false,
    error: null,
    isFallback: false,
  };
}
