"use client";

import { useState } from "react";
import { Alert } from "@/components/ui/alert";
import { ConfirmationDialog } from "@/components/ui/confirmation-dialog";
import { PageHeader } from "@/components/ui/page-header";
import { Panel } from "@/components/ui/panel";
import { StatusBadge } from "@/components/ui/status-badge";
import { usePendingUsers } from "@/lib/hooks/use-pending-users";
import { useApproveUser } from "@/lib/hooks/use-approve-user";
import { useRejectUser } from "@/lib/hooks/use-reject-user";

type PendingAction = { userId: string; action: "approve" | "reject"; name: string } | null;

export function PendingUsersPage() {
  const { items, isLoading, isError, error, isFallback } = usePendingUsers();
  const approveMutation = useApproveUser();
  const rejectMutation = useRejectUser();
  const [pendingAction, setPendingAction] = useState<PendingAction>(null);

  const isConfirming = approveMutation.isPending || rejectMutation.isPending;

  function handleConfirm() {
    if (!pendingAction) return;
    const mutation = pendingAction.action === "approve" ? approveMutation : rejectMutation;
    mutation.mutate(pendingAction.userId, { onSuccess: () => setPendingAction(null) });
  }

  return (
    <div className="space-y-6">
      <PageHeader kicker="Approval Queue" title="Pending Users" subtitle="Role requests awaiting admin approval or rejection. Admin requests should feel higher-risk than drive-tester approvals." />
      {isFallback && (
        <Alert title="Using cached data" tone="info">
          Live pending users data is temporarily unavailable. Showing cached data.
        </Alert>
      )}
      {isError && !isFallback && (
        <Alert title="Error loading pending users" tone="danger">
          {error instanceof Error ? error.message : "Failed to load pending users"}
        </Alert>
      )}
      {(approveMutation.isError || rejectMutation.isError) && (
        <Alert title="Action failed" tone="danger">
          {((approveMutation.error ?? rejectMutation.error) instanceof Error
            ? (approveMutation.error ?? rejectMutation.error) as Error
            : null
          )?.message ?? "Unknown error"}
        </Alert>
      )}
      {isLoading ? (
        <div className="flex items-center justify-center py-12" role="status">
          <div className="animate-spin rounded-full border-4 border-line border-t-brand h-8 w-8" />
        </div>
      ) : (
        <div className="grid gap-4 xl:grid-cols-2">
          {items.map((user) => (
            <Panel key={user.id}>
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h2 className="text-xl font-semibold text-ink">{user.fullName}</h2>
                  <p className="mt-1 text-sm text-neutral">{user.email}</p>
                </div>
                <StatusBadge value={user.requestedRole} />
              </div>
              <p className="mt-2 text-xs font-bold uppercase tracking-[0.12em] text-neutral">Requested {user.createdAt}</p>
              <div className="mt-5 flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={() => setPendingAction({ userId: user.id, action: "approve", name: user.fullName })}
                  className="rounded-panel bg-brand px-4 py-2 text-sm font-semibold text-white"
                >
                  Approve
                </button>
                <button
                  type="button"
                  onClick={() => setPendingAction({ userId: user.id, action: "reject", name: user.fullName })}
                  className="rounded-panel bg-danger-soft px-4 py-2 text-sm font-semibold text-danger"
                >
                  Reject
                </button>
              </div>
            </Panel>
          ))}
        </div>
      )}

      <ConfirmationDialog
        isOpen={pendingAction !== null}
        onClose={() => setPendingAction(null)}
        onConfirm={handleConfirm}
        title={pendingAction?.action === "approve" ? "Approve User" : "Reject User"}
        description={
          pendingAction?.action === "approve"
            ? `Approve ${pendingAction.name}? They will gain access based on their requested role.`
            : `Reject ${pendingAction?.name ?? "this user"}? They will not be granted access.`
        }
        confirmLabel={pendingAction?.action === "approve" ? "Approve" : "Reject"}
        tone={pendingAction?.action === "approve" ? "warning" : "danger"}
        isLoading={isConfirming}
      />
    </div>
  );
}
