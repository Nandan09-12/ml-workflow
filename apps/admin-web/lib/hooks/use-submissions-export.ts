"use client";

import { useMutation } from "@tanstack/react-query";
import { apiGet } from "@/lib/api/client";

export interface SubmissionsExportParams {
  work_date?: string;
  date_from?: string;
  date_to?: string;
  status?: string;
  shift?: string;
  ticket_number?: string;
  file_submission_pending?: boolean;
}

function buildQueryString(params: SubmissionsExportParams): string {
  const p = new URLSearchParams();
  if (params.work_date) p.append("work_date", params.work_date);
  if (params.date_from) p.append("date_from", params.date_from);
  if (params.date_to) p.append("date_to", params.date_to);
  if (params.status) p.append("status", params.status);
  if (params.shift) p.append("shift", params.shift);
  if (params.ticket_number) p.append("ticket_number", params.ticket_number);
  if (params.file_submission_pending !== undefined)
    p.append("file_submission_pending", String(params.file_submission_pending));
  const qs = p.toString();
  return qs ? `?${qs}` : "";
}

function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export function useSubmissionsExport() {
  return useMutation({
    mutationFn: async (params: SubmissionsExportParams) => {
      const qs = buildQueryString(params);
      const blob = await apiGet<Blob>(`/admin/reports/submissions/export${qs}`, {
        skipEnvelope: true,
      });
      const date = new Date().toISOString().slice(0, 10).replace(/-/g, "");
      triggerDownload(blob, `submissions_export_${date}.csv`);
    },
  });
}
