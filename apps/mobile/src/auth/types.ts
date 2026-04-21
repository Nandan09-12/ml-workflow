import type { AppUser, AuthStatus } from "@ml-workflow/shared-types";

import type { AuthSessionSnapshot } from "./session";

export type AuthContextValue = {
  authStatus: AuthStatus;
  errorMessage: string | null;
  isHydrating: boolean;
  isSubmitting: boolean;
  session: AuthSessionSnapshot;
  user: AppUser | null;
  clearError: () => void;
  refreshApprovalStatus: () => Promise<AuthStatus | false>;
  signInWithMicrosoft: () => Promise<boolean>;
  signInWithPassword: (input: {
    email: string;
    password: string;
  }) => Promise<AuthStatus | false>;
  signUpWithPassword: (input: {
    name: string;
    email: string;
    phoneNumber: string;
    password: string;
  }) => Promise<boolean>;
  signOut: () => Promise<void>;
};
