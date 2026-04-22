"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiPost } from "@/lib/api/client";
import { queryKeys } from "@/lib/query/keys";

export function useReopenSubmission() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: (submissionId: string) =>
      apiPost(`/admin/submissions/${submissionId}/reopen`, {}),
    onSuccess: (_data, submissionId) => {
      void qc.invalidateQueries({ queryKey: queryKeys.dailySubmission(submissionId) });
      void qc.invalidateQueries({ queryKey: queryKeys.dailySubmissions() });
      void qc.invalidateQueries({ queryKey: queryKeys.workorders() });
    },
  });
}
