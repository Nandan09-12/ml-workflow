/**
 * Test fixtures for different auth/user states
 */

import { AppUser } from "@/lib/types/auth";
export { isAdminUser, getAccessDenialReason } from "@/lib/utils/auth";

export const ADMIN_USER: AppUser = {
  id: "user-admin-1",
  email: "admin@example.com",
  full_name: "Admin User",
  approved_role: "ADMIN",
  account_status: "APPROVED",
};

export const DRIVE_TESTER_USER: AppUser = {
  id: "user-tester-1",
  email: "tester@example.com",
  full_name: "Drive Tester",
  approved_role: "DRIVE_TESTER",
  account_status: "APPROVED",
};

export const PENDING_USER: AppUser = {
  id: "user-pending-1",
  email: "pending@example.com",
  full_name: "Pending User",
  approved_role: null,
  account_status: "PENDING_APPROVAL",
};

export const REJECTED_USER: AppUser = {
  id: "user-rejected-1",
  email: "rejected@example.com",
  full_name: "Rejected User",
  approved_role: null,
  account_status: "REJECTED",
};

export const SUSPENDED_USER: AppUser = {
  id: "user-suspended-1",
  email: "suspended@example.com",
  full_name: "Suspended User",
  approved_role: "DRIVE_TESTER",
  account_status: "SUSPENDED",
};
