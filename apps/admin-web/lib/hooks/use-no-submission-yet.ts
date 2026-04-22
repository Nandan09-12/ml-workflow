"use client";

import { useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiGet, ApiError } from "@/lib/api/client";
import { queryKeys } from "@/lib/query/keys";
import { noSubmissionYet as mockNoSubmissionYet } from "@/lib/mock/data";
import type { NoSubmissionYetRecord, ApiNoSubmissionYetItem, HookPagination } from "@/lib/types/domain";

export interface NoSubmissionYetParams {
  work_date: string;
  page?: number;
  page_size?: number;
}

interface ApiNoSubmissionYetResponse {
  work_date: string;
  note: string;
  items: ApiNoSubmissionYetItem[];
  count: number;
  pagination: { page: number; page_size: number; total: number; total_pages: number };
}

export interface NoSubmissionYetResult {
  items: NoSubmissionYetRecord[];
  pagination: HookPagination;
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
  isFallback: boolean;
}

const mockPagination: HookPagination = {
  page: 1,
  pageSize: 20,
  total: mockNoSubmissionYet.length,
  totalPages: 1,
};

function mapItem(item: ApiNoSubmissionYetItem): NoSubmissionYetRecord {
  return {
    id: item.id,
    fullName: item.full_name,
    email: item.email,
    approvedRole: "DRIVE_TESTER",
    lastSubmissionDate: null,
    lastWorkorderCode: null,
  };
}

function buildQueryString(params: NoSubmissionYetParams): string {
  const p = new URLSearchParams();
  p.append("work_date", params.work_date);
  if (params.page) p.append("page", String(params.page));
  if (params.page_size) p.append("page_size", String(params.page_size));
  return `?${p.toString()}`;
}

export function useNoSubmissionYet(params: NoSubmissionYetParams): NoSubmissionYetResult {
  const fallbackUsedRef = useRef(false);
  const qs = buildQueryString(params);

  const query = useQuery({
    queryKey: queryKeys.noSubmissionYet(params.work_date),
    queryFn: async () => {
      fallbackUsedRef.current = false;
      try {
        return await apiGet<ApiNoSubmissionYetResponse>(
          `/admin/dashboard/no-submission-yet${qs}`,
        );
      } catch (error) {
        if (error instanceof ApiError) {
          if (error.status >= 500) {
            fallbackUsedRef.current = true;
            return null;
          }
          throw error;
        }
        fallbackUsedRef.current = true;
        return null;
      }
    },
    staleTime: 2 * 60 * 1000,
  });

  if (query.data === null) {
    return {
      items: mockNoSubmissionYet,
      pagination: mockPagination,
      isLoading: false,
      isError: false,
      error: null,
      isFallback: true,
    };
  }

  const items = (query.data?.items ?? []).map(mapItem);
  const raw = query.data?.pagination;
  const pagination: HookPagination = raw
    ? { page: raw.page, pageSize: raw.page_size, total: raw.total, totalPages: raw.total_pages }
    : mockPagination;

  return {
    items,
    pagination,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    isFallback: fallbackUsedRef.current,
  };
}
