import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { DailySubmissionsPage } from "@/components/features/daily-submissions-page";

describe("DailySubmissionsPage", () => {
  it("filters the table from URL search params on first render", () => {
    globalThis.__mockPathname = "/daily-submissions";
    globalThis.__mockSearchParams = "region=NE_UP&submission_status=COMPLETED";

    render(<DailySubmissionsPage />);

    expect(screen.getByText("Jane Doe")).toBeInTheDocument();
    expect(screen.queryByText("Priya Shah")).not.toBeInTheDocument();
    expect(screen.getByText(/1 matching submissions/i)).toBeInTheDocument();
  });

  it("updates the URL when a filter changes and resets the page", () => {
    globalThis.__mockPathname = "/daily-submissions";
    globalThis.__mockSearchParams = "page=3&page_size=2";

    render(<DailySubmissionsPage />);

    fireEvent.change(screen.getByLabelText("Region"), {
      target: { value: "NE_UP" },
    });

    expect(globalThis.__mockRouterReplace).toHaveBeenCalledWith(
      "/daily-submissions?region=NE_UP&page_size=2",
    );
  });

  it("preserves filters when paginating", () => {
    globalThis.__mockPathname = "/daily-submissions";
    globalThis.__mockSearchParams = "region=NE_UP&page_size=2";

    render(<DailySubmissionsPage />);

    fireEvent.click(screen.getByRole("button", { name: "Next" }));

    expect(globalThis.__mockRouterReplace).toHaveBeenCalledWith(
      "/daily-submissions?region=NE_UP&page=2&page_size=2",
    );
  });

  it("shows an empty state when no rows match the active filters", () => {
    globalThis.__mockPathname = "/daily-submissions";
    globalThis.__mockSearchParams = "tester=no-match";

    render(<DailySubmissionsPage />);

    expect(screen.getByText("No daily submissions found")).toBeInTheDocument();
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
  });
});