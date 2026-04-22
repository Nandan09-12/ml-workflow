/**
 * Auth utility functions
 */

import { AppUser } from "@/lib/types/auth";

/**
 * Determine if a user can access admin web
 * Rules: must be ADMIN role AND APPROVED status
 */
export function isAdminUser(user: AppUser | null): boolean {
  if (!user) return false;
  return user.approved_role === "ADMIN" && user.account_status === "APPROVED";
}

/**
 * Get user access denial reason (if blocked)
 */
export function getAccessDenialReason(user: AppUser | null): string | null {
  if (!user) return "Not authenticated";
  if (user.account_status === "PENDING_APPROVAL") return "Your account is pending approval";
  if (user.account_status === "REJECTED") return "Your account has been rejected";
  if (user.account_status === "SUSPENDED") return "Your account has been suspended";
  if (user.approved_role !== "ADMIN") return "You do not have admin access";
  return null;
}
