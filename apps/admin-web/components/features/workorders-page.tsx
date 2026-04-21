import Link from "next/link";
import { DataTable } from "@/components/ui/data-table";
import { PageHeader } from "@/components/ui/page-header";
import { Panel } from "@/components/ui/panel";
import { ProgressBar } from "@/components/ui/progress-bar";
import { StatusBadge } from "@/components/ui/status-badge";
import { workorders } from "@/lib/mock/data";
import { formatRegion } from "@/lib/format/labels";

export function WorkordersPage() {
  return (
    <div className="space-y-6">
      <PageHeader kicker="Parent Records" title="Workorders" subtitle="Aggregate progress view across all child daily submissions, with guardrails for admin edits and reconciliation." />
      <Panel>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
          <label className="grid gap-1 text-xs font-bold uppercase tracking-[0.12em] text-neutral"><span>Workorder Code</span><input defaultValue="WO-" className="rounded-panel border border-line bg-panel px-3 py-2 text-sm font-medium text-ink" /></label>
          <label className="grid gap-1 text-xs font-bold uppercase tracking-[0.12em] text-neutral"><span>Region</span><select className="rounded-panel border border-line bg-panel px-3 py-2 text-sm font-medium text-ink"><option>All</option><option>NE-UP</option><option>Central</option><option>South/Florida</option></select></label>
          <label className="grid gap-1 text-xs font-bold uppercase tracking-[0.12em] text-neutral"><span>Status</span><select className="rounded-panel border border-line bg-panel px-3 py-2 text-sm font-medium text-ink"><option>All</option><option>ACTIVE</option><option>COMPLETED</option></select></label>
          <label className="grid gap-1 text-xs font-bold uppercase tracking-[0.12em] text-neutral"><span>Date From</span><input type="date" defaultValue="2026-04-14" className="rounded-panel border border-line bg-panel px-3 py-2 text-sm font-medium text-ink" /></label>
          <label className="grid gap-1 text-xs font-bold uppercase tracking-[0.12em] text-neutral"><span>Date To</span><input type="date" defaultValue="2026-04-20" className="rounded-panel border border-line bg-panel px-3 py-2 text-sm font-medium text-ink" /></label>
        </div>
      </Panel>
      <Panel>
        <DataTable headers={["Code", "Region", "Total", "Completed", "Skipped", "Remaining", "Progress", "Status", ""]}>
          {workorders.map((workorder) => (
            <tr key={workorder.id}>
              <td className="font-semibold text-ink">{workorder.workorderCode}</td>
              <td>{formatRegion(workorder.region)}</td>
              <td className="text-right">{workorder.totalGrids}</td>
              <td className="text-right">{workorder.completedGrids}</td>
              <td className="text-right">{workorder.skippedGrids}</td>
              <td className="text-right">{workorder.remainingGrids}</td>
              <td className="min-w-52"><ProgressBar value={workorder.progressPercent} caption={`${workorder.progressPercent}% complete`} /></td>
              <td><StatusBadge value={workorder.status} /></td>
              <td><Link href={`/workorders/${workorder.id}`} className="text-sm font-bold text-brand">Open</Link></td>
            </tr>
          ))}
        </DataTable>
      </Panel>
    </div>
  );
}
