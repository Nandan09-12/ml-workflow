"use client";

import { useQuery } from "@tanstack/react-query";
import { apiGet, ApiError } from "@/lib/api/client";
import { queryKeys } from "@/lib/query/keys";
import type { ApiAuditItem } from "@/lib/types/domain";

interface ApiAuditListResponse {
  items: ApiAuditItem[];
  count: number;
}

export interface SubmissionAuditResult {
  items: ApiAuditItem[];
  count: number;
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
}

export function useSubmissionAudit(submissionId: string): SubmissionAuditResult {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: queryKeys.submissionAudit(submissionId),
    queryFn: async () => {
      const res = await apiGet<ApiAuditListResponse>(`/admin/submissions/${submissionId}/audit`);
      return res;
    },
    enabled: Boolean(submissionId),
    retry: (count, err) => {
      if (err instanceof ApiError && err.status >= 400 && err.status < 500) return false;
      return count < 2;
    },
  });

  return {
    items: data?.items ?? [],
    count: data?.count ?? 0,
    isLoading,
    isError,
    error: error as Error | null,
  };
}
