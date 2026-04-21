import type { ReactNode } from "react";

interface DataTableProps {
  headers: string[];
  children: ReactNode;
}

export function DataTable({ headers, children }: DataTableProps) {
  return (
    <div className="overflow-x-auto rounded-panel border border-line">
      <table className="min-w-full border-collapse text-left">
        <thead className="bg-slate-50 text-xs font-bold uppercase tracking-[0.12em] text-neutral">
          <tr>
            {headers.map((header, index) => (
              <th key={`${header}-${index}`} className="border-b border-line px-4 py-3">{header}</th>
            ))}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}
