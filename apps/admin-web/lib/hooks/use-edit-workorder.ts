"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiPatch } from "@/lib/api/client";
import { queryKeys } from "@/lib/query/keys";
import type { Region } from "@/lib/types/domain";

export interface EditWorkorderPayload {
  workorderId: string;
  workorder_code?: string;
  region?: Region;
  total_grids?: number;
}

export function useEditWorkorder() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: ({ workorderId, ...body }: EditWorkorderPayload) =>
      apiPatch(`/admin/workorders/${workorderId}`, body),
    onSuccess: (_data, variables) => {
      void qc.invalidateQueries({ queryKey: queryKeys.workorder(variables.workorderId) });
      void qc.invalidateQueries({ queryKey: queryKeys.workorders() });
    },
  });
}
