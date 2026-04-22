import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { PendingUsersPage } from "@/components/features/pending-users-page";
import { pendingUsers } from "@/lib/mock/data";

const defaultHookResult = {
  items: pendingUsers,
  count: pendingUsers.length,
  isLoading: false,
  isError: false,
  error: null,
};

const mockApproveMutation = { mutate: vi.fn(), isPending: false, isError: false, error: null, isPending_: false };
const mockRejectMutation = { mutate: vi.fn(), isPending: false, isError: false, error: null, isPending_: false };

vi.mock("@/lib/hooks/use-pending-users", () => ({
  usePendingUsers: vi.fn(() => defaultHookResult),
}));

vi.mock("@/lib/hooks/use-approve-user", () => ({
  useApproveUser: vi.fn(() => mockApproveMutation),
}));

vi.mock("@/lib/hooks/use-reject-user", () => ({
  useRejectUser: vi.fn(() => mockRejectMutation),
}));

import { usePendingUsers } from "@/lib/hooks/use-pending-users";
const mockUsePendingUsers = vi.mocked(usePendingUsers);

describe("PendingUsersPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUsePendingUsers.mockReturnValue(defaultHookResult as unknown as ReturnType<typeof usePendingUsers>);
  });

  it("renders all pending user names", () => {
    render(<PendingUsersPage />);

    expect(screen.getByText("Leah Ford")).toBeInTheDocument();
    expect(screen.getByText("Mohammed Khan")).toBeInTheDocument();
    expect(screen.getByText("Iris Chen")).toBeInTheDocument();
  });

  it("renders Approve and Reject buttons for each user", () => {
    render(<PendingUsersPage />);

    const approveButtons = screen.getAllByRole("button", { name: /approve/i });
    const rejectButtons = screen.getAllByRole("button", { name: /reject/i });

    expect(approveButtons.length).toBe(pendingUsers.length);
    expect(rejectButtons.length).toBe(pendingUsers.length);
  });

  it("opens the confirmation dialog when Approve is clicked", () => {
    render(<PendingUsersPage />);

    fireEvent.click(screen.getAllByRole("button", { name: /approve/i })[0]);

    expect(screen.getByText("Approve User")).toBeInTheDocument();
    // Description contains the user's name
    expect(screen.getByText(/Approve Leah Ford/)).toBeInTheDocument();
  });

  it("opens the confirmation dialog when Reject is clicked", () => {
    render(<PendingUsersPage />);

    fireEvent.click(screen.getAllByRole("button", { name: /reject/i })[0]);

    expect(screen.getByText("Reject User")).toBeInTheDocument();
  });

  it("shows loading spinner while data is loading", () => {
    mockUsePendingUsers.mockReturnValueOnce({
      ...defaultHookResult,
      items: [],
      isLoading: true,
    } as unknown as ReturnType<typeof usePendingUsers>);

    render(<PendingUsersPage />);

    // The loading spinner has animate-spin class
    const spinner = document.querySelector(".animate-spin");
    expect(spinner).not.toBeNull();
  });

  it("shows error alert when fetch fails (no fallback)", () => {
    mockUsePendingUsers.mockReturnValueOnce({
      items: [],
      count: 0,
      isLoading: false,
      isError: true,
      error: new Error("Failed to fetch"),
    } as unknown as ReturnType<typeof usePendingUsers>);

    render(<PendingUsersPage />);

    expect(screen.getByText(/error loading pending users/i)).toBeInTheDocument();
  });
});
