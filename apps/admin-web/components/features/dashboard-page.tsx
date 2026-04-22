"use client";

import { useState } from "react";
import Link from "next/link";
import { Alert } from "@/components/ui/alert";
import { DataTable } from "@/components/ui/data-table";
import { MetricCard } from "@/components/ui/metric-card";
import { PageHeader } from "@/components/ui/page-header";
import { Panel } from "@/components/ui/panel";
import { ProgressBar } from "@/components/ui/progress-bar";
import { StatusBadge } from "@/components/ui/status-badge";
import { formatFileState, formatRegion } from "@/lib/format/labels";
import { useAdminSubmissions } from "@/lib/hooks/use-admin-submissions";
import { useAdminWorkorders } from "@/lib/hooks/use-admin-workorders";
import { useDashboardSummary } from "@/lib/hooks/use-dashboard-summary";
import { usePendingUsers } from "@/lib/hooks/use-pending-users";

export function DashboardPage() {
  const [workDate, setWorkDate] = useState(() => new Date().toISOString().split("T")[0]);
  const [dateFrom, setDateFrom] = useState<string | undefined>();
  const [dateTo, setDateTo] = useState<string | undefined>();
  const [region, setRegion] = useState<"ALL" | "NE_UP" | "CENTRAL" | "SOUTH_FLORIDA">("ALL");

  const regionFilter = region === "ALL" ? undefined : region;

  const { data: dashboardData, isLoading, isError, error } = useDashboardSummary({
    work_date: workDate,
    date_from: dateFrom,
    date_to: dateTo,
  });

  const { items: recentWorkorders } = useAdminWorkorders({ page_size: 4, region: regionFilter });
  const { items: recentSubmissions } = useAdminSubmissions({ page_size: 5, region: regionFilter });
  const { count: pendingUsersCount } = usePendingUsers();
  const { pagination: filePendingPagination } = useAdminSubmissions({
    file_submission_pending: true,
    region: regionFilter,
    page_size: 1,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12" role="status">
        <div className="animate-spin rounded-full border-4 border-line border-t-brand h-8 w-8"></div>
      </div>
    );
  }

  if (isError) {
    return (
      <Alert title="Error loading dashboard" tone="danger">
        {error instanceof Error ? error.message : "Failed to load dashboard data"}
      </Alert>
    );
  }

  const activeWorkorders = dashboardData?.active_workorders ?? 0;
  const completedWorkorders = dashboardData?.completed_workorders ?? 0;
  const completedSubmissions = dashboardData?.completed_submissions ?? 0;
  const ongoingSubmissions = dashboardData?.ongoing_submissions ?? 0;
  const noSubmissionYet = dashboardData?.no_submission_yet ?? 0;
  const completionDenominator = completedSubmissions + ongoingSubmissions + noSubmissionYet;

  const liveMetrics = [
    {
      label: "Active Workorders",
      value: activeWorkorders.toString(),
      detail: `${completedWorkorders} completed`,
      tone: "brand" as const,
      href: regionFilter
        ? `/workorders?status=ACTIVE&region=${regionFilter}`
        : "/workorders?status=ACTIVE",
    },
    {
      label: "Completed Submissions",
      value: completedSubmissions.toString(),
      detail:
        completionDenominator > 0
          ? `${Math.round((completedSubmissions / completionDenominator) * 100)}% of daily records`
          : "0% of daily records",
      tone: "success" as const,
      href: regionFilter
        ? `/daily-submissions?submission_status=COMPLETED&region=${regionFilter}`
        : "/daily-submissions?submission_status=COMPLETED",
    },
    {
      label: "Ongoing Submissions",
      value: ongoingSubmissions.toString(),
      detail: "In progress",
      tone: "warning" as const,
      href: regionFilter
        ? `/daily-submissions?submission_status=CHECKED_OUT&region=${regionFilter}`
        : "/daily-submissions?submission_status=CHECKED_OUT",
    },
    {
      label: "No Submission Yet",
      value: noSubmissionYet.toString(),
      detail: "Approved testers only",
      tone: "danger" as const,
      href: "/no-submission-yet",
    },
  ];
  return (
    <div className="space-y-6">
      <PageHeader
        kicker="Today"
        title="Operations Summary"
        subtitle="Dense operational view for workorders, daily submissions, pending approvals, and missing closeout follow-up."
        actions={
          <div className="flex flex-wrap gap-3">
            <label className="grid min-w-40 gap-1 text-xs font-bold uppercase tracking-[0.12em] text-neutral">
              <span>Date</span>
              <input 
                type="date" 
                value={workDate} 
                onChange={(e) => setWorkDate(e.target.value)}
                data-testid="work-date-filter"
                className="rounded-panel border border-line bg-panel px-3 py-2 text-sm font-medium text-ink" 
              />
            </label>
            <label className="grid min-w-40 gap-1 text-xs font-bold uppercase tracking-[0.12em] text-neutral">
              <span>Region</span>
              <select
                value={region}
                onChange={(e) => setRegion(e.target.value as "ALL" | "NE_UP" | "CENTRAL" | "SOUTH_FLORIDA")}
                data-testid="region-filter"
                className="rounded-panel border border-line bg-panel px-3 py-2 text-sm font-medium text-ink"
              >
                <option value="ALL">All regions</option>
                <option value="NE_UP">NE-UP</option>
                <option value="CENTRAL">Central</option>
                <option value="SOUTH_FLORIDA">South/Florida</option>
              </select>
            </label>
          </div>
        }
      />
      {regionFilter ? (
        <Alert title="Region filter applied" tone="info">
          Workorder and submission widgets are filtered to {formatRegion(regionFilter)}.
        </Alert>
      ) : null}
      <div className="grid gap-4 xl:grid-cols-4">
        {liveMetrics.map((metric) => (
          <MetricCard key={metric.label} {...metric} />
        ))}
      </div>
      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <Panel>
          <div className="mb-4 flex items-start justify-between gap-4">
            <div>
              <p className="text-xs font-extrabold uppercase tracking-[0.16em] text-brand">Workorders</p>
              <h2 className="mt-1 text-xl font-semibold text-ink">Progress</h2>
            </div>
            <Link
              className="text-sm font-bold text-brand"
              href={regionFilter ? `/workorders?region=${regionFilter}` : "/workorders"}
            >
              View all
            </Link>
          </div>
          <div className="grid gap-3">
            {recentWorkorders.map((workorder) => (
              <article key={workorder.id} className="rounded-panel border border-line bg-slate-50 p-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <strong className="text-sm font-semibold text-ink">{workorder.workorderCode}</strong>
                    <p className="mt-1 text-sm text-neutral">{formatRegion(workorder.region)}</p>
                  </div>
                  <StatusBadge value={workorder.status} />
                </div>
                <div className="mt-4">
                  <ProgressBar value={workorder.progressPercent} caption={`${workorder.remainingGrids} remaining grids`} />
                </div>
              </article>
            ))}
          </div>
        </Panel>
        <Panel>
          <div className="mb-4">
            <p className="text-xs font-extrabold uppercase tracking-[0.16em] text-brand">Follow-up</p>
            <h2 className="mt-1 text-xl font-semibold text-ink">Admin Queue</h2>
          </div>
          <div className="grid gap-3">
            <Link
              href={
                regionFilter
                  ? `/daily-submissions?file_submission_pending=true&region=${regionFilter}`
                  : "/daily-submissions?file_submission_pending=true"
              }
              className="rounded-panel border border-line bg-slate-50 p-4 transition hover:border-brand"
            >
              <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-brand-soft text-lg font-black text-brand">{filePendingPagination.total}</span>
              <strong className="mt-3 block text-sm font-semibold text-ink">File Pending</strong>
              <p className="mt-1 text-sm text-neutral">Checked-out submissions without an active CSV or XLSX closeout file.</p>
            </Link>
            <Link href="/users/pending" className="rounded-panel border border-line bg-slate-50 p-4 transition hover:border-brand">
              <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-brand-soft text-lg font-black text-brand">{pendingUsersCount}</span>
              <strong className="mt-3 block text-sm font-semibold text-ink">Pending Users</strong>
              <p className="mt-1 text-sm text-neutral">Role requests awaiting admin approval or rejection.</p>
            </Link>
            <Link href="/no-submission-yet" className="rounded-panel border border-line bg-slate-50 p-4 transition hover:border-brand">
              <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-brand-soft text-lg font-black text-brand">{noSubmissionYet}</span>
              <strong className="mt-3 block text-sm font-semibold text-ink">No Submission Yet</strong>
              <p className="mt-1 text-sm text-neutral">Approved drive testers with no daily submission record for the selected date.</p>
            </Link>
          </div>
        </Panel>
      </div>
      <Panel>
        <div className="mb-4 flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-extrabold uppercase tracking-[0.16em] text-brand">Daily Submissions</p>
            <h2 className="mt-1 text-xl font-semibold text-ink">Recent Activity</h2>
          </div>
          <Link
            className="text-sm font-bold text-brand"
            href={regionFilter ? `/daily-submissions?region=${regionFilter}` : "/daily-submissions"}
          >
            Open table
          </Link>
        </div>
        <DataTable headers={["Work Date", "Tester", "Workorder", "Shift", "Status", "File"]}>
          {recentSubmissions.map((submission) => (
            <tr key={submission.id}>
              <td className="whitespace-nowrap">{submission.workDate}</td>
              <td>
                <div className="max-w-48 truncate font-semibold text-ink" title={submission.testerName}>{submission.testerName}</div>
                <div className="max-w-56 truncate text-xs text-neutral" title={submission.testerEmail}>{submission.testerEmail}</div>
              </td>
              <td className="max-w-40 truncate font-mono text-xs sm:text-sm" title={submission.workorderCode}>{submission.workorderCode}</td>
              <td className="whitespace-nowrap">{submission.shift}</td>
              <td><StatusBadge value={submission.status} /></td>
              <td><StatusBadge value={submission.fileState} /></td>
            </tr>
          ))}
        </DataTable>
        <div className="mt-4">
          <Alert title="Review posture" tone="info">
            Keep “No Submission Yet” separate from “File Pending”. They answer different operational questions and should never be merged in the UI.
          </Alert>
        </div>
      </Panel>
    </div>
  );
}
