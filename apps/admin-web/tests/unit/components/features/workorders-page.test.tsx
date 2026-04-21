import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { WorkordersPage } from "@/components/features/workorders-page";

describe("WorkordersPage", () => {
  it("filters the table from URL search params on first render", () => {
    globalThis.__mockPathname = "/workorders";
    globalThis.__mockSearchParams = "region=NE_UP&status=ACTIVE";

    render(<WorkordersPage />);

    expect(screen.getByText("WO-NE-401")).toBeInTheDocument();
    expect(screen.queryByText("WO-CT-072")).not.toBeInTheDocument();
    expect(screen.getByText(/2 matching workorders/i)).toBeInTheDocument();
  });

  it("updates the URL when filters change", () => {
    globalThis.__mockPathname = "/workorders";
    globalThis.__mockSearchParams = "page=3&page_size=2";

    render(<WorkordersPage />);

    fireEvent.change(screen.getByLabelText("Region"), { target: { value: "CENTRAL" } });

    expect(globalThis.__mockRouterReplace).toHaveBeenCalledWith("/workorders?region=CENTRAL&page_size=2");
  });
});