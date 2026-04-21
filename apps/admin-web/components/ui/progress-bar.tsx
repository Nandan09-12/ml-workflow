interface ProgressBarProps {
  value: number;
  caption?: string;
}

export function ProgressBar({ value, caption }: ProgressBarProps) {
  return (
    <div>
      <div className="h-3 overflow-hidden rounded-full bg-slate-200">
        <div className="h-full rounded-full bg-gradient-to-r from-brand to-cyan-600" style={{ width: `${value}%` }} />
      </div>
      {caption ? <p className="mt-2 text-sm text-neutral">{caption}</p> : null}
    </div>
  );
}
