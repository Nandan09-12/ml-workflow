"use client";

import { FilterDateInput } from "@/components/ui/filter-date-input";
import { FilterSelect } from "@/components/ui/filter-select";
import { PageHeader } from "@/components/ui/page-header";
import { Panel } from "@/components/ui/panel";

export function ReportsPage() {
  return (
    <div className="space-y-6">
      <PageHeader kicker="Export Center" title="Reports" subtitle="Filtered CSV export flow for daily submissions, built to mirror list-page filters and backend query names." actions={<button type="button" className="rounded-panel bg-brand px-4 py-2 text-sm font-semibold text-white">Export Filtered CSV</button>} />
      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <Panel>
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <FilterDateInput label="Date From" value="2026-04-14" onChange={() => undefined} />
            <FilterDateInput label="Date To" value="2026-04-20" onChange={() => undefined} />
            <FilterSelect
              label="Region"
              value="ALL"
              onChange={() => undefined}
              options={[
                { value: "ALL", label: "All" },
                { value: "NE_UP", label: "NE-UP" },
                { value: "CENTRAL", label: "Central" },
                { value: "SOUTH_FLORIDA", label: "South/Florida" },
              ]}
            />
            <FilterSelect
              label="Submission Status"
              value="ALL"
              onChange={() => undefined}
              options={[
                { value: "ALL", label: "All" },
                { value: "IN_PROGRESS", label: "IN_PROGRESS" },
                { value: "CHECKED_OUT", label: "CHECKED_OUT" },
                { value: "COMPLETED", label: "COMPLETED" },
              ]}
            />
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
