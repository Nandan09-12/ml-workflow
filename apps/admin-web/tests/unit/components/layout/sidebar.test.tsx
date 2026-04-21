import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Sidebar } from "@/components/layout/sidebar";

describe("Sidebar", () => {
  it("marks the exact top-level route as active", () => {
    globalThis.__mockPathname = "/dashboard";

    render(<Sidebar />);

    expect(screen.getByRole("link", { name: "Dashboard" })).toHaveClass("bg-brand-soft");
  });

  it("marks only the pending users entry as active for the nested pending route", () => {
    globalThis.__mockPathname = "/users/pending";

    render(<Sidebar />);

    expect(screen.getByRole("link", { name: "Pending Users" })).toHaveClass("bg-brand-soft");
    expect(screen.getByRole("link", { name: "Users" })).not.toHaveClass("bg-brand-soft");
  });

  it("marks daily submissions active for submission detail routes", () => {
    globalThis.__mockPathname = "/daily-submissions/sub-1";

    render(<Sidebar />);

    expect(screen.getByRole("link", { name: "Daily Submissions" })).toHaveClass("bg-brand-soft");
  });
});