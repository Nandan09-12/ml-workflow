import { ApiClientError } from "@ml-workflow/api-client";
import type { AppUser, ApprovalStatus, AuthStatus, Role } from "@ml-workflow/shared-types";
import { PropsWithChildren, useCallback, useEffect, useMemo, useState } from "react";
import { Linking } from "react-native";

import { AuthContext } from "./AuthContext";
import {
  clearAuthSessionSnapshot,
  setAuthSessionSnapshot,
  type AuthSessionSnapshot,
} from "./session";
import { apiClient } from "../lib/api";
import { hasSupabaseEnv } from "../lib/env";
import { supabase } from "../lib/supabase";

const mockApprovedUser: AppUser = {
  id: "46ec5f79-1c4d-4da0-9d58-73d98606ca56",
  email: "tester@nwm.example",
  fullName: "Drive Tester",
  role: "DRIVE_TESTER",
  approvalStatus: "APPROVED",
};

const mockPendingUser: AppUser = {
  ...mockApprovedUser,
  approvalStatus: "PENDING",
};

type BackendAccountStatus = "PENDING_APPROVAL" | "APPROVED" | "REJECTED" | "SUSPENDED";

type BackendRole = "DRIVE_TESTER" | "ADMIN";

type BackendMeUser = {
  id: string;
  auth_user_id: string;
  full_name: string;
  email: string;
  requested_role: BackendRole;
  approved_role: BackendRole | null;
  account_status: BackendAccountStatus;
};

const apiV1Prefix = "/api/v1";
const oauthRedirectUri = "mlworkflow://";
const authLoginRedirectUri = "mlworkflow://login";

function mapBackendStatus(status: BackendAccountStatus): ApprovalStatus {
  if (status === "PENDING_APPROVAL") {
    return "PENDING";
  }

  return status;
}

function mapBackendRole(user: BackendMeUser): Role {
  return user.approved_role ?? user.requested_role;
}

function mapBackendUser(user: BackendMeUser): AppUser {
  return {
    id: user.id,
    email: user.email,
    fullName: user.full_name,
    role: mapBackendRole(user),
    approvalStatus: mapBackendStatus(user.account_status),
  };
}

function deriveFullName(input: { email?: string | null; metadata?: Record<string, unknown> | null }) {
  const fullNameFromMetadata =
    typeof input.metadata?.full_name === "string"
      ? input.metadata.full_name
      : typeof input.metadata?.name === "string"
        ? input.metadata.name
        : null;

  if (fullNameFromMetadata?.trim()) {
    return fullNameFromMetadata.trim();
  }

  const emailPrefix = input.email?.split("@")[0]?.trim();
  if (!emailPrefix) {
    return "ML Workflow User";
  }

  return emailPrefix
    .split(/[._-]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function getStatusFromUser(user: AppUser | null): AuthStatus {
  if (!user) {
    return "SIGNED_OUT";
  }

  if (user.approvalStatus === "APPROVED") {
    return "APPROVED";
  }

  if (user.approvalStatus === "SUSPENDED") {
    return "SUSPENDED";
  }

  return "PENDING_APPROVAL";
}

function isTransientMissingBearerTokenError(error: unknown): boolean {
  if (error instanceof ApiClientError) {
    const message = error.message.toLowerCase();
    return error.status === 401 && message.includes("missing bearer token");
  }

  if (error instanceof Error) {
    return error.message.toLowerCase().includes("missing bearer token");
  }

  return false;
}

export function AuthProvider({ children }: PropsWithChildren) {
  const [isHydrating, setIsHydrating] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [user, setUser] = useState<AppUser | null>(null);
  const [session, setSession] = useState<AuthSessionSnapshot>({
    accessToken: null,
    appUserId: null,
    approvalStatus: null,
    authUserId: null,
    email: null,
    role: null,
  });

  const clearError = useCallback(() => {
    setErrorMessage(null);
  }, []);

  const applySession = ({
    accessToken = null,
    authUserId = null,
    user: nextUser,
    email,
  }: {
    accessToken?: string | null;
    authUserId?: string | null;
    email?: string | null;
    user: AppUser | null;
  }) => {
    const nextSession: AuthSessionSnapshot = {
      accessToken,
      appUserId: nextUser?.id ?? null,
      approvalStatus: nextUser?.approvalStatus ?? null,
      authUserId,
      email: nextUser?.email ?? email ?? null,
      role: nextUser?.role ?? null,
    };

    setSession(nextSession);
    setAuthSessionSnapshot(nextSession);
  };

  const loadCurrentUserFromBackend = async ({
    allowBootstrap = false,
    email,
    fullName,
  }: {
    allowBootstrap?: boolean;
    email?: string | null;
    fullName?: string;
  }) => {
    try {
      const me = await apiClient.get<BackendMeUser>(`${apiV1Prefix}/me`);
      const mappedUser = mapBackendUser(me);
      setUser(mappedUser);
      return mappedUser;
    } catch (error) {
      if (
        allowBootstrap &&
        error instanceof ApiClientError &&
        error.status === 404 &&
        email
      ) {
        const bootstrapResponse = await apiClient.post<BackendMeUser>(`${apiV1Prefix}/me/bootstrap`, {
          full_name: fullName?.trim() || deriveFullName({ email, metadata: null }),
          requested_role: "DRIVE_TESTER",
        });
        const mappedUser = mapBackendUser(bootstrapResponse);
        setUser(mappedUser);
        return mappedUser;
      }

      throw error;
    }
  };

  useEffect(() => {
    let isMounted = true;

    const applyUser = (nextUser: AppUser | null) => {
      if (!isMounted) {
        return;
      }

      setUser(nextUser);
    };

    const handleCallbackUrl = async (url: string) => {
      if (!hasSupabaseEnv || !url.startsWith(oauthRedirectUri)) {
        return false;
      }

      const parsedUrl = new URL(url);
      const authCode = parsedUrl.searchParams.get("code");

      if (!authCode) {
        return false;
      }

      const { error } = await supabase.auth.exchangeCodeForSession(authCode);
      if (error) {
        throw error;
      }

      const {
        data: { session },
      } = await supabase.auth.getSession();

      const sessionUser = session?.user;
      if (!sessionUser?.email) {
        throw new Error("Microsoft sign-in completed, but no user email was returned.");
      }

      const nextUser = await loadCurrentUserFromBackend({
        allowBootstrap: true,
        email: sessionUser.email,
        fullName: deriveFullName({
          email: sessionUser.email,
          metadata: sessionUser.user_metadata,
        }),
      });
      applyUser(nextUser);
      applySession({
        accessToken: session?.access_token ?? null,
        authUserId: sessionUser.id,
        email: sessionUser.email,
        user: nextUser,
      });

      return true;
    };

    async function hydrate() {
      if (!hasSupabaseEnv) {
        setIsHydrating(false);
        return;
      }

      const initialUrl = await Linking.getInitialURL();
      if (initialUrl) {
        try {
          await handleCallbackUrl(initialUrl);
        } catch (error) {
          if (isMounted) {
            setErrorMessage(
              error instanceof Error ? error.message : "Unable to complete Microsoft sign-in.",
            );
          }
        }
      }

      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!isMounted) {
        return;
      }

      if (session?.user?.email) {
        try {
          const nextUser = await loadCurrentUserFromBackend({
            email: session.user.email,
          });
          applyUser(nextUser);
          applySession({
            accessToken: session.access_token,
            authUserId: session.user.id,
            email: session.user.email,
            user: nextUser,
          });
        } catch (error) {
          setErrorMessage(
            error instanceof Error ? error.message : "Unable to load your account.",
          );
          applyUser(null);
          applySession({
            accessToken: session.access_token,
            authUserId: session.user.id,
            email: session.user.email,
            user: null,
          });
        }
      } else {
        applySession({ user: null });
      }

      setIsHydrating(false);
    }

    hydrate();

    const linkingSubscription = Linking.addEventListener("url", ({ url }) => {
      void handleCallbackUrl(url).catch((error) => {
        if (isMounted) {
          setErrorMessage(
            error instanceof Error ? error.message : "Unable to complete Microsoft sign-in.",
          );
        }
      });
    });

    const { data } = supabase.auth.onAuthStateChange((_event, session) => {
      if (!session?.user?.email) {
        applyUser(null);
        applySession({ user: null });
        return;
      }

      void loadCurrentUserFromBackend({
        email: session.user.email,
      })
        .then((nextUser) => {
          applyUser(nextUser);
          applySession({
            accessToken: session.access_token,
            authUserId: session.user.id,
            email: session.user.email,
            user: nextUser,
          });
        })
        .catch((error) => {
          if (isMounted && !isTransientMissingBearerTokenError(error)) {
            setErrorMessage(
              error instanceof Error ? error.message : "Unable to load your account.",
            );
          }
          applySession({
            accessToken: session.access_token,
            authUserId: session.user.id,
            email: session.user.email,
            user: null,
          });
        });
    });

    return () => {
      isMounted = false;
      linkingSubscription.remove();
      data.subscription.unsubscribe();
    };
  }, []);

  const signInWithPassword = async ({
    email,
    password,
  }: {
    email: string;
    password: string;
  }): Promise<AuthStatus | false> => {
    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      if (hasSupabaseEnv) {
        const { data: authData, error: authError } = await supabase.auth.signInWithPassword({
          email,
          password,
        });

        if (authError) {
          throw new Error(authError.message || "Invalid email or password");
        }

        if (!authData.user?.id) {
          throw new Error("Authentication failed. Please try again.");
        }

        // Persist the fresh Supabase token before API calls so apiClient sends Authorization.
        applySession({
          accessToken: authData.session?.access_token ?? null,
          authUserId: authData.user.id,
          email: authData.user.email,
          user: null,
        });

        let me: BackendMeUser;
        try {
          me = await apiClient.get<BackendMeUser>(`${apiV1Prefix}/me`);
        } catch (error) {
          if (error instanceof ApiClientError && error.status === 404) {
            me = await apiClient.post<BackendMeUser>(`${apiV1Prefix}/me/bootstrap`, {
              full_name: deriveFullName({
                email: authData.user.email,
                metadata: authData.user.user_metadata,
              }),
              requested_role: "DRIVE_TESTER",
            });
          } else {
            throw error;
          }
        }

        const mappedUser = mapBackendUser(me);

        if (mappedUser.approvalStatus === "SUSPENDED") {
          await supabase.auth.signOut();
          throw new Error("Your account has been suspended. Please contact support.");
        }

        if (mappedUser.approvalStatus === "REJECTED") {
          await supabase.auth.signOut();
          throw new Error("Your registration was rejected. Please contact support.");
        }

        setUser(mappedUser);
        applySession({
          accessToken: authData.session?.access_token ?? null,
          authUserId: authData.user.id,
          email: authData.user.email,
          user: mappedUser,
        });
        return getStatusFromUser(mappedUser);
      } else {
        const nextUser = email.toLowerCase().includes("pending")
          ? { ...mockPendingUser, email }
          : { ...mockApprovedUser, email };
        setUser(nextUser);
        applySession({
          authUserId: null,
          email,
          user: nextUser,
        });
        return getStatusFromUser(nextUser);
      }
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Unable to sign in right now.",
      );
      return false;
    } finally {
      setIsSubmitting(false);
    }
  };

  const signInWithMicrosoft = async () => {
    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      if (!hasSupabaseEnv) {
        throw new Error("Microsoft sign-in requires Supabase environment values.");
      }

      const { data, error } = await supabase.auth.signInWithOAuth({
        provider: "azure",
        options: {
          redirectTo: oauthRedirectUri,
          skipBrowserRedirect: true,
          queryParams: {
            prompt: "select_account",
          },
        },
      });

      if (error) {
        throw error;
      }

      if (!data?.url) {
        throw new Error("Microsoft sign-in URL was not returned.");
      }

      await Linking.openURL(data.url);
      return false;
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Unable to open Microsoft sign-in.",
      );
      return false;
    } finally {
      setIsSubmitting(false);
    }
  };

  const signUpWithPassword = async ({
    name,
    email,
    phoneNumber,
    password,
  }: {
    name: string;
    email: string;
    phoneNumber: string;
    password: string;
  }) => {
    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      if (hasSupabaseEnv) {
        const { data: authData, error } = await supabase.auth.signUp({
          email,
          password,
          options: {
            emailRedirectTo: authLoginRedirectUri,
            data: {
              full_name: name.trim(),
              phone_number: phoneNumber.trim(),
              approval_status: "PENDING_APPROVAL",
              requested_role: "DRIVE_TESTER",
            },
          },
        });

        if (error) {
          throw error;
        }

        if (!authData.session?.user?.email) {
          setErrorMessage("Account created. Check your email to confirm it, then log in.");
          return false;
        }

        const bootstrapResponse = await apiClient.post<BackendMeUser>(`${apiV1Prefix}/me/bootstrap`, {
          full_name: name.trim(),
          requested_role: "DRIVE_TESTER",
        });

        const nextUser = {
          ...mapBackendUser(bootstrapResponse),
          email: bootstrapResponse.email,
          fullName: bootstrapResponse.full_name,
        };

        setUser(nextUser);
        applySession({
          accessToken: authData.session?.access_token ?? null,
          authUserId: authData.session?.user?.id ?? null,
          email: authData.session?.user?.email ?? email,
          user: nextUser,
        });
      } else {
        const nextUser = {
          ...mockPendingUser,
          email,
          fullName: name,
        };
        setUser(nextUser);
        applySession({
          authUserId: null,
          email,
          user: nextUser,
        });
      }

      return true;
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Unable to register right now.",
      );
      return false;
    } finally {
      setIsSubmitting(false);
    }
  };

  const signOut = async () => {
    setErrorMessage(null);

    if (hasSupabaseEnv) {
      await supabase.auth.signOut();
    }

    setUser(null);
    setSession({
      accessToken: null,
      appUserId: null,
      approvalStatus: null,
      authUserId: null,
      email: null,
      role: null,
    });
    clearAuthSessionSnapshot();
  };

  const refreshApprovalStatus = async (): Promise<AuthStatus | false> => {
    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      if (!hasSupabaseEnv) {
        return getStatusFromUser(user);
      }

      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!session?.user?.email) {
        await signOut();
        return false;
      }

      const mappedUser = await loadCurrentUserFromBackend({
        email: session.user.email,
      });

      if (mappedUser.approvalStatus === "SUSPENDED") {
        await signOut();
        throw new Error("Your account has been suspended. Please contact support.");
      }

      if (mappedUser.approvalStatus === "REJECTED") {
        await signOut();
        throw new Error("Your registration was rejected. Please contact support.");
      }

      return getStatusFromUser(mappedUser);
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Unable to refresh your approval status.",
      );
      return false;
    } finally {
      setIsSubmitting(false);
    }
  };

  const value = useMemo(
    () => ({
      authStatus: getStatusFromUser(user),
      clearError,
      errorMessage,
      isHydrating,
      isSubmitting,
      refreshApprovalStatus,
      session,
      user,
      signInWithMicrosoft,
      signInWithPassword,
      signUpWithPassword,
      signOut,
    }),
    [errorMessage, isHydrating, isSubmitting, session, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
