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
import { users } from "@/lib/mock/data";
import {
  buildUsersSearchParams,
  defaultUsersFilters,
  filterUsers,
  hasActiveUsersFilters,
  paginateUsers,
  parseUsersFilters,
  type UsersFilterState,
} from "@/lib/filters/users";

export function UsersPage() {
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();
  const searchParamsKey = searchParams.toString();
  const parsedFilters = useMemo(() => parseUsersFilters(searchParamsKey), [searchParamsKey]);
  const [filters, setFilters] = useState(parsedFilters);

  useEffect(() => {
    setFilters(parsedFilters);
  }, [parsedFilters]);

  const filteredUsers = useMemo(() => filterUsers(users, filters), [filters]);
  const paginatedUsers = useMemo(() => paginateUsers(filteredUsers, filters), [filteredUsers, filters]);

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
          summary={`${paginatedUsers.totalItems} matching users with filter state preserved in the URL for review links.`}
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
        {paginatedUsers.totalItems === 0 ? (
          <EmptyState
            title="No users found"
            description="Adjust the filters to widen the results. User list state is preserved in the URL so the same review view can be shared." 
          />
        ) : (
          <>
            <DataTable headers={["Full Name", "Email", "Requested Role", "Approved Role", "Status", "Created", "Last Login"]}>
              {paginatedUsers.items.map((user) => (
                <tr key={user.id}>
                  <td className="font-semibold text-ink">{user.fullName}</td>
                  <td>{user.email}</td>
                  <td><StatusBadge value={user.requestedRole} /></td>
                  <td>{user.approvedRole ? <StatusBadge value={user.approvedRole} /> : <span className="text-sm text-neutral">Pending</span>}</td>
                  <td><StatusBadge value={user.accountStatus} /></td>
                  <td>{user.createdAt}</td>
                  <td>{user.lastLogin ?? "Never"}</td>
                </tr>
              ))}
            </DataTable>
            <Pagination
              page={paginatedUsers.page}
              pageSize={paginatedUsers.pageSize}
              totalItems={paginatedUsers.totalItems}
              totalPages={paginatedUsers.totalPages}
              onPageChange={updatePage}
              onPageSizeChange={updatePageSize}
            />
          </>
        )}
      </Panel>
    </div>
  );
}
