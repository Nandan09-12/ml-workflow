"use client";

/**
 * AdminGuard - Component for protecting admin-only pages
 * 
 * Shows loading state, access denied message, or renders children based on auth status
 */

import React from "react";
import { useAuth } from "@/lib/hooks/useAuth";
import { getAccessDenialReason } from "@/lib/utils/auth";
import { getSupabaseBrowserClient } from "@/lib/supabase/client";

export interface AdminGuardProps {
  children: React.ReactNode;
}

/**
 * Wraps pages/components to require ADMIN access
 * 
 * States:
 * - Loading: Shows spinner while fetching current user
 * - Error: Shows error message if API call fails
 * - Access Denied: Shows specific reason why user can't access (pending, rejected, suspended, non-admin)
 * - Authorized: Shows children when user is approved ADMIN
 */
export function AdminGuard({ children }: AdminGuardProps) {
  const { user, loading, error, isAdmin } = useAuth();
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [signInError, setSignInError] = React.useState<string | null>(null);
  const [isSigningIn, setIsSigningIn] = React.useState(false);

  const handleSignIn = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSignInError(null);

    const supabase = getSupabaseBrowserClient();
    if (!supabase) {
      setSignInError("Supabase client is not configured. Check frontend env values.");
      return;
    }

    setIsSigningIn(true);
    const { error: authError } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    setIsSigningIn(false);

    if (authError) {
      setSignInError(authError.message);
      return;
    }

    window.location.reload();
  };

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  // API error
  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600 mb-4">Error</h1>
          <p className="text-gray-600">{error}</p>
        </div>
      </div>
    );
  }

  // Not authenticated or not authorized
  if (!user || !isAdmin()) {
    const denialReason =
      getAccessDenialReason(user) || "Access denied";
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="w-full max-w-md rounded-lg border border-gray-200 bg-white p-6 text-center shadow-sm">
          <h1 className="text-2xl font-bold text-red-600 mb-4">Access Denied</h1>
          <p className="text-gray-600">{denialReason}</p>

          {denialReason === "Not authenticated" ? (
            <form className="mt-6 space-y-3 text-left" onSubmit={handleSignIn}>
              <label className="block">
                <span className="mb-1 block text-sm font-medium text-gray-700">Email</span>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none"
                  placeholder="you@example.com"
                />
              </label>

              <label className="block">
                <span className="mb-1 block text-sm font-medium text-gray-700">Password</span>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none"
                  placeholder="Your password"
                />
              </label>

              {signInError ? <p className="text-sm text-red-600">{signInError}</p> : null}

              <button
                type="submit"
                disabled={isSigningIn}
                className="w-full rounded-md bg-gray-900 px-3 py-2 text-sm font-medium text-white hover:bg-gray-800 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isSigningIn ? "Signing in..." : "Sign in"}
              </button>
            </form>
          ) : null}
        </div>
      </div>
    );
  }

  // Authorized - show children
  return <>{children}</>;
}
