import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { UsersPage } from "@/components/features/users-page";
import { users } from "@/lib/mock/data";

const mockUseAdminUsers = vi.fn();
vi.mock("@/lib/hooks/use-admin-users", () => ({
  useAdminUsers: (...args: unknown[]) => mockUseAdminUsers(...args),
}));

vi.mock("@/lib/hooks/use-suspend-user", () => ({
  useSuspendUser: vi.fn(() => ({ mutate: vi.fn(), isPending: false, isError: false, error: null })),
}));

const defaultHookResult = {
  items: users,
  pagination: { page: 1, pageSize: 20, total: users.length, totalPages: 1 },
  isLoading: false,
  isError: false,
  error: null,
  isFallback: false,
};

describe("UsersPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseAdminUsers.mockReturnValue(defaultHookResult);
  });

  it("passes filter params to the hook from URL search params", () => {
    globalThis.__mockPathname = "/users";
    globalThis.__mockSearchParams = "role=ADMIN&account_status=APPROVED";

    render(<UsersPage />);

    expect(mockUseAdminUsers).toHaveBeenCalledWith(
      expect.objectContaining({ requested_role: "ADMIN", account_status: "APPROVED" }),
    );
  });

  it("renders hook items in the table", () => {
    globalThis.__mockPathname = "/users";
    globalThis.__mockSearchParams = "";

    render(<UsersPage />);

    expect(screen.getByText(users[0].fullName)).toBeInTheDocument();
  });

  it("updates the URL when a search filter changes", () => {
    globalThis.__mockPathname = "/users";
    globalThis.__mockSearchParams = "page=2&page_size=2";

    render(<UsersPage />);

    fireEvent.change(screen.getByLabelText("Name or Email"), { target: { value: "jane" } });

    expect(globalThis.__mockRouterReplace).toHaveBeenCalledWith("/users?query=jane&page_size=2");
  });
});
