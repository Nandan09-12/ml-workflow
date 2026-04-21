import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Topbar } from "@/components/layout/topbar";

describe("Topbar", () => {
  it("renders the pending users title for the more specific nested route", () => {
    globalThis.__mockPathname = "/users/pending";

    render(<Topbar />);

    expect(screen.getByRole("heading", { name: "Pending Users" })).toBeInTheDocument();
  });

  it("falls back to the parent section title for nested daily submission detail routes", () => {
    globalThis.__mockPathname = "/daily-submissions/sub-1";

    render(<Topbar />);

    expect(screen.getByRole("heading", { name: "Daily Submissions" })).toBeInTheDocument();
  });

  it("falls back to the default admin console title for unknown routes", () => {
    globalThis.__mockPathname = "/unknown";

    render(<Topbar />);

    expect(screen.getByRole("heading", { name: "Admin Console" })).toBeInTheDocument();
  });
});