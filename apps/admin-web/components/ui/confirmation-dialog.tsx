"use client";

import { clsx } from "clsx";

interface ConfirmationDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  description: string;
  confirmLabel?: string;
  cancelLabel?: string;
  tone?: "danger" | "warning";
  isLoading: boolean;
}

export function ConfirmationDialog({
  isOpen,
  onClose,
  onConfirm,
  title,
  description,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  tone = "danger",
  isLoading,
}: ConfirmationDialogProps) {
  if (!isOpen) return null;

  const confirmBtnClass =
    tone === "danger"
      ? "bg-danger text-white hover:bg-danger/90"
      : "bg-warning text-white hover:bg-warning/90";

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirmation-dialog-title"
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/40"
        onClick={isLoading ? undefined : onClose}
      />

      {/* Panel */}
      <div className="relative z-10 w-full max-w-md rounded-panel border border-line bg-white p-6 shadow-xl">
        <h2
          id="confirmation-dialog-title"
          className="text-base font-semibold text-ink"
        >
          {title}
        </h2>
        <p className="mt-2 text-sm text-neutral">{description}</p>

        <div className="mt-6 flex justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            disabled={isLoading}
            className="rounded-md border border-line px-4 py-2 text-sm font-medium text-ink hover:bg-slate-50 disabled:opacity-50"
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={isLoading}
            className={clsx(
              "rounded-md px-4 py-2 text-sm font-medium disabled:opacity-50",
              confirmBtnClass,
            )}
          >
            {isLoading ? "Loading…" : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
