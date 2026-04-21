import { Alert } from "@/components/ui/alert";
import { DataTable } from "@/components/ui/data-table";
import { PageHeader } from "@/components/ui/page-header";
import { Panel } from "@/components/ui/panel";
import { StatusBadge } from "@/components/ui/status-badge";
import { noSubmissionYet } from "@/lib/mock/data";

export function NoSubmissionYetPage() {
  return (
    <div className="space-y-6">
      <PageHeader kicker="Best-effort Daily Check" title="No Submission Yet" subtitle="Approved drive testers with no daily submission record for the selected date. This is not assignment-based in V1." />
      <Alert title="Meaning of this view" tone="info">
        No daily submission record exists for the selected date. This is not assignment-based in V1. It only compares approved drive testers against daily submissions created on that date.
      </Alert>
      <Panel>
        <div className="mb-5 max-w-56">
          <label className="grid gap-1 text-xs font-bold uppercase tracking-[0.12em] text-neutral"><span>Date</span><input type="date" defaultValue="2026-04-20" className="rounded-panel border border-line bg-panel px-3 py-2 text-sm font-medium text-ink" /></label>
        </div>
        <DataTable headers={["Tester", "Email", "Approved Role", "Last Submission", "Last Workorder"]}>
          {noSubmissionYet.map((user) => (
            <tr key={user.id}>
              <td className="font-semibold text-ink">{user.fullName}</td>
              <td>{user.email}</td>
              <td><StatusBadge value={user.approvedRole} /></td>
              <td>{user.lastSubmissionDate ?? "Unknown"}</td>
              <td>{user.lastWorkorderCode ?? "Unknown"}</td>
            </tr>
          ))}
        </DataTable>
      </Panel>
    </div>
  );
}
