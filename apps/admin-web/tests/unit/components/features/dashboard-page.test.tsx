import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import { DashboardPage } from "@/components/features/dashboard-page";
import { useDashboardSummary } from "@/lib/hooks/use-dashboard-summary";
import { useAdminWorkorders } from "@/lib/hooks/use-admin-workorders";
import { useAdminSubmissions } from "@/lib/hooks/use-admin-submissions";
import { usePendingUsers } from "@/lib/hooks/use-pending-users";

vi.mock("@/lib/hooks/use-dashboard-summary", () => ({
  useDashboardSummary: vi.fn(),
}));

vi.mock("@/lib/hooks/use-admin-workorders", () => ({
  useAdminWorkorders: vi.fn(),
}));

vi.mock("@/lib/hooks/use-admin-submissions", () => ({
  useAdminSubmissions: vi.fn(),
}));

vi.mock("@/lib/hooks/use-pending-users", () => ({
  usePendingUsers: vi.fn(),
}));

const mockUseDashboardSummary = vi.mocked(useDashboardSummary);
const mockUseAdminWorkorders = vi.mocked(useAdminWorkorders);
const mockUseAdminSubmissions = vi.mocked(useAdminSubmissions);
const mockUsePendingUsers = vi.mocked(usePendingUsers);

const mockDashboardData = {
  approved_drive_testers: 12,
  ongoing_submissions: 5,
  completed_submissions: 41,
  no_submission_yet: 7,
  active_workorders: 18,
  completed_workorders: 3,
  reference_date: "2026-04-20",
};

function renderWithQueryClient(component: React.ReactNode) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      {component}
    </QueryClientProvider>
  );
}

describe("DashboardPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseAdminWorkorders.mockReturnValue({
      items: [],
      pagination: { page: 1, pageSize: 4, total: 0, totalPages: 0 },
      isLoading: false,
      isError: false,
      error: null,
    } as never);
    mockUseAdminSubmissions.mockReturnValue({
      items: [],
      pagination: { page: 1, pageSize: 5, total: 0, totalPages: 0 },
      isLoading: false,
      isError: false,
      error: null,
    } as never);
    mockUsePendingUsers.mockReturnValue({
      items: [],
      count: 0,
      isLoading: false,
      isError: false,
      error: null,
    } as never);
  });

  it("displays loading spinner while fetching dashboard data", async () => {
    mockUseDashboardSummary.mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      error: null,
      status: "pending",
    } as never);

    renderWithQueryClient(<DashboardPage />);

    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("displays live data when successfully fetched", async () => {
    mockUseDashboardSummary.mockReturnValue({
      data: mockDashboardData,
      isLoading: false,
      isError: false,
      error: null,
      status: "success",
    } as never);

    renderWithQueryClient(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText(/Operations Summary/i)).toBeInTheDocument();
    });

    // Verify metrics are rendered with live data - use more specific queries
    expect(screen.getByText("Active Workorders")).toBeInTheDocument();
    expect(screen.getByText("18")).toBeInTheDocument(); // Active workorders count
    expect(screen.getByText("Completed Submissions")).toBeInTheDocument();
    expect(screen.getByText("41")).toBeInTheDocument(); // Completed submissions
  });

  it("displays error message for 4xx client error", async () => {
    const error = new Error("Forbidden");
    mockUseDashboardSummary.mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      error: error as never,
      status: "error",
    } as never);

    renderWithQueryClient(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText(/error loading dashboard/i)).toBeInTheDocument();
      expect(screen.getByText(/Forbidden/)).toBeInTheDocument();
    });

  });

  it("passes work_date filter to hook when date input changes", async () => {
    mockUseDashboardSummary.mockReturnValue({
      data: mockDashboardData,
      isLoading: false,
      isError: false,
      error: null,
      status: "success",
    } as never);

    const { rerender } = renderWithQueryClient(<DashboardPage />);

    // Simulate changing the date filter
    const dateInput = screen.getByTestId("work-date-filter") as HTMLInputElement;
    fireEvent.change(dateInput, { target: { value: "2026-04-19" } });

    await waitFor(() => {
      expect(mockUseDashboardSummary).toHaveBeenCalledWith(
        expect.objectContaining({
          work_date: "2026-04-19",
        })
      );
    });
  });

  it("shows no_submission_yet count from live data in Admin Queue panel", async () => {
    mockUseDashboardSummary.mockReturnValue({
      data: {
        ...mockDashboardData,
        no_submission_yet: 13,
      },
      isLoading: false,
      isError: false,
      error: null,
      status: "success",
    } as never);

    renderWithQueryClient(<DashboardPage />);

    await waitFor(() => {
      // The "No Submission Yet" badge in the Admin Queue should show live count
      const noSubBadge = screen.getAllByText("13");
      expect(noSubBadge.length).toBeGreaterThanOrEqual(1);
    });
  });

  it("refetches data when filters change", async () => {
    mockUseDashboardSummary.mockReturnValue({
      data: mockDashboardData,
      isLoading: false,
      isError: false,
      error: null,
      status: "success",
    } as never);

    const { rerender } = renderWithQueryClient(<DashboardPage />);

    expect(mockUseDashboardSummary).toHaveBeenCalledTimes(1);

    // Change filter
    const dateInput = screen.getByTestId("work-date-filter") as HTMLInputElement;
    fireEvent.change(dateInput, { target: { value: "2026-04-18" } });

    await waitFor(() => {
      expect(mockUseDashboardSummary).toHaveBeenCalledTimes(2);
    });
  });

  it("applies region filter to workorders and submissions widgets", async () => {
    mockUseDashboardSummary.mockReturnValue({
      data: mockDashboardData,
      isLoading: false,
      isError: false,
      error: null,
      status: "success",
    } as never);

    renderWithQueryClient(<DashboardPage />);

    fireEvent.change(screen.getByTestId("region-filter"), {
      target: { value: "NE_UP" },
    });

    await waitFor(() => {
      expect(mockUseAdminWorkorders).toHaveBeenLastCalledWith(
        expect.objectContaining({ region: "NE_UP" })
      );
      expect(mockUseAdminSubmissions).toHaveBeenCalledWith(
        expect.objectContaining({ region: "NE_UP" })
      );
      expect(screen.getByText(/Region filter applied/i)).toBeInTheDocument();
    });
  });

  it("renders metric cards with live API data", async () => {
    mockUseDashboardSummary.mockReturnValue({
      data: {
        approved_drive_testers: 15,
        ongoing_submissions: 8,
        completed_submissions: 50,
        no_submission_yet: 3,
        active_workorders: 22,
        completed_workorders: 6,
        reference_date: "2026-04-20",
      },
      isLoading: false,
      isError: false,
      error: null,
      status: "success",
    } as never);

    renderWithQueryClient(<DashboardPage />);

    await waitFor(() => {
      // Verify live data is displayed with labels
      expect(screen.getByText("Active Workorders")).toBeInTheDocument();
      expect(screen.getByText("Completed Submissions")).toBeInTheDocument();
      expect(screen.getByText("22")).toBeInTheDocument(); // Active workorders
      expect(screen.getByText("50")).toBeInTheDocument(); // Completed submissions
    });
  });

  it("shows Page Header with correct operational summary text", async () => {
    mockUseDashboardSummary.mockReturnValue({
      data: mockDashboardData,
      isLoading: false,
      isError: false,
      error: null,
      status: "success",
    } as never);

    renderWithQueryClient(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("Operations Summary")).toBeInTheDocument();
      expect(screen.getByText(/Dense operational view/i)).toBeInTheDocument();
    });
  });
});
