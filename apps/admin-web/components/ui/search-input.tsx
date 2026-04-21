interface SearchInputProps {
  label: string;
  value: string;
  placeholder: string;
  onChange: (nextValue: string) => void;
}

export function SearchInput({ label, value, placeholder, onChange }: SearchInputProps) {
  return (
    <label className="grid gap-1 text-xs font-bold uppercase tracking-[0.12em] text-neutral">
      <span>{label}</span>
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        className="rounded-panel border border-line bg-panel px-3 py-2 text-sm font-medium text-ink placeholder:text-neutral"
      />
    </label>
  );
}