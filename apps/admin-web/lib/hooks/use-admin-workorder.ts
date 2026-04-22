"use client";

import { useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiGet, ApiError } from "@/lib/api/client";
import { queryKeys } from "@/lib/query/keys";
import { workorders as mockWorkorders } from "@/lib/mock/data";
import type {
  WorkorderRecord,
  SubmissionRecord,
  ApiWorkorderDetailResponse,
  ApiSubmissionItem,
} from "@/lib/types/domain";

export interface WorkorderDetailRecord extends WorkorderRecord {
  submissions: SubmissionRecord[];
}

export interface AdminWorkorderResult {
  workorder: WorkorderDetailRecord | null;
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
  isFallback: boolean;
}

function mapSubmission(item: ApiSubmissionItem): SubmissionRecord {
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

function mapWorkorder(item: ApiWorkorderDetailResponse): WorkorderDetailRecord {
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
    submissions: item.submissions.map(mapSubmission),
  };
}

export function useAdminWorkorder(workorderId: string): AdminWorkorderResult {
  const fallbackRef = useRef<WorkorderDetailRecord | null>(null);

  const { data, isLoading, isError, error } = useQuery({
    queryKey: queryKeys.workorder(workorderId),
    queryFn: async () => {
      const res = await apiGet<ApiWorkorderDetailResponse>(`/admin/workorders/${workorderId}`);
      return res;
    },
    enabled: Boolean(workorderId),
    retry: (count, err) => {
      if (err instanceof ApiError && err.status >= 400 && err.status < 500) return false;
      return count < 2;
    },
  });

  if (isError) {
    const err = error as Error;
    const is4xx = err instanceof ApiError && err.status >= 400 && err.status < 500;
    if (!is4xx && !fallbackRef.current) {
      const found = mockWorkorders.find((w) => w.id === workorderId);
      fallbackRef.current = found ? { ...found, submissions: [] } : null;
    }
    return {
      workorder: is4xx ? null : fallbackRef.current,
      isLoading: false,
      isError: true,
      error: err,
      isFallback: !is4xx,
    };
  }

  if (data) fallbackRef.current = null;

  return {
    workorder: data ? mapWorkorder(data) : null,
    isLoading,
    isError: false,
    error: null,
    isFallback: false,
  };
}
