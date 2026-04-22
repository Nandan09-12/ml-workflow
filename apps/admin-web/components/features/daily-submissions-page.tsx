"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Alert } from "@/components/ui/alert";
import { DataTable } from "@/components/ui/data-table";
import { EmptyState } from "@/components/ui/empty-state";
import { FilterDateInput } from "@/components/ui/filter-date-input";
import { FilterSelect } from "@/components/ui/filter-select";
import { Pagination } from "@/components/ui/pagination";
import { PageHeader } from "@/components/ui/page-header";
import { Panel } from "@/components/ui/panel";
import { SearchInput } from "@/components/ui/search-input";
import { StatusBadge } from "@/components/ui/status-badge";
import { TableToolbar } from "@/components/ui/table-toolbar";
import {
  buildDailySubmissionsSearchParams,
  defaultDailySubmissionsFilters,
  hasActiveDailySubmissionsFilters,
  parseDailySubmissionsFilters,
  type DailySubmissionsFilterState,
} from "@/lib/filters/daily-submissions";
import { formatRegion } from "@/lib/format/labels";
import { useAdminSubmissions } from "@/lib/hooks/use-admin-submissions";
import { useSubmissionsExport } from "@/lib/hooks/use-submissions-export";

export function DailySubmissionsPage() {
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();
  const searchParamsKey = searchParams.toString();
  const parsedFilters = useMemo(
    () => parseDailySubmissionsFilters(searchParamsKey),
    [searchParamsKey],
  );
  const [filters, setFilters] = useState(parsedFilters);

  useEffect(() => {
    setFilters(parsedFilters);
  }, [parsedFilters]);

  const { items, pagination, isLoading, isError, error } = useAdminSubmissions({
    work_date: filters.workDate || undefined,
    region: filters.region !== "ALL" ? filters.region : undefined,
    tester: filters.tester || undefined,
    workorder_code: filters.workorderCode || undefined,
    status: filters.submissionStatus !== "ALL" ? filters.submissionStatus : undefined,
    shift: filters.shift !== "ALL" ? filters.shift : undefined,
    file_submission_pending:
      filters.fileSubmissionPending !== "ALL"
        ? filters.fileSubmissionPending === "true"
        : undefined,
    page: filters.page,
    page_size: filters.pageSize,
  });
  const exportMutation = useSubmissionsExport();

  function handleExport() {
    exportMutation.mutate({
      work_date: filters.workDate || undefined,
      status: filters.submissionStatus !== "ALL" ? filters.submissionStatus : undefined,
      shift: filters.shift !== "ALL" ? filters.shift : undefined,
      file_submission_pending:
        filters.fileSubmissionPending !== "ALL"
          ? filters.fileSubmissionPending === "true"
          : undefined,
    });
  }

  function syncFilters(nextFilters: DailySubmissionsFilterState) {
    setFilters(nextFilters);

    const nextSearchParams = buildDailySubmissionsSearchParams(nextFilters);
    router.replace(nextSearchParams ? `${pathname}?${nextSearchParams}` : pathname);
  }

  function updateFilter<K extends keyof DailySubmissionsFilterState>(
    key: K,
    value: DailySubmissionsFilterState[K],
  ) {
    syncFilters({
      ...filters,
      [key]: value,
      page: defaultDailySubmissionsFilters.page,
    });
  }

  function updatePage(nextPage: number) {
    syncFilters({ ...filters, page: nextPage });
  }

  function updatePageSize(nextPageSize: number) {
    syncFilters({
      ...filters,
      page: defaultDailySubmissionsFilters.page,
      pageSize: nextPageSize,
    });
  }

  return (
    <div className="space-y-6">
      <PageHeader
        kicker="Operations Review"
        title="Daily Submissions"
        subtitle="Main operations table for daily records, file state follow-up, and drill-down into admin detail views."
        actions={
          <button
            type="button"
            onClick={handleExport}
            disabled={exportMutation.isPending}
            className="rounded-panel border border-line bg-panel px-4 py-2 text-sm font-semibold text-slate-700 disabled:opacity-50"
          >
            {exportMutation.isPending ? "Exporting…" : "Export CSV"}
          </button>
        }
      />
      {exportMutation.isError && (
        <Alert title="Export failed" tone="danger">
          {exportMutation.error instanceof Error ? exportMutation.error.message : "Failed to export submissions"}
        </Alert>
      )}
      {isError && (
        <Alert title="Error loading submissions" tone="danger">
          {error instanceof Error ? error.message : "Failed to load submissions"}
        </Alert>
      )}
      <Panel>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-6">
          <FilterDateInput label="Date" value={filters.workDate} onChange={(value) => updateFilter("workDate", value)} />
          <FilterSelect
            label="Region"
            value={filters.region}
            onChange={(value) => updateFilter("region", value as DailySubmissionsFilterState["region"])}
            options={[
              { value: "ALL", label: "All" },
              { value: "NE_UP", label: "NE-UP" },
              { value: "CENTRAL", label: "Central" },
              { value: "SOUTH_FLORIDA", label: "South/Florida" },
            ]}
          />
          <FilterSelect
            label="Shift"
            value={filters.shift}
            onChange={(value) => updateFilter("shift", value as DailySubmissionsFilterState["shift"])}
            options={[
              { value: "ALL", label: "All" },
              { value: "AM", label: "AM" },
              { value: "PM", label: "PM" },
            ]}
          />
          <FilterSelect
            label="Submission Status"
            value={filters.submissionStatus}
            onChange={(value) => updateFilter("submissionStatus", value as DailySubmissionsFilterState["submissionStatus"])}
            options={[
              { value: "ALL", label: "All" },
              { value: "IN_PROGRESS", label: "IN_PROGRESS" },
              { value: "CHECKED_OUT", label: "CHECKED_OUT" },
              { value: "COMPLETED", label: "COMPLETED" },
            ]}
          />
          <FilterSelect
            label="File Pending"
            value={filters.fileSubmissionPending}
            onChange={(value) => updateFilter("fileSubmissionPending", value as DailySubmissionsFilterState["fileSubmissionPending"])}
            options={[
              { value: "ALL", label: "All" },
              { value: "true", label: "Pending" },
              { value: "false", label: "Ready" },
            ]}
          />
          <SearchInput
            label="Workorder Code"
            value={filters.workorderCode}
            onChange={(value) => updateFilter("workorderCode", value)}
            placeholder="WO-NE"
          />
          <SearchInput
            label="Tester, Email, Or Ticket"
            value={filters.tester}
            onChange={(value) => updateFilter("tester", value)}
            placeholder="Search"
          />
        </div>
      </Panel>
      <Panel>
        <TableToolbar
          summary={`${pagination.total} matching submissions with filters persisted in the URL for shareable review links.`}
          actions={
            hasActiveDailySubmissionsFilters(filters) ? (
              <button
                type="button"
                className="rounded-panel border border-line bg-panel px-4 py-2 text-sm font-semibold text-slate-700"
                onClick={() => syncFilters(defaultDailySubmissionsFilters)}
              >
                Reset Filters
              </button>
            ) : null
          }
        />
        {isLoading ? (
          <div className="flex items-center justify-center py-12" role="status">
            <div className="animate-spin rounded-full border-4 border-line border-t-brand h-8 w-8" />
          </div>
        ) : items.length === 0 ? (
          <EmptyState
            title="No daily submissions found"
            description="Adjust the filters to widen the results. Empty filters are omitted from the URL so shared links stay clean."
          />
        ) : (
          <>
            <DataTable headers={["Work Date", "Tester", "Workorder", "Region", "Shift", "Completed", "Skipped", "Submission", "Workorder", "File", ""]}>
              {items.map((submission) => (
                <tr key={submission.id}>
                  <td className="whitespace-nowrap">{submission.workDate}</td>
                  <td>
                    <div className="max-w-48 truncate font-semibold text-ink" title={submission.testerName}>{submission.testerName}</div>
                    <div className="max-w-56 truncate text-xs text-neutral" title={submission.testerEmail}>{submission.testerEmail}</div>
                  </td>
                  <td className="max-w-40 truncate font-mono text-xs sm:text-sm" title={submission.workorderCode}>{submission.workorderCode}</td>
                  <td className="whitespace-nowrap">{formatRegion(submission.region)}</td>
                  <td className="whitespace-nowrap">{submission.shift}</td>
                  <td className="text-right">{submission.completedGrids}</td>
                  <td className="text-right">{submission.skippedGrids}</td>
                  <td><StatusBadge value={submission.status} /></td>
                  <td><StatusBadge value={submission.workorderStatus} /></td>
                  <td><StatusBadge value={submission.fileState} /></td>
                  <td className="whitespace-nowrap"><Link href={`/daily-submissions/${submission.id}`} className="text-sm font-bold text-brand">Open</Link></td>
                </tr>
              ))}
            </DataTable>
            <Pagination
              page={pagination.page}
              pageSize={pagination.pageSize}
              totalItems={pagination.total}
              totalPages={pagination.totalPages}
              onPageChange={updatePage}
              onPageSizeChange={updatePageSize}
            />
          </>
        )}
      </Panel>
    </div>
  );
}
