import Link from "next/link";
import { Alert } from "@/components/ui/alert";
import { DataTable } from "@/components/ui/data-table";
import { PageHeader } from "@/components/ui/page-header";
import { Panel } from "@/components/ui/panel";
import { ProgressBar } from "@/components/ui/progress-bar";
import { StatusBadge } from "@/components/ui/status-badge";
import { submissions, workorders } from "@/lib/mock/data";
import { formatFileState, formatRegion } from "@/lib/format/labels";

interface WorkorderDetailPageProps {
  workorderId: string;
}

export function WorkorderDetailPage({ workorderId }: WorkorderDetailPageProps) {
  const workorder = workorders.find((item) => item.id === workorderId) ?? workorders[0];
  const childSubmissions = submissions.filter((item) => item.workorderCode === workorder.workorderCode);

  return (
    <div className="space-y-6">
      <PageHeader
        kicker="Workorder"
        title={workorder.workorderCode}
        subtitle={`${formatRegion(workorder.region)} · created ${workorder.createdAt}`}
        actions={<div className="flex gap-3"><StatusBadge value={workorder.status} /><button type="button" className="rounded-panel bg-brand px-4 py-2 text-sm font-semibold text-white">Edit Workorder</button></div>}
      />
      <Panel>
        <div className="grid gap-4 md:grid-cols-5">
          <div className="rounded-panel border border-line bg-slate-50 p-4"><span className="text-xs font-bold uppercase tracking-[0.12em] text-neutral">Total Grids</span><strong className="mt-2 block text-3xl font-semibold text-ink">{workorder.totalGrids}</strong></div>
          <div className="rounded-panel border border-line bg-slate-50 p-4"><span className="text-xs font-bold uppercase tracking-[0.12em] text-neutral">Completed</span><strong className="mt-2 block text-3xl font-semibold text-ink">{workorder.completedGrids}</strong></div>
          <div className="rounded-panel border border-line bg-slate-50 p-4"><span className="text-xs font-bold uppercase tracking-[0.12em] text-neutral">Skipped</span><strong className="mt-2 block text-3xl font-semibold text-ink">{workorder.skippedGrids}</strong></div>
          <div className="rounded-panel border border-line bg-slate-50 p-4"><span className="text-xs font-bold uppercase tracking-[0.12em] text-neutral">Remaining</span><strong className="mt-2 block text-3xl font-semibold text-ink">{workorder.remainingGrids}</strong></div>
          <div className="rounded-panel border border-line bg-slate-50 p-4"><span className="text-xs font-bold uppercase tracking-[0.12em] text-neutral">Progress</span><strong className="mt-2 block text-3xl font-semibold text-ink">{workorder.progressPercent}%</strong></div>
        </div>
        <div className="mt-6"><ProgressBar value={workorder.progressPercent} caption="Remaining grids are computed from total grids minus aggregate completed and skipped." /></div>
      </Panel>
      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <Panel>
          <div className="mb-4 flex items-start justify-between gap-4">
            <div>
              <p className="text-xs font-extrabold uppercase tracking-[0.16em] text-brand">Child Daily Submissions</p>
              <h2 className="mt-1 text-xl font-semibold text-ink">Submission History</h2>
            </div>
            <button type="button" className="rounded-panel border border-line bg-panel px-4 py-2 text-sm font-semibold text-slate-700">Export</button>
          </div>
          <DataTable headers={["Work Date", "Tester", "Shift", "Ticket", "Completed", "Skipped", "Submission", "File", ""]}>
            {childSubmissions.map((submission) => (
              <tr key={submission.id}>
                <td>{submission.workDate}</td>
                <td>{submission.testerName}</td>
                <td>{submission.shift}</td>
                <td>{submission.ticketNumber}</td>
                <td className="text-right">{submission.completedGrids}</td>
                <td className="text-right">{submission.skippedGrids}</td>
                <td><StatusBadge value={submission.status} /></td>
                <td><StatusBadge value={submission.fileState} /></td>
                <td><Link href={`/daily-submissions/${submission.id}`} className="text-sm font-bold text-brand">Open</Link></td>
              </tr>
            ))}
          </DataTable>
        </Panel>
        <div className="space-y-6">
          <Panel>
            <p className="text-xs font-extrabold uppercase tracking-[0.16em] text-brand">Guardrails</p>
            <div className="mt-4 space-y-3 text-sm text-neutral">
              <p>Total grids cannot be reduced below aggregate completed plus skipped.</p>
              <p>Workorder code must remain unique after normalization.</p>
              <p>Region belongs to the parent workorder and affects date validation by timezone.</p>
            </div>
          </Panel>
          <Alert title="Edit scope" tone="info">
            Admin edits stay on detail pages. Inline table editing is intentionally excluded from V1 to keep high-impact changes explicit and auditable.
          </Alert>
        </div>
      </div>
    </div>
  );
}
