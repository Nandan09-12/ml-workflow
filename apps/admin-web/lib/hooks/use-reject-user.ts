"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiPost } from "@/lib/api/client";
import { queryKeys } from "@/lib/query/keys";

export function useRejectUser() {
  const qc = useQueryClient();

  return useMutation({
    mutationFn: (userId: string) => apiPost(`/admin/users/${userId}/reject`, {}),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: queryKeys.users() });
      void qc.invalidateQueries({ queryKey: queryKeys.pendingUsers });
    },
  });
}
