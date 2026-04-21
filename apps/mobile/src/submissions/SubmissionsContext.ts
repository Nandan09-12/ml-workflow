import { createContext, useContext } from "react";

import type { SubmissionPayload, SubmissionRecord } from "./types";

export type SubmissionsContextValue = {
  addSubmission: (payload: SubmissionPayload) => SubmissionRecord;
  submissions: SubmissionRecord[];
  updateSubmission: (
    id: string,
    updates: Partial<
      Pick<
        SubmissionRecord,
        | "attachments"
        | "backendVersionNumber"
        | "completedGrids"
        | "endTime"
        | "forceTestedGrids"
        | "numberOfGrids"
        | "pendingGrids"
        | "skippedGrids"
        | "status"
      >
    >,
  ) => void;
};

export const SubmissionsContext = createContext<SubmissionsContextValue | null>(null);

export function useSubmissions() {
  const value = useContext(SubmissionsContext);

  if (!value) {
    throw new Error("useSubmissions must be used inside SubmissionsProvider");
  }

  return value;
}
