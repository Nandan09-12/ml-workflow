import { PageHeader } from "@/components/ui/page-header";
import { Panel } from "@/components/ui/panel";
import { StatusBadge } from "@/components/ui/status-badge";
import { pendingUsers } from "@/lib/mock/data";

export function PendingUsersPage() {
  return (
    <div className="space-y-6">
      <PageHeader kicker="Approval Queue" title="Pending Users" subtitle="Role requests awaiting admin approval or rejection. Admin requests should feel higher-risk than drive-tester approvals." />
      <div className="grid gap-4 xl:grid-cols-2">
        {pendingUsers.map((user) => (
          <Panel key={user.id}>
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="text-xl font-semibold text-ink">{user.fullName}</h2>
                <p className="mt-1 text-sm text-neutral">{user.email}</p>
              </div>
              <StatusBadge value={user.requestedRole} />
            </div>
            <p className="mt-4 text-sm text-neutral">{user.note}</p>
            <p className="mt-2 text-xs font-bold uppercase tracking-[0.12em] text-neutral">Requested {user.requestedAt}</p>
            <div className="mt-5 flex flex-wrap gap-3">
              <button type="button" className="rounded-panel bg-brand px-4 py-2 text-sm font-semibold text-white">Approve</button>
              <button type="button" className="rounded-panel bg-danger-soft px-4 py-2 text-sm font-semibold text-danger">Reject</button>
            </div>
          </Panel>
        ))}
      </div>
    </div>
  );
}
