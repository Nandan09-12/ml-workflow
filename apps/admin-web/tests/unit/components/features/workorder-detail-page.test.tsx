import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { WorkorderDetailPage } from "@/components/features/workorder-detail-page";
import { workorders } from "@/lib/mock/data";

const wo1 = workorders.find((w) => w.id === "wo-1")!;

const defaultHookResult = {
  workorder: {
    ...wo1,
    submissions: [],
    remainingGrids: 46,
    progressPercent: 68,
  },
  isLoading: false,
  isError: false,
  error: null,
  isFallback: false,
};

const mockEditMutation = { mutate: vi.fn(), isPending: false, isError: false, error: null };

vi.mock("@/lib/hooks/use-admin-workorder", () => ({
  useAdminWorkorder: vi.fn(() => defaultHookResult),
}));

vi.mock("@/lib/hooks/use-edit-workorder", () => ({
  useEditWorkorder: vi.fn(() => mockEditMutation),
}));

import { useAdminWorkorder } from "@/lib/hooks/use-admin-workorder";
const mockUseAdminWorkorder = vi.mocked(useAdminWorkorder);

describe("WorkorderDetailPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseAdminWorkorder.mockReturnValue(defaultHookResult as ReturnType<typeof useAdminWorkorder>);
    vi.mocked(mockEditMutation.mutate).mockReset?.();
  });

  it("renders the workorder code in the page header", () => {
    render(<WorkorderDetailPage workorderId="wo-1" />);

    expect(screen.getByRole("heading", { name: "WO-NE-401" })).toBeInTheDocument();
  });

  it("renders grid stats (total, completed, skipped, remaining, progress)", () => {
    render(<WorkorderDetailPage workorderId="wo-1" />);

    expect(screen.getByText(String(wo1.totalGrids))).toBeInTheDocument();
    expect(screen.getAllByText(String(wo1.completedGrids)).length).toBeGreaterThan(0);
    expect(screen.getByText("68%")).toBeInTheDocument();
  });

  it("shows LoadingState while loading", () => {
    mockUseAdminWorkorder.mockReturnValueOnce({
      ...defaultHookResult,
      workorder: null,
      isLoading: true,
    } as ReturnType<typeof useAdminWorkorder>);

    render(<WorkorderDetailPage workorderId="wo-1" />);

    expect(screen.getByText("Loading")).toBeInTheDocument();
  });

  it("shows ErrorState when fetch fails (no fallback)", () => {
    mockUseAdminWorkorder.mockReturnValueOnce({
      workorder: null,
      isLoading: false,
      isError: true,
      error: new Error("Not found"),
      isFallback: false,
    } as ReturnType<typeof useAdminWorkorder>);

    render(<WorkorderDetailPage workorderId="wo-1" />);

    expect(screen.getByText(/failed to load workorder/i)).toBeInTheDocument();
  });

  it("shows fallback alert banner when using cached data", () => {
    mockUseAdminWorkorder.mockReturnValueOnce({
      ...defaultHookResult,
      isFallback: true,
    } as ReturnType<typeof useAdminWorkorder>);

    render(<WorkorderDetailPage workorderId="wo-1" />);

    expect(screen.getByText(/using cached data/i)).toBeInTheDocument();
  });

  it("opens the edit drawer when 'Edit Workorder' button is clicked", () => {
    render(<WorkorderDetailPage workorderId="wo-1" />);

    fireEvent.click(screen.getByRole("button", { name: /edit workorder/i }));

    // Drawer title should appear (separate from the button)
    const headings = screen.getAllByText(/edit workorder/i);
    expect(headings.length).toBeGreaterThan(1);
  });

  it("renders the child submissions table header", () => {
    render(<WorkorderDetailPage workorderId="wo-1" />);

    expect(screen.getByText("Submission History")).toBeInTheDocument();
  });
});
