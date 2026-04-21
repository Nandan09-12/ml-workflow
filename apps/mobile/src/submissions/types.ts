export type SubmissionStatus = "ONGOING" | "COMPLETED" | "ATTACHMENTS";

export type Attachment = {
  id: string;
  name: string;
  type: string;
  uri: string;
};

export type SubmissionPayload = {
  backendVersionNumber?: number;
  completedGrids: number;
  forceTestedGrids?: number;
  workDate: string;
  numberOfGrids: number;
  pendingGrids: number;
  region: "NE-UP" | "Central" | "South";
  skippedGrids: number;
  shift: "AM" | "PM";
  startTime: string;
  teamNumber: string;
  ticketNumber: string;
  workorderName: string;
};

export type SubmissionRecord = SubmissionPayload & {
  attachments?: Attachment[];
  createdAt: string;
  endTime?: string;
  id: string;
  status: SubmissionStatus;
};
