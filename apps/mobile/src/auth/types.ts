import type { AppUser, AuthStatus } from "@ml-workflow/shared-types";

import type { AuthSessionSnapshot } from "./session";

export type SignInResult = AuthStatus | "EMAIL_NOT_CONFIRMED" | false;
export type SignUpResult = true | "VERIFY_EMAIL_REQUIRED" | "EMAIL_ALREADY_USED" | false;

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
  }) => Promise<SignInResult>;
  signUpWithPassword: (input: {
    name: string;
    email: string;
    phoneNumber: string;
    password: string;
  }) => Promise<SignUpResult>;
  signOut: () => Promise<void>;
};
