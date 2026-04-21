import { clsx } from "clsx";

interface StatusBadgeProps {
  value: string;
}

const toneMap: Record<string, string> = {
  IN_PROGRESS: "bg-brand-soft text-brand",
  ACTIVE: "bg-brand-soft text-brand",
  ADMIN: "bg-brand-soft text-brand",
  DRIVE_TESTER: "bg-brand-soft text-brand",
  CHECKED_OUT: "bg-warning-soft text-warning",
  FILE_PENDING: "bg-warning-soft text-warning",
  PENDING_APPROVAL: "bg-warning-soft text-warning",
  COMPLETED: "bg-success-soft text-success",
  APPROVED: "bg-success-soft text-success",
  ATTACHED: "bg-success-soft text-success",
  REJECTED: "bg-danger-soft text-danger",
  SUSPENDED: "bg-danger-soft text-danger",
  NOT_REQUIRED: "bg-neutral-soft text-neutral",
};

export function StatusBadge({ value }: StatusBadgeProps) {
  return (
    <span className={clsx("inline-flex min-h-7 items-center rounded-full px-3 text-[11px] font-extrabold uppercase tracking-[0.12em]", toneMap[value] ?? "bg-neutral-soft text-neutral")}>
      {value.replaceAll("_", " ")}
    </span>
  );
}
