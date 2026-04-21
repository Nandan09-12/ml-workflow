interface PaginationProps {
  page: number;
  pageSize: number;
  totalItems: number;
  totalPages: number;
  onPageChange: (nextPage: number) => void;
  onPageSizeChange: (nextPageSize: number) => void;
}

export function Pagination({
  page,
  pageSize,
  totalItems,
  totalPages,
  onPageChange,
  onPageSizeChange,
}: PaginationProps) {
  const startItem = totalItems === 0 ? 0 : (page - 1) * pageSize + 1;
  const endItem = totalItems === 0 ? 0 : Math.min(page * pageSize, totalItems);

  return (
    <div className="flex flex-col gap-3 border-t border-line pt-4 md:flex-row md:items-center md:justify-between">
      <p className="text-sm text-neutral">
        Showing <strong className="text-ink">{startItem}-{endItem}</strong> of <strong className="text-ink">{totalItems}</strong>
      </p>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <label className="flex items-center gap-2 text-xs font-bold uppercase tracking-[0.12em] text-neutral">
          <span>Page Size</span>
          <select
            value={String(pageSize)}
            onChange={(event) => onPageSizeChange(Number(event.target.value))}
            className="rounded-panel border border-line bg-panel px-3 py-2 text-sm font-medium text-ink"
          >
            <option value="2">2</option>
            <option value="5">5</option>
            <option value="20">20</option>
          </select>
        </label>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
            className="rounded-panel border border-line bg-panel px-4 py-2 text-sm font-semibold text-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Previous
          </button>
          <span className="text-sm font-semibold text-ink">
            Page {page} of {totalPages}
          </span>
          <button
            type="button"
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages}
            className="rounded-panel border border-line bg-panel px-4 py-2 text-sm font-semibold text-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}