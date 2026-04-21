import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import DashboardRoute from "@/app/dashboard/page";
import DailySubmissionsRoute from "@/app/daily-submissions/page";
import DailySubmissionDetailRoute from "@/app/daily-submissions/[submissionId]/page";
import NoSubmissionYetRoute from "@/app/no-submission-yet/page";
import ReportsRoute from "@/app/reports/page";
import PendingUsersRoute from "@/app/users/pending/page";
import UsersRoute from "@/app/users/page";
import WorkorderDetailRoute from "@/app/workorders/[workorderId]/page";
import WorkordersRoute from "@/app/workorders/page";

describe("route smoke tests", () => {
  it("renders the dashboard route", () => {
    render(<DashboardRoute />);

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