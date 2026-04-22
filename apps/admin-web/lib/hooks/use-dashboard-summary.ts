"use client";

import { useQuery } from "@tanstack/react-query";
import { useRef } from "react";
import { apiGet, ApiError } from "@/lib/api/client";
import { queryKeys } from "@/lib/query/keys";

export interface DashboardSummaryFilters {
  work_date?: string;
  date_from?: string;
  date_to?: string;
}

export interface DashboardSummary {
  approved_drive_testers: number;
  ongoing_submissions: number;
  completed_submissions: number;
  no_submission_yet: number;
  active_workorders: number;
  completed_workorders: number;
  reference_date: string;
}

export interface UseDashboardSummaryResult {
  data: DashboardSummary | undefined;
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
  status: "pending" | "error" | "success";
  isFallback: boolean;
}

// Mock dashboard summary data for fallback
const mockDashboardSummary: DashboardSummary = {
  approved_drive_testers: 12,
  ongoing_submissions: 5,
  completed_submissions: 41,
  no_submission_yet: 7,
  active_workorders: 18,
  completed_workorders: 3,
  reference_date: new Date().toISOString().split("T")[0],
};

function buildQueryString(filters?: DashboardSummaryFilters): string {
  if (!filters || Object.keys(filters).length === 0) {
    return "";
  }

  const params = new URLSearchParams();
  if (filters.work_date) params.append("work_date", filters.work_date);
  if (filters.date_from) params.append("date_from", filters.date_from);
  if (filters.date_to) params.append("date_to", filters.date_to);

  return `?${params.toString()}`;
}

export function useDashboardSummary(
  filters?: DashboardSummaryFilters
): UseDashboardSummaryResult {
  const queryString = buildQueryString(filters);
  const fallbackUsedRef = useRef(false);

  // Convert filters to Record for queryKeys
  const filterRecord: Record<string, string> = {};
  if (filters?.work_date) filterRecord.work_date = filters.work_date;
  if (filters?.date_from) filterRecord.date_from = filters.date_from;
  if (filters?.date_to) filterRecord.date_to = filters.date_to;

  const query = useQuery({
    queryKey: queryKeys.dashboard(Object.keys(filterRecord).length > 0 ? filterRecord : undefined),
    queryFn: async () => {
      fallbackUsedRef.current = false;
      
      try {
        return await apiGet<DashboardSummary>(`/admin/dashboard/summary${queryString}`);
      } catch (error) {
        // Fallback to mock on network errors or 5xx
        if (error instanceof ApiError) {
          if (error.status >= 500) {
            // 5xx error - use fallback
            fallbackUsedRef.current = true;
            return mockDashboardSummary;
          }
          // 4xx error - re-throw (don't fallback)
          throw error;
        }
        // Network error or other errors - use fallback
        fallbackUsedRef.current = true;
        return mockDashboardSummary;
      }
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: (failureCount, error) => {
      // Don't retry on 4xx errors
      if (error instanceof ApiError && error.status < 500) {
        return false;
      }
      // Retry on 5xx and network errors up to 1 time
      return failureCount < 1;
    },
  });

  return {
    data: query.data,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error as Error | null,
    status: query.status,
    isFallback: fallbackUsedRef.current,
  };
}
