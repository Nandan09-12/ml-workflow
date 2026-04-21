interface FilterDateInputProps {
  label: string;
  value: string;
  onChange: (nextValue: string) => void;
}

export function FilterDateInput({ label, value, onChange }: FilterDateInputProps) {
  return (
    <label className="grid gap-1 text-xs font-bold uppercase tracking-[0.12em] text-neutral">
      <span>{label}</span>
      <input
        type="date"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="rounded-panel border border-line bg-panel px-3 py-2 text-sm font-medium text-ink"
      />
    </label>
  );
}