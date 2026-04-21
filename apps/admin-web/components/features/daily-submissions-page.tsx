import Link from "next/link";
import { DataTable } from "@/components/ui/data-table";
import { PageHeader } from "@/components/ui/page-header";
import { Panel } from "@/components/ui/panel";
import { StatusBadge } from "@/components/ui/status-badge";
import { submissions } from "@/lib/mock/data";
import { formatRegion } from "@/lib/format/labels";

export function DailySubmissionsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        kicker="Operations Review"
        title="Daily Submissions"
        subtitle="Main operations table for daily records, file state follow-up, and drill-down into admin detail views."
        actions={
          <button type="button" className="rounded-panel border border-line bg-panel px-4 py-2 text-sm font-semibold text-slate-700">Export CSV</button>
        }
      />
      <Panel>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-6">
          <label className="grid gap-1 text-xs font-bold uppercase tracking-[0.12em] text-neutral"><span>Date</span><input type="date" defaultValue="2026-04-20" className="rounded-panel border border-line bg-panel px-3 py-2 text-sm font-medium text-ink" /></label>
          <label className="grid gap-1 text-xs font-bold uppercase tracking-[0.12em] text-neutral"><span>Region</span><select className="rounded-panel border border-line bg-panel px-3 py-2 text-sm font-medium text-ink"><option>All</option><option>NE-UP</option><option>Central</option><option>South/Florida</option></select></label>
          <label className="grid gap-1 text-xs font-bold uppercase tracking-[0.12em] text-neutral"><span>Shift</span><select className="rounded-panel border border-line bg-panel px-3 py-2 text-sm font-medium text-ink"><option>All</option><option>AM</option><option>PM</option></select></label>
          <label className="grid gap-1 text-xs font-bold uppercase tracking-[0.12em] text-neutral"><span>Submission Status</span><select className="rounded-panel border border-line bg-panel px-3 py-2 text-sm font-medium text-ink"><option>All</option><option>IN_PROGRESS</option><option>CHECKED_OUT</option><option>COMPLETED</option></select></label>
          <label className="grid gap-1 text-xs font-bold uppercase tracking-[0.12em] text-neutral"><span>File State</span><select className="rounded-panel border border-line bg-panel px-3 py-2 text-sm font-medium text-ink"><option>All</option><option>File pending</option><option>Attached</option></select></label>
          <label className="grid gap-1 text-xs font-bold uppercase tracking-[0.12em] text-neutral"><span>Workorder Code</span><input defaultValue="WO-NE" className="rounded-panel border border-line bg-panel px-3 py-2 text-sm font-medium text-ink" /></label>
        </div>
      </Panel>
      <Panel>
        <DataTable headers={["Work Date", "Tester", "Workorder", "Region", "Shift", "Completed", "Skipped", "Submission", "Workorder", "File", ""]}>
          {submissions.map((submission) => (
            <tr key={submission.id}>
              <td>{submission.workDate}</td>
              <td>
                <div className="font-semibold text-ink">{submission.testerName}</div>
                <div className="text-xs text-neutral">{submission.testerEmail}</div>
              </td>
              <td>{submission.workorderCode}</td>
              <td>{formatRegion(submission.region)}</td>
              <td>{submission.shift}</td>
              <td className="text-right">{submission.completedGrids}</td>
              <td className="text-right">{submission.skippedGrids}</td>
              <td><StatusBadge value={submission.status} /></td>
              <td><StatusBadge value={submission.workorderStatus} /></td>
              <td><StatusBadge value={submission.fileState} /></td>
              <td><Link href={`/daily-submissions/${submission.id}`} className="text-sm font-bold text-brand">Open</Link></td>
            </tr>
          ))}
        </DataTable>
      </Panel>
    </div>
  );
}
