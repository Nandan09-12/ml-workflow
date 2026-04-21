import Link from "next/link";

interface MetricCardProps {
  label: string;
  value: string;
  detail: string;
  tone?: "brand" | "success" | "warning" | "danger";
  href?: string;
}

const toneStyles = {
  brand: "border-l-brand",
  success: "border-l-success",
  warning: "border-l-warning",
  danger: "border-l-danger",
};

export function MetricCard({ label, value, detail, tone = "brand", href }: MetricCardProps) {
  const content = (
    <article className={`rounded-panel border border-line border-l-4 bg-slate-50 p-4 transition hover:border-brand ${toneStyles[tone]}`}>
      <span className="text-xs font-bold uppercase tracking-[0.12em] text-neutral">{label}</span>
      <strong className="mt-3 block text-4xl font-semibold tracking-tight text-ink">{value}</strong>
      <span className="mt-3 block text-sm text-neutral">{detail}</span>
    </article>
  );

  if (!href) return content;

  return <Link href={href}>{content}</Link>;
}
