import { PropsWithChildren, useMemo, useState } from "react";

import { SubmissionsContext } from "./SubmissionsContext";
import type { SubmissionPayload, SubmissionRecord } from "./types";

const initialSubmissions: SubmissionRecord[] = [
  {
    workorderName: "Cluster 4",
    completedGrids: 18,
    createdAt: "2026-04-15T10:00:00.000Z",
    id: "1",
    numberOfGrids: 24,
    pendingGrids: 6,
    region: "NE-UP",
    skippedGrids: 0,
    shift: "AM",
    startTime: "08:15 AM",
    status: "ATTACHMENTS",
    teamNumber: "12",
    ticketNumber: "8891",
    workDate: "2026-04-15",
  },
  {
    workorderName: "Cluster 2",
    completedGrids: 11,
    createdAt: "2026-04-14T10:00:00.000Z",
    id: "2",
    numberOfGrids: 20,
    pendingGrids: 7,
    region: "Central",
    skippedGrids: 2,
    shift: "PM",
    startTime: "01:05 PM",
    status: "ONGOING",
    teamNumber: "18",
    ticketNumber: "7712",
    workDate: "2026-04-14",
  },
];

export function SubmissionsProvider({ children }: PropsWithChildren) {
  const [submissions, setSubmissions] = useState<SubmissionRecord[]>(initialSubmissions);

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
    [submissions],
  );

  return <SubmissionsContext.Provider value={value}>{children}</SubmissionsContext.Provider>;
}
