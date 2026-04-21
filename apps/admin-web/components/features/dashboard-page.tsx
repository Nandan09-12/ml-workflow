import Link from "next/link";
import { Alert } from "@/components/ui/alert";
import { DataTable } from "@/components/ui/data-table";
import { MetricCard } from "@/components/ui/metric-card";
import { PageHeader } from "@/components/ui/page-header";
import { Panel } from "@/components/ui/panel";
import { ProgressBar } from "@/components/ui/progress-bar";
import { StatusBadge } from "@/components/ui/status-badge";
import { dashboardMetrics, submissions, workorders } from "@/lib/mock/data";
import { formatFileState, formatRegion } from "@/lib/format/labels";

export function DashboardPage() {
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
              <input type="date" defaultValue="2026-04-20" className="rounded-panel border border-line bg-panel px-3 py-2 text-sm font-medium text-ink" />
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
        {dashboardMetrics.map((metric) => (
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
            {workorders.map((workorder) => (
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
              <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-brand-soft text-lg font-black text-brand">7</span>
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
          {submissions.slice(0, 5).map((submission) => (
            <tr key={submission.id}>
              <td>{submission.workDate}</td>
              <td>
                <div className="font-semibold text-ink">{submission.testerName}</div>
                <div className="text-xs text-neutral">{submission.testerEmail}</div>
              </td>
              <td>{submission.workorderCode}</td>
              <td>{submission.shift}</td>
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
