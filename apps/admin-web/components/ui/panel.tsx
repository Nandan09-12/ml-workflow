import type { ReactNode } from "react";
import { clsx } from "clsx";

interface PanelProps {
  children: ReactNode;
  className?: string;
}

export function Panel({ children, className }: PanelProps) {
  return <section className={clsx("rounded-panel border border-line bg-panel p-5 shadow-panel", className)}>{children}</section>;
}
