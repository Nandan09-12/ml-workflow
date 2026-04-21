interface ErrorStateProps {
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
}

export function ErrorState({ title, description, actionLabel, onAction }: ErrorStateProps) {
  return (
    <div className="rounded-panel border border-danger bg-danger-soft p-5">
      <strong className="block text-sm font-semibold text-danger">{title}</strong>
      <p className="mt-2 text-sm text-slate-700">{description}</p>
      {actionLabel && onAction ? (
        <button
          type="button"
          onClick={onAction}
          className="mt-4 rounded-panel border border-danger bg-white px-4 py-2 text-sm font-semibold text-danger"
        >
          {actionLabel}
        </button>
      ) : null}
    </div>
  );
}