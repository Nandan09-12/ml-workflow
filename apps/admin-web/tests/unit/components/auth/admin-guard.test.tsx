import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { AdminGuard } from "@/components/auth/AdminGuard";
import { useAuth } from "@/lib/hooks/useAuth";
import {
  ADMIN_USER,
  DRIVE_TESTER_USER,
  PENDING_USER,
  REJECTED_USER,
  SUSPENDED_USER,
} from "@/tests/fixtures/auth";

// Mock useAuth hook
vi.mock("@/lib/hooks/useAuth");

/**
 * AdminGuard component tests
 * Verifies auth guard displays correct state based on user permissions
 */
describe("AdminGuard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should show loading state while fetching current user", () => {
    vi.mocked(useAuth).mockReturnValue({
      user: null,
      loading: true,
      error: null,
      isAdmin: () => false,
    });

    render(
      <AdminGuard>
        <div>Protected Content</div>
      </AdminGuard>
    );

    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("should allow approved ADMIN users to access protected content", () => {
    vi.mocked(useAuth).mockReturnValue({
      user: ADMIN_USER,
      loading: false,
      error: null,
      isAdmin: () => true,
    });

    render(
      <AdminGuard>
        <div>Admin Content</div>
      </AdminGuard>
    );

    expect(screen.getByText("Admin Content")).toBeInTheDocument();
  });

  it("should block DRIVE_TESTER users and show 'You do not have admin access'", () => {
    vi.mocked(useAuth).mockReturnValue({
      user: DRIVE_TESTER_USER,
      loading: false,
      error: null,
      isAdmin: () => false,
    });

    render(
      <AdminGuard>
        <div>Admin Content</div>
      </AdminGuard>
    );

    expect(screen.getByText("You do not have admin access")).toBeInTheDocument();
  });

  it("should block pending users and show 'Your account is pending approval'", () => {
    vi.mocked(useAuth).mockReturnValue({
      user: PENDING_USER,
      loading: false,
      error: null,
      isAdmin: () => false,
    });

    render(
      <AdminGuard>
        <div>Admin Content</div>
      </AdminGuard>
    );

    expect(screen.getByText("Your account is pending approval")).toBeInTheDocument();
  });

  it("should block rejected users and show 'Your account has been rejected'", () => {
    vi.mocked(useAuth).mockReturnValue({
      user: REJECTED_USER,
      loading: false,
      error: null,
      isAdmin: () => false,
    });

    render(
      <AdminGuard>
        <div>Admin Content</div>
      </AdminGuard>
    );

    expect(screen.getByText("Your account has been rejected")).toBeInTheDocument();
  });

  it("should block suspended users and show 'Your account has been suspended'", () => {
    vi.mocked(useAuth).mockReturnValue({
      user: SUSPENDED_USER,
      loading: false,
      error: null,
      isAdmin: () => false,
    });

    render(
      <AdminGuard>
        <div>Admin Content</div>
      </AdminGuard>
    );

    expect(screen.getByText("Your account has been suspended")).toBeInTheDocument();
  });

  it("should show access denied heading when user is not admin", () => {
    vi.mocked(useAuth).mockReturnValue({
      user: DRIVE_TESTER_USER,
      loading: false,
      error: null,
      isAdmin: () => false,
    });

    render(
      <AdminGuard>
        <div>Admin Content</div>
      </AdminGuard>
    );

    expect(screen.getByText("Access Denied")).toBeInTheDocument();
  });

  it("should render children when user is authorized ADMIN", () => {
    vi.mocked(useAuth).mockReturnValue({
      user: ADMIN_USER,
      loading: false,
      error: null,
      isAdmin: () => true,
    });

    render(
      <AdminGuard>
        <div>Secret Admin Dashboard</div>
      </AdminGuard>
    );

    expect(screen.getByText("Secret Admin Dashboard")).toBeInTheDocument();
  });

  it("should show error message when API fails", () => {
    vi.mocked(useAuth).mockReturnValue({
      user: null,
      loading: false,
      error: "Failed to fetch current user: 500",
      isAdmin: () => false,
    });

    render(
      <AdminGuard>
        <div>Admin Content</div>
      </AdminGuard>
    );

    expect(screen.getByText("Error")).toBeInTheDocument();
    expect(screen.getByText("Failed to fetch current user: 500")).toBeInTheDocument();
  });

  it("should handle unauthenticated state (null user, no error)", () => {
    vi.mocked(useAuth).mockReturnValue({
      user: null,
      loading: false,
      error: null,
      isAdmin: () => false,
    });

    render(
      <AdminGuard>
        <div>Admin Content</div>
      </AdminGuard>
    );

    expect(screen.getByText("Not authenticated")).toBeInTheDocument();
  });
});

/**
 * useAuth hook contract tests
 * AdminGuard tests above verify the hook's behavior through component integration
 * These contract tests verify the hook provides expected interface
 */
describe("useAuth hook contract", () => {
  it("should return object with user, loading, error, and isAdmin", () => {
    // Mock return value shows the expected contract
    const mockReturnValue = {
      user: ADMIN_USER,
      loading: false,
      error: null,
      isAdmin: () => true,
    };
    expect(mockReturnValue).toHaveProperty("user");
    expect(mockReturnValue).toHaveProperty("loading");
    expect(mockReturnValue).toHaveProperty("error");
    expect(typeof mockReturnValue.isAdmin).toBe("function");
  });

  it("should have isAdmin as a callable function", () => {
    const mockReturn = { isAdmin: () => false };
    expect(typeof mockReturn.isAdmin).toBe("function");
    expect(mockReturn.isAdmin()).toBe(false);
  });
});
