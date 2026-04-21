import { PropsWithChildren, useCallback, useMemo, useState } from "react";

import { apiClient } from "../lib/api";
import { SubmissionsContext } from "./SubmissionsContext";
import type { SubmissionPayload, SubmissionRecord } from "./types";

type BackendSubmission = {
  id: string;
  work_date: string;
  shift: "AM" | "PM";
  team_number: string | null;
  ticket_number: string | null;
  skipped_grids: number;
  force_tested_grids: number;
  completed_grids: number;
  status: "IN_PROGRESS" | "CHECKED_OUT" | "COMPLETED";
  version_number: number;
  started_at: string;
  ended_at: string | null;
  created_at: string;
  file_submission_pending: boolean;
  workorder_summary: {
    workorder_code: string;
    total_grids: number;
    region: "NE_UP" | "CENTRAL" | "SOUTH_FLORIDA";
  } | null;
};

type ListSubmissionsResponse = {
  items: BackendSubmission[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
  };
};

function toLocalRegion(region: "NE_UP" | "CENTRAL" | "SOUTH_FLORIDA" | undefined): SubmissionRecord["region"] {
  if (region === "NE_UP") {
    return "NE-UP";
  }
  if (region === "CENTRAL") {
    return "Central";
  }
  return "South";
}

function toDisplayTime(isoTimestamp: string | null | undefined) {
  if (!isoTimestamp) {
    return undefined;
  }

  const parsed = new Date(isoTimestamp);
  if (Number.isNaN(parsed.getTime())) {
    return undefined;
  }

  return parsed.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function toLocalStatus(item: BackendSubmission): SubmissionRecord["status"] {
  if (item.status === "COMPLETED") {
    return "COMPLETED";
  }
  if (item.file_submission_pending) {
    return "ATTACHMENTS";
  }
  return "ONGOING";
}

function toSubmissionRecord(item: BackendSubmission): SubmissionRecord {
  const totalGrids = item.workorder_summary?.total_grids ?? item.completed_grids + item.skipped_grids;
  return {
    backendVersionNumber: item.version_number,
    completedGrids: item.completed_grids,
    createdAt: item.created_at,
    endTime: toDisplayTime(item.ended_at),
    forceTestedGrids: item.force_tested_grids,
    id: item.id,
    numberOfGrids: totalGrids,
    pendingGrids: Math.max(totalGrids - item.completed_grids - item.skipped_grids, 0),
    region: toLocalRegion(item.workorder_summary?.region),
    shift: item.shift,
    skippedGrids: item.skipped_grids,
    startTime: toDisplayTime(item.started_at) ?? "",
    status: toLocalStatus(item),
    teamNumber: item.team_number ?? "",
    ticketNumber: item.ticket_number ?? "",
    workDate: item.work_date,
    workorderName: item.workorder_summary?.workorder_code ?? "Workorder",
  };
}

export function SubmissionsProvider({ children }: PropsWithChildren) {
  const [submissions, setSubmissions] = useState<SubmissionRecord[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const loadSubmissions = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await apiClient.get<ListSubmissionsResponse>("/api/v1/submissions");
      const mapped = response.items.map(toSubmissionRecord);
      setSubmissions(mapped);
      return mapped;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const value = useMemo(
    () => ({
      addSubmission: (payload: SubmissionPayload) => {
        const record: SubmissionRecord = {
          ...payload,
          createdAt: new Date().toISOString(),
          id: String(Date.now()),
          status: "ONGOING",
        };

        setSubmissions((current) => [record, ...current]);
        return record;
      },
      isLoading,
      loadSubmissions,
      submissions,
      updateSubmission: (
        id: string,
        updates: Partial<
          Pick<
            SubmissionRecord,
            | "backendVersionNumber"
            | "completedGrids"
            | "numberOfGrids"
            | "pendingGrids"
            | "skippedGrids"
            | "status"
            | "endTime"
            | "forceTestedGrids"
            | "attachments"
          >
        >,
      ) => {
        setSubmissions((current) =>
          current.map((submission) =>
            submission.id === id ? { ...submission, ...updates } : submission,
          ),
        );
      },
    }),
    [isLoading, loadSubmissions, submissions],
  );

  return <SubmissionsContext.Provider value={value}>{children}</SubmissionsContext.Provider>;
}
