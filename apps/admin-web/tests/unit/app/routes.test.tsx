import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import DashboardRoute from "@/app/dashboard/page";
import DailySubmissionsRoute from "@/app/daily-submissions/page";
import DailySubmissionDetailRoute from "@/app/daily-submissions/[submissionId]/page";
import NoSubmissionYetRoute from "@/app/no-submission-yet/page";
import ReportsRoute from "@/app/reports/page";
import PendingUsersRoute from "@/app/users/pending/page";
import UsersRoute from "@/app/users/page";
import WorkorderDetailRoute from "@/app/workorders/[workorderId]/page";
import WorkordersRoute from "@/app/workorders/page";

vi.mock("@/lib/hooks/use-dashboard-summary", () => ({
  useDashboardSummary: vi.fn(() => ({
    data: {
      approved_drive_testers: 12,
      ongoing_submissions: 5,
      completed_submissions: 41,
      no_submission_yet: 7,
      active_workorders: 18,
      completed_workorders: 3,
      reference_date: "2026-04-20",
    },
    isLoading: false,
    isError: false,
    error: null,
    status: "success",
    isFallback: false,
  })),
}));

vi.mock("@/lib/hooks/use-admin-submissions", () => ({
  useAdminSubmissions: vi.fn(() => ({ items: [], pagination: { page: 1, pageSize: 20, total: 0, totalPages: 0 }, isLoading: false, isError: false, error: null, isFallback: false })),
}));

vi.mock("@/lib/hooks/use-admin-workorders", () => ({
  useAdminWorkorders: vi.fn(() => ({ items: [], pagination: { page: 1, pageSize: 20, total: 0, totalPages: 0 }, isLoading: false, isError: false, error: null, isFallback: false })),
}));

vi.mock("@/lib/hooks/use-admin-users", () => ({
  useAdminUsers: vi.fn(() => ({ items: [], pagination: { page: 1, pageSize: 20, total: 0, totalPages: 0 }, isLoading: false, isError: false, error: null, isFallback: false })),
}));

vi.mock("@/lib/hooks/use-pending-users", () => ({
  usePendingUsers: vi.fn(() => ({ items: [], count: 0, isLoading: false, isError: false, error: null, isFallback: false })),
}));

vi.mock("@/lib/hooks/use-no-submission-yet", () => ({
  useNoSubmissionYet: vi.fn(() => ({ items: [], pagination: { page: 1, pageSize: 20, total: 0, totalPages: 0 }, isLoading: false, isError: false, error: null, isFallback: false })),
}));

vi.mock("@/lib/hooks/use-admin-submission", () => ({
  useAdminSubmission: vi.fn((id: string) => {
    const sub1 = { id: "sub-1", testerName: "Priya Shah", workorderCode: "WO-SF-118", region: "SOUTH_FLORIDA", shift: "PM", ticketNumber: "TKT-9031", completedGrids: 27, skippedGrids: 2, forceTestedGrids: 4, status: "CHECKED_OUT", workorderStatus: "ACTIVE", fileState: "FILE_PENDING", startedAt: "2026-04-20T08:12:00Z", endedAt: "2026-04-20T17:41:00Z", updatedAt: "2026-04-20T17:41:00Z", fileSubmissionPending: true, workDate: "2026-04-20", testerEmail: "priya@mltech.com" };
    const sub2 = { id: "sub-2", testerName: "Jane Doe", workorderCode: "WO-NE-401", region: "NE_UP", shift: "AM", ticketNumber: "TKT-8712", completedGrids: 38, skippedGrids: 1, forceTestedGrids: 3, status: "COMPLETED", workorderStatus: "ACTIVE", fileState: "ATTACHED", startedAt: "2026-04-20T07:48:00Z", endedAt: "2026-04-20T16:55:00Z", updatedAt: "2026-04-20T16:55:00Z", fileSubmissionPending: false, workDate: "2026-04-20", testerEmail: "jane@mltech.com" };
    const found = id === "sub-1" ? sub1 : id === "sub-2" ? sub2 : sub1;
    return { submission: found, isLoading: false, isError: false, error: null, isFallback: false };
  }),
}));

vi.mock("@/lib/hooks/use-submission-audit", () => ({
  useSubmissionAudit: vi.fn(() => ({ items: [], count: 0, isLoading: false, isError: false, error: null })),
}));

vi.mock("@/lib/hooks/use-submission-attachment-history", () => ({
  useSubmissionAttachmentHistory: vi.fn(() => ({ items: [], count: 0, isLoading: false, isError: false, error: null })),
}));

vi.mock("@/lib/hooks/use-edit-submission", () => ({
  useEditSubmission: vi.fn(() => ({ mutate: vi.fn(), isPending: false, isError: false, error: null })),
}));

vi.mock("@/lib/hooks/use-reopen-submission", () => ({
  useReopenSubmission: vi.fn(() => ({ mutate: vi.fn(), isPending: false, isError: false, error: null })),
}));

vi.mock("@/lib/hooks/use-attachment-download", () => ({
  useAttachmentDownload: vi.fn(() => ({ mutate: vi.fn(), isPending: false, isError: false, error: null })),
}));

vi.mock("@/lib/hooks/use-admin-workorder", () => ({
  useAdminWorkorder: vi.fn(() => ({
    workorder: { id: "wo-1", workorderCode: "WO-NE-401", region: "NE_UP", totalGrids: 145, completedGrids: 91, skippedGrids: 8, remainingGrids: 46, progressPercent: 68, status: "ACTIVE", createdAt: "2026-04-16 08:20 AM", updatedAt: "2026-04-20 05:41 PM", submissions: [] },
    isLoading: false, isError: false, error: null, isFallback: false,
  })),
}));

vi.mock("@/lib/hooks/use-edit-workorder", () => ({
  useEditWorkorder: vi.fn(() => ({ mutate: vi.fn(), isPending: false, isError: false, error: null })),
}));

vi.mock("@/lib/hooks/use-suspend-user", () => ({
  useSuspendUser: vi.fn(() => ({ mutate: vi.fn(), isPending: false, isError: false, error: null })),
}));

vi.mock("@/lib/hooks/use-approve-user", () => ({
  useApproveUser: vi.fn(() => ({ mutate: vi.fn(), isPending: false, isError: false, error: null })),
}));

vi.mock("@/lib/hooks/use-reject-user", () => ({
  useRejectUser: vi.fn(() => ({ mutate: vi.fn(), isPending: false, isError: false, error: null })),
}));

vi.mock("@/lib/hooks/use-submissions-export", () => ({
  useSubmissionsExport: vi.fn(() => ({ mutate: vi.fn(), isPending: false, isError: false, error: null })),
}));

describe("route smoke tests", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the dashboard route", () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    render(
      <QueryClientProvider client={queryClient}>
        <DashboardRoute />
      </QueryClientProvider>
    );

    expect(screen.getByRole("heading", { name: "Operations Summary" })).toBeInTheDocument();
  });

  it("renders the daily submissions route", () => {
    render(<DailySubmissionsRoute />);

    expect(screen.getByRole("heading", { name: "Daily Submissions" })).toBeInTheDocument();
  });

  it("renders the daily submission detail route with async params", async () => {
    const page = await DailySubmissionDetailRoute({ params: Promise.resolve({ submissionId: "sub-1" }) });

    render(page);

    expect(screen.getByRole("heading", { name: "Priya Shah / WO-SF-118" })).toBeInTheDocument();
  });

  it("renders the workorders route", () => {
    render(<WorkordersRoute />);

    expect(screen.getByRole("heading", { name: "Workorders" })).toBeInTheDocument();
  });

  it("renders the workorder detail route with async params", async () => {
    const page = await WorkorderDetailRoute({ params: Promise.resolve({ workorderId: "wo-1" }) });

    render(page);

    expect(screen.getByRole("heading", { name: "WO-NE-401" })).toBeInTheDocument();
  });

  it("renders the users routes", () => {
    render(<UsersRoute />);
    expect(screen.getByRole("heading", { name: "Users" })).toBeInTheDocument();

    render(<PendingUsersRoute />);
    expect(screen.getByRole("heading", { name: "Pending Users" })).toBeInTheDocument();
  });

  it("renders no-submission-yet and reports routes", () => {
    render(<NoSubmissionYetRoute />);
    expect(screen.getByRole("heading", { name: "No Submission Yet" })).toBeInTheDocument();

    render(<ReportsRoute />);
    expect(screen.getByRole("heading", { name: "Reports" })).toBeInTheDocument();
  });
});