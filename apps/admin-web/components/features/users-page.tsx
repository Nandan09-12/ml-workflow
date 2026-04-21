import { DataTable } from "@/components/ui/data-table";
import { PageHeader } from "@/components/ui/page-header";
import { Panel } from "@/components/ui/panel";
import { StatusBadge } from "@/components/ui/status-badge";
import { users } from "@/lib/mock/data";

export function UsersPage() {
  return (
    <div className="space-y-6">
      <PageHeader kicker="Access Management" title="Users" subtitle="All app users with role and account-status filters. Admin-only access decisions remain explicit and auditable." />
      <Panel>
        <div className="grid gap-3 md:grid-cols-3">
          <label className="grid gap-1 text-xs font-bold uppercase tracking-[0.12em] text-neutral"><span>Role</span><select className="rounded-panel border border-line bg-panel px-3 py-2 text-sm font-medium text-ink"><option>All</option><option>ADMIN</option><option>DRIVE_TESTER</option></select></label>
          <label className="grid gap-1 text-xs font-bold uppercase tracking-[0.12em] text-neutral"><span>Account Status</span><select className="rounded-panel border border-line bg-panel px-3 py-2 text-sm font-medium text-ink"><option>All</option><option>APPROVED</option><option>PENDING_APPROVAL</option><option>REJECTED</option><option>SUSPENDED</option></select></label>
          <label className="grid gap-1 text-xs font-bold uppercase tracking-[0.12em] text-neutral"><span>Name or Email</span><input defaultValue="asha@mltech.com" className="rounded-panel border border-line bg-panel px-3 py-2 text-sm font-medium text-ink" /></label>
        </div>
      </Panel>
      <Panel>
        <DataTable headers={["Full Name", "Email", "Requested Role", "Approved Role", "Status", "Created", "Last Login"]}>
          {users.map((user) => (
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
      </Panel>
    </div>
  );
}
