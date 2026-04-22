/**
 * Auth types for admin web
 */

export type AppUser = {
  id: string;
  email: string;
  full_name: string;
  approved_role: "ADMIN" | "DRIVE_TESTER" | null;
  account_status: "PENDING_APPROVAL" | "APPROVED" | "REJECTED" | "SUSPENDED";
};

export type AuthContext = {
  user: AppUser | null;
  loading: boolean;
  error: string | null;
};
