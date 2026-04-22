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