"use client";

import { useMutation } from "@tanstack/react-query";
import { apiPost } from "@/lib/api/client";

interface DownloadUrlResponse {
  url: string;
  expires_in_seconds: number;
}

export function useAttachmentDownload() {
  return useMutation({
    mutationFn: async (attachmentId: string) => {
      const res = await apiPost<DownloadUrlResponse>(
        `/attachments/${attachmentId}/download-url`,
        {},
      );
      window.open(res.url, "_blank", "noopener,noreferrer");
      return res;
    },
  });
}
