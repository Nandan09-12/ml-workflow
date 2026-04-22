"use client";

import { useState } from "react";
import { Alert } from "@/components/ui/alert";
import { FilterDateInput } from "@/components/ui/filter-date-input";
import { FilterSelect } from "@/components/ui/filter-select";
import { PageHeader } from "@/components/ui/page-header";
import { Panel } from "@/components/ui/panel";
import { useSubmissionsExport } from "@/lib/hooks/use-submissions-export";

export function ReportsPage() {
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [status, setStatus] = useState("ALL");
  const [shift, setShift] = useState("ALL");

  const exportMutation = useSubmissionsExport();

  function handleExport() {
    exportMutation.mutate({
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
      status: status !== "ALL" ? status : undefined,
      shift: shift !== "ALL" ? shift : undefined,
    });
  }

  return (
    <div className="space-y-6">
      <PageHeader
        kicker="Export Center"
        title="Reports"
        subtitle="Filtered CSV export flow for daily submissions, built to mirror list-page filters and backend query names."
        actions={
          <button
            type="button"
            onClick={handleExport}
            disabled={exportMutation.isPending}
            className="rounded-panel bg-brand px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
          >
            {exportMutation.isPending ? "Exporting…" : "Export Filtered CSV"}
          </button>
        }
      />
      {exportMutation.isError && (
        <Alert title="Export failed" tone="danger">
          {exportMutation.error instanceof Error ? exportMutation.error.message : "Unknown error"}
        </Alert>
      )}
      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <Panel>
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            <FilterDateInput label="Date From" value={dateFrom} onChange={setDateFrom} />
            <FilterDateInput label="Date To" value={dateTo} onChange={setDateTo} />
            <FilterSelect
              label="Submission Status"
              value={status}
              onChange={setStatus}
              options={[
                { value: "ALL", label: "All" },
                { value: "IN_PROGRESS", label: "IN_PROGRESS" },
                { value: "CHECKED_OUT", label: "CHECKED_OUT" },
                { value: "COMPLETED", label: "COMPLETED" },
              ]}
            />
            <FilterSelect
              label="Shift"
              value={shift}
              onChange={setShift}
              options={[
                { value: "ALL", label: "All" },
                { value: "AM", label: "AM" },
                { value: "PM", label: "PM" },
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
