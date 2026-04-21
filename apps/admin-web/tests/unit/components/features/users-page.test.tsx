import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { UsersPage } from "@/components/features/users-page";

describe("UsersPage", () => {
  it("filters the table from URL search params on first render", () => {
    globalThis.__mockPathname = "/users";
    globalThis.__mockSearchParams = "role=ADMIN&account_status=APPROVED";

    render(<UsersPage />);

    expect(screen.getByText("Asha Kumar")).toBeInTheDocument();
    expect(screen.queryByText("Jane Doe")).not.toBeInTheDocument();
    expect(screen.getByText(/1 matching users/i)).toBeInTheDocument();
  });

  it("updates the URL when a search filter changes", () => {
    globalThis.__mockPathname = "/users";
    globalThis.__mockSearchParams = "page=2&page_size=2";

    render(<UsersPage />);

    fireEvent.change(screen.getByLabelText("Name or Email"), { target: { value: "jane" } });

    expect(globalThis.__mockRouterReplace).toHaveBeenCalledWith("/users?query=jane&page_size=2");
  });
});