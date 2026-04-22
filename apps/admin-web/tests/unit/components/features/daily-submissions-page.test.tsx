import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { DailySubmissionsPage } from "@/components/features/daily-submissions-page";
import { submissions } from "@/lib/mock/data";

const mockUseAdminSubmissions = vi.fn();
const mockMutate = vi.fn();
vi.mock("@/lib/hooks/use-admin-submissions", () => ({
  useAdminSubmissions: (...args: unknown[]) => mockUseAdminSubmissions(...args),
}));

vi.mock("@/lib/hooks/use-submissions-export", () => ({
  useSubmissionsExport: () => ({
    mutate: mockMutate,
    isPending: false,
    isError: false,
    error: null,
  }),
}));

const defaultHookResult = {
  items: submissions,
  pagination: { page: 1, pageSize: 20, total: submissions.length, totalPages: 1 },
  isLoading: false,
  isError: false,
  error: null,
  isFallback: false,
};

describe("DailySubmissionsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseAdminSubmissions.mockReturnValue(defaultHookResult);
  });

  it("passes filter params to the hook from URL search params", () => {
    globalThis.__mockPathname = "/daily-submissions";
    globalThis.__mockSearchParams = "submission_status=COMPLETED&shift=AM";

    render(<DailySubmissionsPage />);

    expect(mockUseAdminSubmissions).toHaveBeenCalledWith(
      expect.objectContaining({ status: "COMPLETED", shift: "AM" }),
    );
  });

  it("renders hook items in the table", () => {
    globalThis.__mockPathname = "/daily-submissions";
    globalThis.__mockSearchParams = "";
    const name = submissions[0].testerName;

    render(<DailySubmissionsPage />);

    expect(screen.getByText(name)).toBeInTheDocument();
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

  it("shows an empty state when hook returns no items", () => {
    globalThis.__mockPathname = "/daily-submissions";
    globalThis.__mockSearchParams = "";
    mockUseAdminSubmissions.mockReturnValue({
      ...defaultHookResult,
      items: [],
      pagination: { page: 1, pageSize: 20, total: 0, totalPages: 0 },
    });

    render(<DailySubmissionsPage />);

    expect(screen.getByText("No daily submissions found")).toBeInTheDocument();
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
  });

  it("exports CSV using only backend-supported active filters", () => {
    globalThis.__mockPathname = "/daily-submissions";
    globalThis.__mockSearchParams = [
      "work_date=2026-04-22",
      "submission_status=COMPLETED",
      "shift=AM",
      "file_submission_pending=true",
      "workorder_code=WO-NE-401",
      "tester=alex@example.com",
    ].join("&");

    render(<DailySubmissionsPage />);

    fireEvent.click(screen.getByRole("button", { name: "Export CSV" }));

    expect(mockMutate).toHaveBeenCalledWith({
      work_date: "2026-04-22",
      status: "COMPLETED",
      shift: "AM",
      file_submission_pending: true,
    });
  });
});
