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
  versionNumber: number;
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

// ─── API response item shapes (snake_case — exactly as returned by backend) ────

export interface ApiWorkorderItem {
  id: string;
  workorder_code: string;
  region: Region;
  status: WorkorderStatus;
  total_grids: number;
  completed_grids: number;
  skipped_grids: number;
  remaining_grids: number;
  progress_percent: number;
  created_at: string;
  updated_at: string;
}

export interface ApiSubmissionWorkorderSummary {
  workorder_code: string;
  region: Region;
  status: WorkorderStatus;
  total_grids: number;
  completed_grids: number;
  skipped_grids: number;
  remaining_grids: number;
  progress_percent: number;
}

export interface ApiSubmissionItem {
  id: string;
  client_generated_id: string;
  workorder_id: string;
  owner_user_id: string;
  submitter_name_snapshot: string;
  submitter_email_snapshot: string;
  work_date: string;
  shift: Shift;
  team_number: string | null;
  ticket_number: string | null;
  skipped_grids: number;
  force_tested_grids: number;
  completed_grids: number;
  status: SubmissionStatus;
  version_number: number;
  started_at: string;
  ended_at: string | null;
  created_at: string;
  updated_at: string;
  file_submission_pending: boolean;
  workorder_summary: ApiSubmissionWorkorderSummary | null;
}

export interface ApiUserItem {
  id: string;
  auth_user_id: string;
  full_name: string;
  email: string;
  requested_role: UserRole;
  approved_role: UserRole | null;
  account_status: AccountStatus;
  approved_at: string | null;
  approved_by_user_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApiNoSubmissionYetItem {
  id: string;
  full_name: string;
  email: string;
}

export interface ApiPagination {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

// ─── Wave 5: audit, attachment history, workorder detail ────────────────────────

export interface ApiAuditItem {
  id: string;
  submission_id: string;
  action_type: string;
  actor_user_id: string;
  actor_role: string;
  source: string;
  changed_fields_json: { fields: string[] } | null;
  before_snapshot_json: Record<string, unknown> | null;
  after_snapshot_json: Record<string, unknown> | null;
  created_at: string;
}

export interface ApiAttachmentHistoryItem {
  id: string;
  submission_id: string;
  file_name: string;
  bucket_name: string;
  object_path: string;
  mime_type: string;
  file_extension: string;
  file_size_bytes: number;
  uploaded_by_user_id: string;
  uploaded_at: string;
  is_active: boolean;
}

export interface ApiWorkorderDetailResponse extends ApiWorkorderItem {
  submissions: ApiSubmissionItem[];
}

// ─── Hook pagination (camelCase — used inside hooks and page components) ────────

export interface HookPagination {
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
}
