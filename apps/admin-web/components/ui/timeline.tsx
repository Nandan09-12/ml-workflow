interface TimelineItem {
  id: string;
  title: string;
  detail: string;
}

interface TimelineProps {
  items: TimelineItem[];
}

export function Timeline({ items }: TimelineProps) {
  return (
    <ol className="mt-4 grid gap-4">
      {items.map((item) => (
        <li key={item.id} className="border-l-2 border-line pl-4">
          <strong className="block text-sm font-semibold text-ink">{item.title}</strong>
          <span className="mt-1 block text-sm text-neutral">{item.detail}</span>
        </li>
      ))}
    </ol>
  );
}