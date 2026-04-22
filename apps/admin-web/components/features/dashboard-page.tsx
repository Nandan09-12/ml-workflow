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
import { dashboardMetrics } from "@/lib/mock/data";
import { formatFileState, formatRegion } from "@/lib/format/labels";
import { useAdminSubmissions } from "@/lib/hooks/use-admin-submissions";
import { useAdminWorkorders } from "@/lib/hooks/use-admin-workorders";
import { useDashboardSummary } from "@/lib/hooks/use-dashboard-summary";

export function DashboardPage() {
  const [workDate, setWorkDate] = useState(() => new Date().toISOString().split("T")[0]);
  const [dateFrom, setDateFrom] = useState<string | undefined>();
  const [dateTo, setDateTo] = useState<string | undefined>();

  const { data: dashboardData, isLoading, isError, error, isFallback } = useDashboardSummary({
    work_date: workDate,
    date_from: dateFrom,
    date_to: dateTo,
  });

  const { items: recentWorkorders } = useAdminWorkorders({ page_size: 4 });
  const { items: recentSubmissions } = useAdminSubmissions({ page_size: 5 });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12" role="status">
        <div className="animate-spin rounded-full border-4 border-line border-t-brand h-8 w-8"></div>
      </div>
    );
  }

  if (isError && !isFallback) {
    return (
      <Alert title="Error loading dashboard" tone="danger">
        {error instanceof Error ? error.message : "Failed to load dashboard data"}
      </Alert>
    );
  }

  // Build metrics from live data or mock fallback
  const liveMetrics = dashboardData
    ? [
        {
          label: "Active Workorders",
          value: dashboardData.active_workorders.toString(),
          detail: `${dashboardData.completed_workorders} completed`,
          tone: "brand" as const,
          href: "/workorders?status=ACTIVE",
        },
        {
          label: "Completed Submissions",
          value: dashboardData.completed_submissions.toString(),
          detail: (() => { const total = dashboardData.completed_submissions + dashboardData.ongoing_submissions + dashboardData.no_submission_yet; return total > 0 ? `${Math.round((dashboardData.completed_submissions / total) * 100)}% of daily records` : "0% of daily records"; })(),
          tone: "success" as const,
          href: "/daily-submissions?submission_status=COMPLETED",
        },
        {
          label: "Ongoing Submissions",
          value: dashboardData.ongoing_submissions.toString(),
          detail: "In progress",
          tone: "warning" as const,
          href: "/daily-submissions?submission_status=CHECKED_OUT",
        },
        {
          label: "No Submission Yet",
          value: dashboardData.no_submission_yet.toString(),
          detail: "Approved testers only",
          tone: "danger" as const,
          href: "/no-submission-yet",
        },
      ]
    : dashboardMetrics;
  return (
    <div className="space-y-6">
      {isFallback && (
        <Alert title="Using cached data" tone="info">
          Dashboard data is cached. Live updates may not be available at this time.
        </Alert>
      )}
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
              <select className="rounded-panel border border-line bg-panel px-3 py-2 text-sm font-medium text-ink">
                <option>All regions</option>
                <option>NE-UP</option>
                <option>Central</option>
                <option>South/Florida</option>
              </select>
            </label>
          </div>
        }
      />
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
            <Link className="text-sm font-bold text-brand" href="/workorders">View all</Link>
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
            <Link href="/daily-submissions?file_submission_pending=true" className="rounded-panel border border-line bg-slate-50 p-4 transition hover:border-brand">
              <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-brand-soft text-lg font-black text-brand">6</span>
              <strong className="mt-3 block text-sm font-semibold text-ink">File Pending</strong>
              <p className="mt-1 text-sm text-neutral">Checked-out submissions without an active CSV or XLSX closeout file.</p>
            </Link>
            <Link href="/users/pending" className="rounded-panel border border-line bg-slate-50 p-4 transition hover:border-brand">
              <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-brand-soft text-lg font-black text-brand">4</span>
              <strong className="mt-3 block text-sm font-semibold text-ink">Pending Users</strong>
              <p className="mt-1 text-sm text-neutral">Role requests awaiting admin approval or rejection.</p>
            </Link>
            <Link href="/no-submission-yet" className="rounded-panel border border-line bg-slate-50 p-4 transition hover:border-brand">
              <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-brand-soft text-lg font-black text-brand">{dashboardData?.no_submission_yet ?? 7}</span>
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
          <Link className="text-sm font-bold text-brand" href="/daily-submissions">Open table</Link>
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
