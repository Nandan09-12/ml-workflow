import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { Topbar } from "@/components/layout/topbar";

const mockUseAuth = vi.fn();

vi.mock("@/lib/hooks/useAuth", () => ({
  useAuth: () => mockUseAuth(),
}));

describe("Topbar", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseAuth.mockReturnValue({
      user: {
        id: "user-1",
        email: "admin@example.com",
        full_name: "Admin User",
        approved_role: "ADMIN",
        account_status: "APPROVED",
      },
      loading: false,
      error: null,
      isAdmin: () => true,
    });
  });

  it("renders the pending users title for the more specific nested route", () => {
    globalThis.__mockPathname = "/users/pending";

    render(<Topbar />);

    expect(screen.getByText("Pending Users")).toBeInTheDocument();
  });

  it("falls back to the parent section title for nested daily submission detail routes", () => {
    globalThis.__mockPathname = "/daily-submissions/sub-1";

    render(<Topbar />);

    expect(screen.getByText("Daily Submissions")).toBeInTheDocument();
  });

  it("falls back to the default admin console title for unknown routes", () => {
    globalThis.__mockPathname = "/unknown";

    render(<Topbar />);

    expect(screen.getByText("Admin Console")).toBeInTheDocument();
  });

  it("renders the current admin from auth state instead of mock data", () => {
    render(<Topbar />);

    expect(screen.getByText("Admin User")).toBeInTheDocument();
    expect(screen.getByText("ADMIN")).toBeInTheDocument();
  });

  it("routes workorder-style search queries to the workorders page", () => {
    render(<Topbar />);

    fireEvent.change(screen.getByRole("textbox", { name: "Search by workorder code" }), {
      target: { value: "WO-NE-401" },
    });
    fireEvent.submit(screen.getByRole("search"));

    expect(globalThis.__mockRouterPush).toHaveBeenCalledWith("/workorders?workorder_code=WO-NE-401");
  });

  it("does not navigate when the quick-jump search is empty", () => {
    render(<Topbar />);

    fireEvent.submit(screen.getByRole("search"));

    expect(globalThis.__mockRouterPush).not.toHaveBeenCalled();
  });
});