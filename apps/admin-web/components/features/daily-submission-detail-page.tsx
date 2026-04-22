"use client";

import { useState } from "react";
import { Alert } from "@/components/ui/alert";
import { ConfirmationDialog } from "@/components/ui/confirmation-dialog";
import { DefinitionList } from "@/components/ui/definition-list";
import { EditDrawer } from "@/components/ui/edit-drawer";
import { LoadingState } from "@/components/ui/loading-state";
import { ErrorState } from "@/components/ui/error-state";
import { PageHeader } from "@/components/ui/page-header";
import { Panel } from "@/components/ui/panel";
import { ProgressBar } from "@/components/ui/progress-bar";
import { StatusBadge } from "@/components/ui/status-badge";
import { Timeline } from "@/components/ui/timeline";
import { useAdminSubmission } from "@/lib/hooks/use-admin-submission";
import { useSubmissionAudit } from "@/lib/hooks/use-submission-audit";
import { useSubmissionAttachmentHistory } from "@/lib/hooks/use-submission-attachment-history";
import { useEditSubmission } from "@/lib/hooks/use-edit-submission";
import { useReopenSubmission } from "@/lib/hooks/use-reopen-submission";
import { useAttachmentDownload } from "@/lib/hooks/use-attachment-download";
import { formatRegion } from "@/lib/format/labels";
import type { ApiAuditItem, ApiAttachmentHistoryItem } from "@/lib/types/domain";

interface DailySubmissionDetailPageProps {
  submissionId: string;
}

function auditItemToTimeline(item: ApiAuditItem) {
  const fields = item.changed_fields_json?.fields ?? [];
  return {
    id: item.id,
    title: `${item.action_type.replace(/_/g, " ")} by ${item.actor_role.replace(/_/g, " ")}`,
    detail: `${new Date(item.created_at).toLocaleString()}${fields.length ? ` · ${fields.join(", ")}` : ""}`,
  };
}

function attachmentItemToTimeline(item: ApiAttachmentHistoryItem) {
  const sizeMb = (item.file_size_bytes / 1024 / 1024).toFixed(1);
  return {
    id: item.id,
    title: item.file_name,
    detail: `${item.mime_type} · ${sizeMb} MB · ${item.is_active ? "Active" : "Superseded"} · ${new Date(item.uploaded_at).toLocaleString()}`,
  };
}

export function DailySubmissionDetailPage({ submissionId }: DailySubmissionDetailPageProps) {
  const { submission, isLoading, isError, error } = useAdminSubmission(submissionId);
  const { items: auditItems, isLoading: auditLoading } = useSubmissionAudit(submissionId);
  const { items: attachmentItems, isLoading: attachmentLoading } = useSubmissionAttachmentHistory(submissionId);

  const editMutation = useEditSubmission();
  const reopenMutation = useReopenSubmission();
  const downloadMutation = useAttachmentDownload();
  const activeAttachment = attachmentItems.find((item) => item.is_active) ?? null;

  const [editOpen, setEditOpen] = useState(false);
  const [reopenOpen, setReopenOpen] = useState(false);

  const [editWorkDate, setEditWorkDate] = useState("");
  const [editShift, setEditShift] = useState("");
  const [editTicket, setEditTicket] = useState("");
  const [editCompleted, setEditCompleted] = useState("");
  const [editSkipped, setEditSkipped] = useState("");
  const [editForceTested, setEditForceTested] = useState("");

  function openEdit() {
    if (!submission) return;
    setEditWorkDate(submission.workDate);
    setEditShift(submission.shift);
    setEditTicket(submission.ticketNumber);
    setEditCompleted(String(submission.completedGrids));
    setEditSkipped(String(submission.skippedGrids));
    setEditForceTested(String(submission.forceTestedGrids));
    setEditOpen(true);
  }

  function handleSave() {
    if (!submission) return;
    editMutation.mutate(
      {
        submissionId,
        version_number: submission.versionNumber,
        work_date: editWorkDate || undefined,
        shift: (editShift as "AM" | "PM") || undefined,
        ticket_number: editTicket || undefined,
        completed_grids: editCompleted ? Number(editCompleted) : undefined,
        skipped_grids: editSkipped ? Number(editSkipped) : undefined,
        force_tested_grids: editForceTested ? Number(editForceTested) : undefined,
      },
      { onSuccess: () => setEditOpen(false) },
    );
  }

  function handleReopen() {
    reopenMutation.mutate(submissionId, { onSuccess: () => setReopenOpen(false) });
  }

  if (isLoading) return <LoadingState />;
  if (isError) {
    return <ErrorState title="Failed to load submission" description={error?.message ?? "An unexpected error occurred."} />;
  }
  if (!submission) return <ErrorState title="Submission not found" description="The requested submission could not be found." />;

  const auditTimeline = auditItems.map(auditItemToTimeline);
  const attachmentTimeline = attachmentItems.map(attachmentItemToTimeline);

  return (
    <>
      <div className="grid gap-6 xl:grid-cols-[1.3fr_0.7fr]">
        <div className="space-y-6">
          <PageHeader
            kicker="Daily Submission"
            title={`${submission.testerName} / ${submission.workorderCode}`}
            subtitle={`${submission.workDate}, ${submission.shift} shift, ticket ${submission.ticketNumber}`}
            actions={
              <div className="flex flex-wrap gap-3">
                <StatusBadge value={submission.status} />
                {submission.fileSubmissionPending ? <StatusBadge value="FILE_PENDING" /> : null}
                <button
                  type="button"
                  onClick={openEdit}
                  className="rounded-panel bg-brand px-4 py-2 text-sm font-semibold text-white"
                >
                  Edit Submission
                </button>
              </div>
            }
          />
          {submission.fileSubmissionPending ? (
            <Alert title="Closeout file is missing" tone="warning">
              This daily submission has been checked out but has no active CSV or XLSX attachment.
            </Alert>
          ) : null}
          <Panel>
            <div className="grid gap-3 md:grid-cols-5">
              <div className="rounded-panel border border-line bg-slate-50 p-4">
                <span className="text-xs font-bold uppercase tracking-[0.12em] text-neutral">Completed</span>
                <strong className="mt-2 block text-3xl font-semibold text-ink">{submission.completedGrids}</strong>
              </div>
              <div className="rounded-panel border border-line bg-slate-50 p-4">
                <span className="text-xs font-bold uppercase tracking-[0.12em] text-neutral">Skipped</span>
                <strong className="mt-2 block text-3xl font-semibold text-ink">{submission.skippedGrids}</strong>
              </div>
              <div className="rounded-panel border border-line bg-slate-50 p-4">
                <span className="text-xs font-bold uppercase tracking-[0.12em] text-neutral">Force Tested</span>
                <strong className="mt-2 block text-3xl font-semibold text-ink">{submission.forceTestedGrids}</strong>
              </div>
              <div className="rounded-panel border border-line bg-slate-50 p-4">
                <span className="text-xs font-bold uppercase tracking-[0.12em] text-neutral">Started</span>
                <strong className="mt-2 block text-lg font-semibold text-ink">{new Date(submission.startedAt).toLocaleString()}</strong>
              </div>
              <div className="rounded-panel border border-line bg-slate-50 p-4">
                <span className="text-xs font-bold uppercase tracking-[0.12em] text-neutral">Ended</span>
                <strong className="mt-2 block text-lg font-semibold text-ink">
                  {submission.endedAt ? new Date(submission.endedAt).toLocaleString() : "In progress"}
                </strong>
              </div>
            </div>
          </Panel>
          <Panel>
            <div className="mb-4 flex items-start justify-between gap-4">
              <div>
                <p className="text-xs font-extrabold uppercase tracking-[0.16em] text-brand">Parent Workorder</p>
                <h2 className="mt-1 text-xl font-semibold text-ink">{submission.workorderCode}</h2>
              </div>
              <StatusBadge value={submission.workorderStatus} />
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <DefinitionList
                items={[
                  { term: "Region", description: formatRegion(submission.region) },
                  { term: "Tester", description: submission.testerName },
                  { term: "Email", description: submission.testerEmail },
                  { term: "Ticket", description: submission.ticketNumber },
                ]}
              />
              <ProgressBar
                value={0}
                caption="Parent workorder progress is available on the workorder detail page."
              />
            </div>
          </Panel>
        </div>
        <div className="space-y-6">
          <Panel>
            <p className="text-xs font-extrabold uppercase tracking-[0.16em] text-brand">Active Attachment</p>
            <div className="mt-4">
              {attachmentLoading ? (
                <p className="text-sm text-neutral">Loading…</p>
              ) : !activeAttachment ? (
                <p className="text-sm text-neutral">No active file yet.</p>
              ) : (
                <div className="space-y-3">
                  <div className="rounded-panel border border-line bg-slate-50 p-3">
                    <p className="truncate text-sm font-semibold text-ink">{activeAttachment.file_name}</p>
                    <p className="mt-1 text-xs text-neutral">
                      {activeAttachment.mime_type} · {(activeAttachment.file_size_bytes / 1024 / 1024).toFixed(1)} MB
                    </p>
                    <p className="mt-0.5 text-xs text-neutral">
                      Uploaded {new Date(activeAttachment.uploaded_at).toLocaleString()}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => downloadMutation.mutate(activeAttachment.id)}
                    disabled={downloadMutation.isPending}
                    className="w-full rounded-panel border border-brand px-4 py-2 text-sm font-semibold text-brand hover:bg-brand/5 disabled:opacity-50"
                  >
                    {downloadMutation.isPending ? "Getting link…" : "Download File"}
                  </button>
                  {downloadMutation.isError && (
                    <Alert title="Download failed" tone="danger">
                      {downloadMutation.error instanceof Error
                        ? downloadMutation.error.message
                        : "Could not generate download link."}
                    </Alert>
                  )}
                </div>
              )}
            </div>
          </Panel>
          <Panel>
            <p className="text-xs font-extrabold uppercase tracking-[0.16em] text-brand">Attachment History</p>
            {attachmentLoading ? (
              <p className="mt-4 text-sm text-neutral">Loading…</p>
            ) : attachmentTimeline.length === 0 ? (
              <p className="mt-4 text-sm text-neutral">No attachments yet.</p>
            ) : (
              <Timeline items={attachmentTimeline} />
            )}
          </Panel>
          <Panel>
            <p className="text-xs font-extrabold uppercase tracking-[0.16em] text-brand">Audit Timeline</p>
            {auditLoading ? (
              <p className="mt-4 text-sm text-neutral">Loading…</p>
            ) : auditTimeline.length === 0 ? (
              <p className="mt-4 text-sm text-neutral">No audit events yet.</p>
            ) : (
              <Timeline items={auditTimeline} />
            )}
          </Panel>
          <Panel>
            <p className="text-xs font-extrabold uppercase tracking-[0.16em] text-brand">Admin Actions</p>
            <div className="mt-4 grid gap-3">
              <button
                type="button"
                onClick={openEdit}
                className="rounded-panel bg-brand px-4 py-2 text-sm font-semibold text-white"
              >
                Edit Submission
              </button>
              <button
                type="button"
                onClick={() => setReopenOpen(true)}
                className="rounded-panel border border-line bg-panel px-4 py-2 text-sm font-semibold text-slate-700"
              >
                Reopen Submission
              </button>
            </div>
          </Panel>
        </div>
      </div>

      <EditDrawer
        isOpen={editOpen}
        onClose={() => setEditOpen(false)}
        title="Edit Submission"
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
            <span className="text-xs font-semibold uppercase tracking-[0.12em] text-neutral">Work Date</span>
            <input
              type="date"
              value={editWorkDate}
              onChange={(e) => setEditWorkDate(e.target.value)}
              className="rounded-md border border-line px-3 py-2 text-sm text-ink"
            />
          </label>
          <label className="grid gap-1">
            <span className="text-xs font-semibold uppercase tracking-[0.12em] text-neutral">Shift</span>
            <select
              value={editShift}
              onChange={(e) => setEditShift(e.target.value)}
              className="rounded-md border border-line px-3 py-2 text-sm text-ink"
            >
              <option value="AM">AM</option>
              <option value="PM">PM</option>
            </select>
          </label>
          <label className="grid gap-1">
            <span className="text-xs font-semibold uppercase tracking-[0.12em] text-neutral">Ticket Number</span>
            <input
              type="text"
              value={editTicket}
              onChange={(e) => setEditTicket(e.target.value)}
              className="rounded-md border border-line px-3 py-2 text-sm text-ink"
            />
          </label>
          <label className="grid gap-1">
            <span className="text-xs font-semibold uppercase tracking-[0.12em] text-neutral">Completed Grids</span>
            <input
              type="number"
              min={0}
              value={editCompleted}
              onChange={(e) => setEditCompleted(e.target.value)}
              className="rounded-md border border-line px-3 py-2 text-sm text-ink"
            />
          </label>
          <label className="grid gap-1">
            <span className="text-xs font-semibold uppercase tracking-[0.12em] text-neutral">Skipped Grids</span>
            <input
              type="number"
              min={0}
              value={editSkipped}
              onChange={(e) => setEditSkipped(e.target.value)}
              className="rounded-md border border-line px-3 py-2 text-sm text-ink"
            />
          </label>
          <label className="grid gap-1">
            <span className="text-xs font-semibold uppercase tracking-[0.12em] text-neutral">Force Tested Grids</span>
            <input
              type="number"
              min={0}
              value={editForceTested}
              onChange={(e) => setEditForceTested(e.target.value)}
              className="rounded-md border border-line px-3 py-2 text-sm text-ink"
            />
          </label>
        </div>
      </EditDrawer>

      <ConfirmationDialog
        isOpen={reopenOpen}
        onClose={() => setReopenOpen(false)}
        onConfirm={handleReopen}
        title="Reopen Submission"
        description="This will reopen the submission, allowing the tester to continue. Are you sure?"
        confirmLabel="Reopen"
        tone="warning"
        isLoading={reopenMutation.isPending}
      />
    </>
  );
}
