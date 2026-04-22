"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiPatch } from "@/lib/api/client";
import { queryKeys } from "@/lib/query/keys";
import type { Shift } from "@/lib/types/domain";

export interface EditSubmissionPayload {
  submissionId: string;
  version_number: number;
  work_date?: string;
  shift?: Shift;
  team_number?: string | null;
  ticket_number?: string | null;
  skipped_grids?: number;
  force_tested_grids?: number;
  completed_grids?: number;
}

export function useEditSubmission() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: ({ submissionId, ...body }: EditSubmissionPayload) =>
      apiPatch(`/admin/submissions/${submissionId}`, body),
    onSuccess: (_data, variables) => {
      void qc.invalidateQueries({ queryKey: queryKeys.dailySubmission(variables.submissionId) });
      void qc.invalidateQueries({ queryKey: queryKeys.dailySubmissions() });
    },
  });
}
