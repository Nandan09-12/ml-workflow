import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { WorkordersPage } from "@/components/features/workorders-page";
import { workorders } from "@/lib/mock/data";

const mockUseAdminWorkorders = vi.fn();
vi.mock("@/lib/hooks/use-admin-workorders", () => ({
  useAdminWorkorders: (...args: unknown[]) => mockUseAdminWorkorders(...args),
}));

const defaultHookResult = {
  items: workorders,
  pagination: { page: 1, pageSize: 20, total: workorders.length, totalPages: 1 },
  isLoading: false,
  isError: false,
  error: null,
  isFallback: false,
};

describe("WorkordersPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseAdminWorkorders.mockReturnValue(defaultHookResult);
  });

  it("passes filter params to the hook from URL search params", () => {
    globalThis.__mockPathname = "/workorders";
    globalThis.__mockSearchParams = "region=NE_UP&status=ACTIVE";

    render(<WorkordersPage />);

    expect(mockUseAdminWorkorders).toHaveBeenCalledWith(
      expect.objectContaining({ region: "NE_UP", status: "ACTIVE" }),
    );
  });

  it("renders hook items in the table", () => {
    globalThis.__mockPathname = "/workorders";
    globalThis.__mockSearchParams = "";

    render(<WorkordersPage />);

    expect(screen.getByText(workorders[0].workorderCode)).toBeInTheDocument();
  });

  it("updates the URL when filters change", () => {
    globalThis.__mockPathname = "/workorders";
    globalThis.__mockSearchParams = "page=3&page_size=2";

    render(<WorkordersPage />);

    fireEvent.change(screen.getByLabelText("Region"), { target: { value: "CENTRAL" } });

    expect(globalThis.__mockRouterReplace).toHaveBeenCalledWith("/workorders?region=CENTRAL&page_size=2");
  });
});
