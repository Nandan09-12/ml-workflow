import type { ReactNode } from "react";
import { clsx } from "clsx";

interface AlertProps {
  title: string;
  children: ReactNode;
  tone?: "info" | "warning" | "danger";
}

const toneMap = {
  info: "border-brand/25 bg-brand-soft",
  warning: "border-warning/30 bg-warning-soft",
  danger: "border-danger/30 bg-danger-soft",
};

export function Alert({ title, children, tone = "info" }: AlertProps) {
  return (
    <div className={clsx("rounded-panel border p-4", toneMap[tone])}>
      <strong className="block text-sm font-semibold text-ink">{title}</strong>
      <div className="mt-1 text-sm text-neutral">{children}</div>
    </div>
  );
}
