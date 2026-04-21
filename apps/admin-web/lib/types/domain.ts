export type SubmissionStatus = "IN_PROGRESS" | "CHECKED_OUT" | "COMPLETED";
export type WorkorderStatus = "ACTIVE" | "COMPLETED";
export type AccountStatus = "PENDING_APPROVAL" | "APPROVED" | "REJECTED" | "SUSPENDED";
export type UserRole = "ADMIN" | "DRIVE_TESTER";
export type Region = "NE_UP" | "CENTRAL" | "SOUTH_FLORIDA";
export type Shift = "AM" | "PM";
export type FileState = "FILE_PENDING" | "ATTACHED" | "NOT_REQUIRED";

export interface AdminUserSummary {
  initials: string;
  fullName: string;
  role: UserRole;
}

export interface MetricSummary {
  label: string;
  value: string;
  detail: string;
  tone?: "brand" | "success" | "warning" | "danger";
  href?: string;
}

export interface WorkorderRecord {
  id: string;
  workorderCode: string;
  region: Region;
  totalGrids: number;
  completedGrids: number;
  skippedGrids: number;
  remainingGrids: number;
  progressPercent: number;
  status: WorkorderStatus;
  createdAt: string;
  updatedAt: string;
}

export interface SubmissionRecord {
  id: string;
  workDate: string;
  testerName: string;
  testerEmail: string;
  workorderCode: string;
  region: Region;
  shift: Shift;
  ticketNumber: string;
  completedGrids: number;
  skippedGrids: number;
  forceTestedGrids: number;
  status: SubmissionStatus;
  workorderStatus: WorkorderStatus;
  fileState: FileState;
  startedAt: string;
  endedAt: string | null;
  updatedAt: string;
  fileSubmissionPending: boolean;
}

export interface AttachmentEvent {
  id: string;
  title: string;
  detail: string;
}

export interface AuditEvent {
  id: string;
  title: string;
  detail: string;
}

export interface UserRecord {
  id: string;
  fullName: string;
  email: string;
  requestedRole: UserRole;
  approvedRole: UserRole | null;
  accountStatus: AccountStatus;
  createdAt: string;
  lastLogin: string | null;
  approvedAt: string | null;
}

export interface PendingUserRecord {
  id: string;
  fullName: string;
  email: string;
  requestedRole: UserRole;
  requestedAt: string;
  note: string;
}

export interface NoSubmissionYetRecord {
  id: string;
  fullName: string;
  email: string;
  approvedRole: UserRole;
  lastSubmissionDate: string | null;
  lastWorkorderCode: string | null;
}
