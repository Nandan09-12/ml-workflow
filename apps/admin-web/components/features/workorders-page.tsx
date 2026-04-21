"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { DataTable } from "@/components/ui/data-table";
import { EmptyState } from "@/components/ui/empty-state";
import { FilterDateInput } from "@/components/ui/filter-date-input";
import { FilterSelect } from "@/components/ui/filter-select";
import { Pagination } from "@/components/ui/pagination";
import { PageHeader } from "@/components/ui/page-header";
import { Panel } from "@/components/ui/panel";
import { ProgressBar } from "@/components/ui/progress-bar";
import { SearchInput } from "@/components/ui/search-input";
import { StatusBadge } from "@/components/ui/status-badge";
import { TableToolbar } from "@/components/ui/table-toolbar";
import { workorders } from "@/lib/mock/data";
import { formatRegion } from "@/lib/format/labels";
import {
  buildWorkordersSearchParams,
  defaultWorkordersFilters,
  filterWorkorders,
  hasActiveWorkordersFilters,
  paginateWorkorders,
  parseWorkordersFilters,
  type WorkordersFilterState,
} from "@/lib/filters/workorders";

export function WorkordersPage() {
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();
  const searchParamsKey = searchParams.toString();
  const parsedFilters = useMemo(() => parseWorkordersFilters(searchParamsKey), [searchParamsKey]);
  const [filters, setFilters] = useState(parsedFilters);

  useEffect(() => {
    setFilters(parsedFilters);
  }, [parsedFilters]);

  const filteredWorkorders = useMemo(() => filterWorkorders(workorders, filters), [filters]);
  const paginatedWorkorders = useMemo(() => paginateWorkorders(filteredWorkorders, filters), [filteredWorkorders, filters]);

  function syncFilters(nextFilters: WorkordersFilterState) {
    setFilters(nextFilters);

    const nextSearchParams = buildWorkordersSearchParams(nextFilters);
    router.replace(nextSearchParams ? `${pathname}?${nextSearchParams}` : pathname);
  }

  function updateFilter<K extends keyof WorkordersFilterState>(key: K, value: WorkordersFilterState[K]) {
    syncFilters({
      ...filters,
      [key]: value,
      page: defaultWorkordersFilters.page,
    });
  }

  function updatePage(nextPage: number) {
    syncFilters({ ...filters, page: nextPage });
  }

  function updatePageSize(nextPageSize: number) {
    syncFilters({ ...filters, page: defaultWorkordersFilters.page, pageSize: nextPageSize });
  }

  return (
    <div className="space-y-6">
      <PageHeader kicker="Parent Records" title="Workorders" subtitle="Aggregate progress view across all child daily submissions, with guardrails for admin edits and reconciliation." />
      <Panel>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
          <SearchInput label="Workorder Code" value={filters.workorderCode} onChange={(value) => updateFilter("workorderCode", value)} placeholder="WO-" />
          <FilterSelect
            label="Region"
            value={filters.region}
            onChange={(value) => updateFilter("region", value as WorkordersFilterState["region"])}
            options={[
              { value: "ALL", label: "All" },
              { value: "NE_UP", label: "NE-UP" },
              { value: "CENTRAL", label: "Central" },
              { value: "SOUTH_FLORIDA", label: "South/Florida" },
            ]}
          />
          <FilterSelect
            label="Status"
            value={filters.status}
            onChange={(value) => updateFilter("status", value as WorkordersFilterState["status"])}
            options={[
              { value: "ALL", label: "All" },
              { value: "ACTIVE", label: "ACTIVE" },
              { value: "COMPLETED", label: "COMPLETED" },
            ]}
          />
          <FilterDateInput label="Date From" value={filters.dateFrom} onChange={(value) => updateFilter("dateFrom", value)} />
          <FilterDateInput label="Date To" value={filters.dateTo} onChange={(value) => updateFilter("dateTo", value)} />
        </div>
      </Panel>
      <Panel>
        <TableToolbar
          summary={`${paginatedWorkorders.totalItems} matching workorders with filters and pagination persisted in the URL.`}
          actions={
            hasActiveWorkordersFilters(filters) ? (
              <button
                type="button"
                className="rounded-panel border border-line bg-panel px-4 py-2 text-sm font-semibold text-slate-700"
                onClick={() => syncFilters(defaultWorkordersFilters)}
              >
                Reset Filters
              </button>
            ) : null
          }
        />
        {paginatedWorkorders.totalItems === 0 ? (
          <EmptyState
            title="No workorders found"
            description="Adjust the filters to widen the results. Workorder list state stays in the URL so drill-down links can preserve context."
          />
        ) : (
          <>
            <DataTable headers={["Code", "Region", "Total", "Completed", "Skipped", "Remaining", "Progress", "Status", ""]}>
              {paginatedWorkorders.items.map((workorder) => (
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
            <Pagination
              page={paginatedWorkorders.page}
              pageSize={paginatedWorkorders.pageSize}
              totalItems={paginatedWorkorders.totalItems}
              totalPages={paginatedWorkorders.totalPages}
              onPageChange={updatePage}
              onPageSizeChange={updatePageSize}
            />
          </>
        )}
      </Panel>
    </div>
  );
}
