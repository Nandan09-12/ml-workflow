"use client";

import { useState } from "react";
import { Alert } from "@/components/ui/alert";
import { DataTable } from "@/components/ui/data-table";
import { FilterDateInput } from "@/components/ui/filter-date-input";
import { PageHeader } from "@/components/ui/page-header";
import { Panel } from "@/components/ui/panel";
import { StatusBadge } from "@/components/ui/status-badge";
import { Pagination } from "@/components/ui/pagination";
import { useNoSubmissionYet } from "@/lib/hooks/use-no-submission-yet";

export function NoSubmissionYetPage() {
  const [workDate, setWorkDate] = useState(() => new Date().toISOString().split("T")[0]);
  const [page, setPage] = useState(1);

  const { items, pagination, isLoading, isError, error, isFallback } = useNoSubmissionYet({
    work_date: workDate,
    page,
    page_size: 20,
  });

  return (
    <div className="space-y-6">
      <PageHeader kicker="Best-effort Daily Check" title="No Submission Yet" subtitle="Approved drive testers with no daily submission record for the selected date. This is not assignment-based in V1." />
      <Alert title="Meaning of this view" tone="info">
        No daily submission record exists for the selected date. This is not assignment-based in V1. It only compares approved drive testers against daily submissions created on that date.
      </Alert>
      {isFallback && (
        <Alert title="Using cached data" tone="info">
          Live data is temporarily unavailable. Showing cached data.
        </Alert>
      )}
      {isError && !isFallback && (
        <Alert title="Error loading data" tone="danger">
          {error instanceof Error ? error.message : "Failed to load no-submission-yet list"}
        </Alert>
      )}
      <Panel>
        <div className="mb-5 max-w-56">
          <FilterDateInput
            label="Date"
            value={workDate}
            onChange={(value) => { setWorkDate(value); setPage(1); }}
          />
        </div>
        {isLoading ? (
          <div className="flex items-center justify-center py-12" role="status">
            <div className="animate-spin rounded-full border-4 border-line border-t-brand h-8 w-8" />
          </div>
        ) : (
          <>
            <DataTable headers={["Tester", "Email", "Approved Role", "Last Submission", "Last Workorder"]}>
              {items.map((user) => (
                <tr key={user.id}>
                  <td className="font-semibold text-ink">{user.fullName}</td>
                  <td>{user.email}</td>
                  <td><StatusBadge value={user.approvedRole} /></td>
                  <td>{user.lastSubmissionDate ?? "Unknown"}</td>
                  <td>{user.lastWorkorderCode ?? "Unknown"}</td>
                </tr>
              ))}
            </DataTable>
            {pagination.totalPages > 1 && (
              <Pagination
                page={pagination.page}
                pageSize={pagination.pageSize}
                totalItems={pagination.total}
                totalPages={pagination.totalPages}
                onPageChange={setPage}
                onPageSizeChange={() => undefined}
              />
            )}
          </>
        )}
      </Panel>
    </div>
  );
}
