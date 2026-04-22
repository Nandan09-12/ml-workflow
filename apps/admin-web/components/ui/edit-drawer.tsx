"use client";

interface EditDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  onSave: () => void;
  isLoading: boolean;
}

export function EditDrawer({
  isOpen,
  onClose,
  title,
  children,
  onSave,
  isLoading,
}: EditDrawerProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end" role="dialog" aria-modal="true" aria-labelledby="edit-drawer-title">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/40"
        onClick={isLoading ? undefined : onClose}
      />

      {/* Drawer panel */}
      <div className="relative z-10 flex h-full w-full max-w-lg flex-col bg-white shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-line px-6 py-4">
          <h2 id="edit-drawer-title" className="text-base font-semibold text-ink">
            {title}
          </h2>
          <button
            type="button"
            onClick={onClose}
            disabled={isLoading}
            aria-label="Close"
            className="text-neutral hover:text-ink disabled:opacity-50"
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-6 py-4">{children}</div>

        {/* Footer */}
        <div className="flex justify-end gap-3 border-t border-line px-6 py-4">
          <button
            type="button"
            onClick={onClose}
            disabled={isLoading}
            className="rounded-md border border-line px-4 py-2 text-sm font-medium text-ink hover:bg-slate-50 disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onSave}
            disabled={isLoading}
            className="rounded-md bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand/90 disabled:opacity-50"
          >
            {isLoading ? "Saving…" : "Save"}
          </button>
        </div>
      </div>
    </div>
  );
}
