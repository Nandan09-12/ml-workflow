"use client";

import { useEffect, useMemo, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { DataTable } from "@/components/ui/data-table";
import { EmptyState } from "@/components/ui/empty-state";
import { FilterSelect } from "@/components/ui/filter-select";
import { Pagination } from "@/components/ui/pagination";
import { PageHeader } from "@/components/ui/page-header";
import { Panel } from "@/components/ui/panel";
import { SearchInput } from "@/components/ui/search-input";
import { StatusBadge } from "@/components/ui/status-badge";
import { TableToolbar } from "@/components/ui/table-toolbar";
import { Alert } from "@/components/ui/alert";
import { ConfirmationDialog } from "@/components/ui/confirmation-dialog";
import {
  buildUsersSearchParams,
  defaultUsersFilters,
  hasActiveUsersFilters,
  parseUsersFilters,
  type UsersFilterState,
} from "@/lib/filters/users";
import { useAdminUsers } from "@/lib/hooks/use-admin-users";
import { useSuspendUser } from "@/lib/hooks/use-suspend-user";

export function UsersPage() {
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();
  const searchParamsKey = searchParams.toString();
  const parsedFilters = useMemo(() => parseUsersFilters(searchParamsKey), [searchParamsKey]);
  const [filters, setFilters] = useState(parsedFilters);
  const [suspendUserId, setSuspendUserId] = useState<string | null>(null);
  const [suspendUserName, setSuspendUserName] = useState("");

  const suspendMutation = useSuspendUser();

  useEffect(() => {
    setFilters(parsedFilters);
  }, [parsedFilters]);

  const { items, pagination, isLoading, isError, error, isFallback } = useAdminUsers({
    requested_role: filters.role !== "ALL" ? filters.role : undefined,
    account_status: filters.accountStatus !== "ALL" ? filters.accountStatus : undefined,
    page: filters.page,
    page_size: filters.pageSize,
  });

  function syncFilters(nextFilters: UsersFilterState) {
    setFilters(nextFilters);

    const nextSearchParams = buildUsersSearchParams(nextFilters);
    router.replace(nextSearchParams ? `${pathname}?${nextSearchParams}` : pathname);
  }

  function updateFilter<K extends keyof UsersFilterState>(key: K, value: UsersFilterState[K]) {
    syncFilters({
      ...filters,
      [key]: value,
      page: defaultUsersFilters.page,
    });
  }

  function updatePage(nextPage: number) {
    syncFilters({ ...filters, page: nextPage });
  }

  function updatePageSize(nextPageSize: number) {
    syncFilters({ ...filters, page: defaultUsersFilters.page, pageSize: nextPageSize });
  }

  return (
    <div className="space-y-6">
      <PageHeader kicker="Access Management" title="Users" subtitle="All app users with role and account-status filters. Admin-only access decisions remain explicit and auditable." />
      {isFallback && (
        <Alert title="Using cached data" tone="info">
          Live users data is temporarily unavailable. Showing cached data.
        </Alert>
      )}
      {isError && !isFallback && (
        <Alert title="Error loading users" tone="danger">
          {error instanceof Error ? error.message : "Failed to load users"}
        </Alert>
      )}
      <Panel>
        <div className="grid gap-3 md:grid-cols-3">
          <FilterSelect
            label="Role"
            value={filters.role}
            onChange={(value) => updateFilter("role", value as UsersFilterState["role"])}
            options={[
              { value: "ALL", label: "All" },
              { value: "ADMIN", label: "ADMIN" },
              { value: "DRIVE_TESTER", label: "DRIVE_TESTER" },
            ]}
          />
          <FilterSelect
            label="Account Status"
            value={filters.accountStatus}
            onChange={(value) => updateFilter("accountStatus", value as UsersFilterState["accountStatus"])}
            options={[
              { value: "ALL", label: "All" },
              { value: "APPROVED", label: "APPROVED" },
              { value: "PENDING_APPROVAL", label: "PENDING_APPROVAL" },
              { value: "REJECTED", label: "REJECTED" },
              { value: "SUSPENDED", label: "SUSPENDED" },
            ]}
          />
          <SearchInput label="Name or Email" value={filters.query} onChange={(value) => updateFilter("query", value)} placeholder="Search users" />
        </div>
      </Panel>
      <Panel>
        <TableToolbar
          summary={`${pagination.total} matching users with filter state preserved in the URL for review links.`}
          actions={
            hasActiveUsersFilters(filters) ? (
              <button
                type="button"
                className="rounded-panel border border-line bg-panel px-4 py-2 text-sm font-semibold text-slate-700"
                onClick={() => syncFilters(defaultUsersFilters)}
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
            title="No users found"
            description="Adjust the filters to widen the results. User list state is preserved in the URL so the same review view can be shared." 
          />
        ) : (
          <>
            <DataTable headers={["Full Name", "Email", "Requested Role", "Approved Role", "Status", "Created", "Last Login", ""]}>
              {items.map((user) => (
                <tr key={user.id}>
                  <td className="max-w-48 truncate font-semibold text-ink" title={user.fullName}>{user.fullName}</td>
                  <td className="max-w-56 truncate" title={user.email}>{user.email}</td>
                  <td><StatusBadge value={user.requestedRole} /></td>
                  <td>{user.approvedRole ? <StatusBadge value={user.approvedRole} /> : <span className="text-sm text-neutral">Pending</span>}</td>
                  <td><StatusBadge value={user.accountStatus} /></td>
                  <td className="whitespace-nowrap">{user.createdAt}</td>
                  <td className="whitespace-nowrap">{user.lastLogin ?? "Never"}</td>
                  <td>
                    {user.accountStatus === "APPROVED" && (
                      <button
                        type="button"
                        onClick={() => { setSuspendUserId(user.id); setSuspendUserName(user.fullName); }}
                        className="rounded-md border border-line px-3 py-1 text-xs font-semibold text-danger hover:bg-danger-soft"
                      >
                        Suspend
                      </button>
                    )}
                  </td>
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

      <ConfirmationDialog
        isOpen={suspendUserId !== null}
        onClose={() => setSuspendUserId(null)}
        onConfirm={() => {
          if (!suspendUserId) return;
          suspendMutation.mutate(suspendUserId, { onSuccess: () => setSuspendUserId(null) });
        }}
        title="Suspend User"
        description={`Suspend ${suspendUserName}? They will lose access immediately.`}
        confirmLabel="Suspend"
        tone="danger"
        isLoading={suspendMutation.isPending}
      />
    </div>
  );
}
