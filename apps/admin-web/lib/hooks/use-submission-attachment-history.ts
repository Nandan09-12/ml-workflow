"use client";

import { useQuery } from "@tanstack/react-query";
import { apiGet, ApiError } from "@/lib/api/client";
import { queryKeys } from "@/lib/query/keys";
import type { ApiAttachmentHistoryItem } from "@/lib/types/domain";

interface ApiAttachmentHistoryResponse {
  items: ApiAttachmentHistoryItem[];
  count: number;
}

export interface SubmissionAttachmentHistoryResult {
  items: ApiAttachmentHistoryItem[];
  count: number;
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
}

export function useSubmissionAttachmentHistory(
  submissionId: string,
): SubmissionAttachmentHistoryResult {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: queryKeys.submissionAttachmentHistory(submissionId),
    queryFn: async () => {
      const res = await apiGet<ApiAttachmentHistoryResponse>(
        `/admin/submissions/${submissionId}/attachments/history`,
      );
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
