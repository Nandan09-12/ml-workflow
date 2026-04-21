import { PageHeader } from "@/components/ui/page-header";
import { Panel } from "@/components/ui/panel";

export function ReportsPage() {
  return (
    <div className="space-y-6">
      <PageHeader kicker="Export Center" title="Reports" subtitle="Filtered CSV export flow for daily submissions, built to mirror list-page filters and backend query names." actions={<button type="button" className="rounded-panel bg-brand px-4 py-2 text-sm font-semibold text-white">Export Filtered CSV</button>} />
      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <Panel>
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <label className="grid gap-1 text-xs font-bold uppercase tracking-[0.12em] text-neutral"><span>Date From</span><input type="date" defaultValue="2026-04-14" className="rounded-panel border border-line bg-panel px-3 py-2 text-sm font-medium text-ink" /></label>
            <label className="grid gap-1 text-xs font-bold uppercase tracking-[0.12em] text-neutral"><span>Date To</span><input type="date" defaultValue="2026-04-20" className="rounded-panel border border-line bg-panel px-3 py-2 text-sm font-medium text-ink" /></label>
            <label className="grid gap-1 text-xs font-bold uppercase tracking-[0.12em] text-neutral"><span>Region</span><select className="rounded-panel border border-line bg-panel px-3 py-2 text-sm font-medium text-ink"><option>All</option><option>NE-UP</option><option>Central</option><option>South/Florida</option></select></label>
            <label className="grid gap-1 text-xs font-bold uppercase tracking-[0.12em] text-neutral"><span>Submission Status</span><select className="rounded-panel border border-line bg-panel px-3 py-2 text-sm font-medium text-ink"><option>All</option><option>IN_PROGRESS</option><option>CHECKED_OUT</option><option>COMPLETED</option></select></label>
          </div>
        </Panel>
        <Panel>
          <p className="text-xs font-extrabold uppercase tracking-[0.16em] text-brand">Export Includes</p>
          <ul className="mt-4 grid gap-3 text-sm text-neutral">
            <li>Daily submission fields</li>
            <li>Tester name and email snapshots</li>
            <li>Parent workorder fields</li>
            <li>Computed remaining grids</li>
            <li>File pending indicator</li>
            <li>Submission and workorder statuses</li>
          </ul>
        </Panel>
      </div>
    </div>
  );
}
