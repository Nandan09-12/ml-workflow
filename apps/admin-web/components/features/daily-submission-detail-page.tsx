import { Alert } from "@/components/ui/alert";
import { DataTable } from "@/components/ui/data-table";
import { PageHeader } from "@/components/ui/page-header";
import { Panel } from "@/components/ui/panel";
import { ProgressBar } from "@/components/ui/progress-bar";
import { StatusBadge } from "@/components/ui/status-badge";
import { attachmentHistory, auditTimeline, submissions, workorders } from "@/lib/mock/data";
import { formatRegion } from "@/lib/format/labels";

interface DailySubmissionDetailPageProps {
  submissionId: string;
}

export function DailySubmissionDetailPage({ submissionId }: DailySubmissionDetailPageProps) {
  const submission = submissions.find((item) => item.id === submissionId) ?? submissions[0];
  const workorder = workorders.find((item) => item.workorderCode === submission.workorderCode) ?? workorders[0];

  return (
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
              <button type="button" className="rounded-panel bg-brand px-4 py-2 text-sm font-semibold text-white">Edit Submission</button>
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
            <div className="rounded-panel border border-line bg-slate-50 p-4"><span className="text-xs font-bold uppercase tracking-[0.12em] text-neutral">Completed</span><strong className="mt-2 block text-3xl font-semibold text-ink">{submission.completedGrids}</strong></div>
            <div className="rounded-panel border border-line bg-slate-50 p-4"><span className="text-xs font-bold uppercase tracking-[0.12em] text-neutral">Skipped</span><strong className="mt-2 block text-3xl font-semibold text-ink">{submission.skippedGrids}</strong></div>
            <div className="rounded-panel border border-line bg-slate-50 p-4"><span className="text-xs font-bold uppercase tracking-[0.12em] text-neutral">Force Tested</span><strong className="mt-2 block text-3xl font-semibold text-ink">{submission.forceTestedGrids}</strong></div>
            <div className="rounded-panel border border-line bg-slate-50 p-4"><span className="text-xs font-bold uppercase tracking-[0.12em] text-neutral">Started</span><strong className="mt-2 block text-lg font-semibold text-ink">{submission.startedAt}</strong></div>
            <div className="rounded-panel border border-line bg-slate-50 p-4"><span className="text-xs font-bold uppercase tracking-[0.12em] text-neutral">Ended</span><strong className="mt-2 block text-lg font-semibold text-ink">{submission.endedAt ?? "In progress"}</strong></div>
          </div>
        </Panel>
        <Panel>
          <div className="mb-4 flex items-start justify-between gap-4">
            <div>
              <p className="text-xs font-extrabold uppercase tracking-[0.16em] text-brand">Parent Workorder</p>
              <h2 className="mt-1 text-xl font-semibold text-ink">{workorder.workorderCode}</h2>
            </div>
            <StatusBadge value={workorder.status} />
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <dl className="grid gap-3 text-sm text-neutral">
              <div className="flex justify-between gap-4 border-b border-line pb-3"><dt>Region</dt><dd className="font-semibold text-ink">{formatRegion(workorder.region)}</dd></div>
              <div className="flex justify-between gap-4 border-b border-line pb-3"><dt>Total Grids</dt><dd className="font-semibold text-ink">{workorder.totalGrids}</dd></div>
              <div className="flex justify-between gap-4 border-b border-line pb-3"><dt>Aggregate Completed</dt><dd className="font-semibold text-ink">{workorder.completedGrids}</dd></div>
              <div className="flex justify-between gap-4 border-b border-line pb-3"><dt>Aggregate Skipped</dt><dd className="font-semibold text-ink">{workorder.skippedGrids}</dd></div>
              <div className="flex justify-between gap-4"><dt>Remaining Grids</dt><dd className="font-semibold text-ink">{workorder.remainingGrids}</dd></div>
            </dl>
            <ProgressBar value={workorder.progressPercent} caption={`${workorder.progressPercent}% complete across all child daily submissions`} />
          </div>
        </Panel>
      </div>
      <div className="space-y-6">
        <Panel>
          <p className="text-xs font-extrabold uppercase tracking-[0.16em] text-brand">Active Attachment</p>
          <div className="mt-4">
            {submission.fileSubmissionPending ? (
              <p className="text-sm text-neutral">No active file yet. Admin detail UI is prepared for the attachment source once the backend contract is confirmed.</p>
            ) : (
              <div className="space-y-2 text-sm text-neutral">
                <p><strong className="text-ink">closeout.csv</strong></p>
                <p>CSV · 1.2 MB · uploaded by {submission.testerName}</p>
                <button type="button" className="rounded-panel border border-line bg-panel px-4 py-2 font-semibold text-slate-700">Download Attachment</button>
              </div>
            )}
          </div>
        </Panel>
        <Panel>
          <p className="text-xs font-extrabold uppercase tracking-[0.16em] text-brand">Attachment History</p>
          <ol className="mt-4 grid gap-4">
            {attachmentHistory.map((event) => (
              <li key={event.id} className="border-l-2 border-line pl-4">
                <strong className="block text-sm font-semibold text-ink">{event.title}</strong>
                <span className="mt-1 block text-sm text-neutral">{event.detail}</span>
              </li>
            ))}
          </ol>
        </Panel>
        <Panel>
          <p className="text-xs font-extrabold uppercase tracking-[0.16em] text-brand">Audit Timeline</p>
          <ol className="mt-4 grid gap-4">
            {auditTimeline.map((event) => (
              <li key={event.id} className="border-l-2 border-line pl-4">
                <strong className="block text-sm font-semibold text-ink">{event.title}</strong>
                <span className="mt-1 block text-sm text-neutral">{event.detail}</span>
              </li>
            ))}
          </ol>
        </Panel>
        <Panel>
          <p className="text-xs font-extrabold uppercase tracking-[0.16em] text-brand">Admin Actions</p>
          <div className="mt-4 grid gap-3">
            <button type="button" className="rounded-panel bg-brand px-4 py-2 text-sm font-semibold text-white">Edit Submission</button>
            <button type="button" className="rounded-panel border border-line bg-panel px-4 py-2 text-sm font-semibold text-slate-700">Reopen Submission</button>
          </div>
        </Panel>
      </div>
    </div>
  );
}
