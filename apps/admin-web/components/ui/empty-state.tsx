interface EmptyStateProps {
  title: string;
  description: string;
}

export function EmptyState({ title, description }: EmptyStateProps) {
  return (
    <div className="rounded-panel border border-dashed border-line bg-slate-50 p-5">
      <strong className="block text-sm font-semibold text-ink">{title}</strong>
      <p className="mt-2 text-sm text-neutral">{description}</p>
    </div>
  );
}
