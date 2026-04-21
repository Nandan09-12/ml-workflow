import type { ReactNode } from "react";

interface TableToolbarProps {
  summary: string;
  actions?: ReactNode;
}

export function TableToolbar({ summary, actions }: TableToolbarProps) {
  return (
    <div className="mb-4 flex flex-col gap-3 border-b border-line pb-4 md:flex-row md:items-center md:justify-between">
      <p className="text-sm text-neutral">{summary}</p>
      {actions ? <div className="flex items-center gap-3">{actions}</div> : null}
    </div>
  );
}