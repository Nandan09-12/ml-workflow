"use client";

import { useState } from "react";
import Link from "next/link";
import { Alert } from "@/components/ui/alert";
import { DataTable } from "@/components/ui/data-table";
import { DefinitionList } from "@/components/ui/definition-list";
import { EditDrawer } from "@/components/ui/edit-drawer";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { PageHeader } from "@/components/ui/page-header";
import { Panel } from "@/components/ui/panel";
import { ProgressBar } from "@/components/ui/progress-bar";
import { StatusBadge } from "@/components/ui/status-badge";
import { useAdminWorkorder } from "@/lib/hooks/use-admin-workorder";
import { useEditWorkorder } from "@/lib/hooks/use-edit-workorder";
import { formatFileState, formatRegion } from "@/lib/format/labels";
import type { Region } from "@/lib/types/domain";

interface WorkorderDetailPageProps {
  workorderId: string;
}

export function WorkorderDetailPage({ workorderId }: WorkorderDetailPageProps) {
  const { workorder, isLoading, isError, error, isFallback } = useAdminWorkorder(workorderId);
  const editMutation = useEditWorkorder();

  const [editOpen, setEditOpen] = useState(false);
  const [editCode, setEditCode] = useState("");
  const [editRegion, setEditRegion] = useState<Region>("NE_UP");
  const [editTotalGrids, setEditTotalGrids] = useState("");

  function openEdit() {
    if (!workorder) return;
    setEditCode(workorder.workorderCode);
    setEditRegion(workorder.region);
    setEditTotalGrids(String(workorder.totalGrids));
    setEditOpen(true);
  }

  function handleSave() {
    editMutation.mutate(
      {
        workorderId,
        workorder_code: editCode || undefined,
        region: editRegion,
        total_grids: editTotalGrids ? Number(editTotalGrids) : undefined,
      },
      { onSuccess: () => setEditOpen(false) },
    );
  }

  if (isLoading) return <LoadingState />;
  if (isError && !isFallback) {
    return <ErrorState title="Failed to load workorder" description={error?.message ?? "An unexpected error occurred."} />;
  }
  if (!workorder) return <ErrorState title="Workorder not found" description="The requested workorder could not be found." />;

  const childSubmissions = workorder.submissions;

  return (
    <>
      <div className="space-y-6">
        {isFallback && (
          <Alert title="Using cached data" tone="info">
            Live workorder data is temporarily unavailable. Showing cached data.
          </Alert>
        )}
        <PageHeader
          kicker="Workorder"
          title={workorder.workorderCode}
          subtitle={`${formatRegion(workorder.region)} · created ${new Date(workorder.createdAt).toLocaleDateString()}`}
          actions={
            <div className="flex gap-3">
              <StatusBadge value={workorder.status} />
              <button
                type="button"
                onClick={openEdit}
                className="rounded-panel bg-brand px-4 py-2 text-sm font-semibold text-white"
              >
                Edit Workorder
              </button>
            </div>
          }
        />
        <Panel>
          <div className="grid gap-4 md:grid-cols-5">
            <div className="rounded-panel border border-line bg-slate-50 p-4"><span className="text-xs font-bold uppercase tracking-[0.12em] text-neutral">Total Grids</span><strong className="mt-2 block text-3xl font-semibold text-ink">{workorder.totalGrids}</strong></div>
            <div className="rounded-panel border border-line bg-slate-50 p-4"><span className="text-xs font-bold uppercase tracking-[0.12em] text-neutral">Completed</span><strong className="mt-2 block text-3xl font-semibold text-ink">{workorder.completedGrids}</strong></div>
            <div className="rounded-panel border border-line bg-slate-50 p-4"><span className="text-xs font-bold uppercase tracking-[0.12em] text-neutral">Skipped</span><strong className="mt-2 block text-3xl font-semibold text-ink">{workorder.skippedGrids}</strong></div>
            <div className="rounded-panel border border-line bg-slate-50 p-4"><span className="text-xs font-bold uppercase tracking-[0.12em] text-neutral">Remaining</span><strong className="mt-2 block text-3xl font-semibold text-ink">{workorder.remainingGrids}</strong></div>
            <div className="rounded-panel border border-line bg-slate-50 p-4"><span className="text-xs font-bold uppercase tracking-[0.12em] text-neutral">Progress</span><strong className="mt-2 block text-3xl font-semibold text-ink">{workorder.progressPercent}%</strong></div>
          </div>
          <div className="mt-6"><ProgressBar value={workorder.progressPercent} caption="Remaining grids are computed from total grids minus aggregate completed and skipped." /></div>
        </Panel>
        <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
          <Panel>
            <div className="mb-4 flex items-start justify-between gap-4">
              <div>
                <p className="text-xs font-extrabold uppercase tracking-[0.16em] text-brand">Child Daily Submissions</p>
                <h2 className="mt-1 text-xl font-semibold text-ink">Submission History</h2>
              </div>
            </div>
            <DataTable headers={["Work Date", "Tester", "Shift", "Ticket", "Completed", "Skipped", "Submission", "File", ""]}>
              {childSubmissions.map((submission) => (
                <tr key={submission.id}>
                  <td className="whitespace-nowrap">{submission.workDate}</td>
                  <td className="max-w-48 truncate" title={submission.testerName}>{submission.testerName}</td>
                  <td className="whitespace-nowrap">{submission.shift}</td>
                  <td className="max-w-40 truncate" title={submission.ticketNumber}>{submission.ticketNumber}</td>
                  <td className="text-right">{submission.completedGrids}</td>
                  <td className="text-right">{submission.skippedGrids}</td>
                  <td><StatusBadge value={submission.status} /></td>
                  <td><StatusBadge value={submission.fileState} /></td>
                  <td className="whitespace-nowrap"><Link href={`/daily-submissions/${submission.id}`} className="text-sm font-bold text-brand">Open</Link></td>
                </tr>
              ))}
            </DataTable>
          </Panel>
          <div className="space-y-6">
            <Panel>
              <p className="text-xs font-extrabold uppercase tracking-[0.16em] text-brand">Guardrails</p>
              <div className="mt-4">
                <DefinitionList
                  items={[
                    { term: "Minimum Total", description: "Cannot drop below aggregate completed plus skipped" },
                    { term: "Code Rule", description: "Workorder code must remain unique after normalization" },
                    { term: "Region Guard", description: "Region stays on the parent workorder and influences date validation" },
                  ]}
                />
              </div>
            </Panel>
            <Alert title="Edit scope" tone="info">
              Admin edits stay on detail pages. Inline table editing is intentionally excluded from V1 to keep high-impact changes explicit and auditable.
            </Alert>
          </div>
        </div>
      </div>

      <EditDrawer
        isOpen={editOpen}
        onClose={() => setEditOpen(false)}
        title="Edit Workorder"
        onSave={handleSave}
        isLoading={editMutation.isPending}
      >
        <div className="grid gap-4">
          {editMutation.isError && (
            <Alert title="Save failed" tone="danger">
              {editMutation.error instanceof Error ? editMutation.error.message : "Unknown error"}
            </Alert>
          )}
          <label className="grid gap-1">
            <span className="text-xs font-semibold uppercase tracking-[0.12em] text-neutral">Workorder Code</span>
            <input
              type="text"
              value={editCode}
              onChange={(e) => setEditCode(e.target.value)}
              className="rounded-md border border-line px-3 py-2 text-sm text-ink"
            />
          </label>
          <label className="grid gap-1">
            <span className="text-xs font-semibold uppercase tracking-[0.12em] text-neutral">Region</span>
            <select
              value={editRegion}
              onChange={(e) => setEditRegion(e.target.value as Region)}
              className="rounded-md border border-line px-3 py-2 text-sm text-ink"
            >
              <option value="NE_UP">NE-UP</option>
              <option value="CENTRAL">Central</option>
              <option value="SOUTH_FLORIDA">South/Florida</option>
            </select>
          </label>
          <label className="grid gap-1">
            <span className="text-xs font-semibold uppercase tracking-[0.12em] text-neutral">Total Grids</span>
            <input
              type="number"
              min={1}
              value={editTotalGrids}
              onChange={(e) => setEditTotalGrids(e.target.value)}
              className="rounded-md border border-line px-3 py-2 text-sm text-ink"
            />
          </label>
        </div>
      </EditDrawer>
    </>
  );
}
