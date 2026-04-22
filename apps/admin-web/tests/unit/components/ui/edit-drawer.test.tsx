import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { EditDrawer } from "@/components/ui/edit-drawer";

describe("EditDrawer", () => {
  it("closes on Escape when open and not loading", () => {
    const onClose = vi.fn();

    render(
      <EditDrawer
        isOpen
        onClose={onClose}
        onSave={vi.fn()}
        title="Edit Submission"
        isLoading={false}
      >
        <input aria-label="Work Date" />
      </EditDrawer>,
    );

    fireEvent.keyDown(document, { key: "Escape" });

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("does not close on Escape while loading", () => {
    const onClose = vi.fn();

    render(
      <EditDrawer
        isOpen
        onClose={onClose}
        onSave={vi.fn()}
        title="Edit Submission"
        isLoading
      >
        <input aria-label="Work Date" />
      </EditDrawer>,
    );

    fireEvent.keyDown(document, { key: "Escape" });

    expect(onClose).not.toHaveBeenCalled();
  });

  it("focuses the first interactive element when opened", () => {
    render(
      <EditDrawer
        isOpen
        onClose={vi.fn()}
        onSave={vi.fn()}
        title="Edit Submission"
        isLoading={false}
      >
        <input aria-label="Work Date" />
      </EditDrawer>,
    );

    expect(screen.getByLabelText("Close")).toHaveFocus();
  });
});