interface LoadingStateProps {
  title?: string;
  description?: string;
}

export function LoadingState({
  title = "Loading",
  description = "Fetching the latest admin view.",
}: LoadingStateProps) {
  return (
    <div className="rounded-panel border border-line bg-slate-50 p-5">
      <div className="flex items-center gap-3">
        <span className="h-3 w-3 rounded-full bg-brand" aria-hidden="true" />
        <strong className="text-sm font-semibold text-ink">{title}</strong>
      </div>
      <p className="mt-2 text-sm text-neutral">{description}</p>
    </div>
  );
}