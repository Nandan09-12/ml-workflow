interface DefinitionListItem {
  term: string;
  description: string | number;
}

interface DefinitionListProps {
  items: DefinitionListItem[];
}

export function DefinitionList({ items }: DefinitionListProps) {
  return (
    <dl className="grid gap-3 text-sm text-neutral">
      {items.map((item, index) => (
        <div
          key={item.term}
          className={index < items.length - 1 ? "flex justify-between gap-4 border-b border-line pb-3" : "flex justify-between gap-4"}
        >
          <dt>{item.term}</dt>
          <dd className="text-right font-semibold text-ink">{item.description}</dd>
        </div>
      ))}
    </dl>
  );
}