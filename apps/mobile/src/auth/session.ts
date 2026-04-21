import type { ApprovalStatus, Role } from "@ml-workflow/shared-types";

export type AuthSessionSnapshot = {
  accessToken: string | null;
  appUserId: string | null;
  approvalStatus: ApprovalStatus | null;
  authUserId: string | null;
  email: string | null;
  role: Role | null;
};

const emptySession: AuthSessionSnapshot = {
  accessToken: null,
  appUserId: null,
  approvalStatus: null,
  authUserId: null,
  email: null,
  role: null,
};

let currentSessionSnapshot: AuthSessionSnapshot = emptySession;

export function getAuthSessionSnapshot() {
  return currentSessionSnapshot;
}

export function setAuthSessionSnapshot(snapshot: AuthSessionSnapshot) {
  currentSessionSnapshot = snapshot;
}

export function clearAuthSessionSnapshot() {
  currentSessionSnapshot = emptySession;
}
