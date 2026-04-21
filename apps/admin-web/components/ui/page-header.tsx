import type * as React from "react";

interface PageHeaderProps {
  kicker: string;
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
}

export function PageHeader({ kicker, title, subtitle, actions }: PageHeaderProps) {
  return (
    <div className="mb-5 flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
      <div>
        <p className="text-xs font-extrabold uppercase tracking-[0.18em] text-brand">{kicker}</p>
        <h1 className="mt-1 text-3xl font-semibold tracking-tight text-ink">{title}</h1>
        {subtitle ? <p className="mt-2 max-w-3xl text-sm text-neutral">{subtitle}</p> : null}
      </div>
      {actions ? <div className="flex items-center gap-3">{actions}</div> : null}
    </div>
  );
}
