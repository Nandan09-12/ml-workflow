import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ConfirmationDialog } from "@/components/ui/confirmation-dialog";

describe("ConfirmationDialog", () => {
  it("closes on Escape when open and not loading", () => {
    const onClose = vi.fn();

    render(
      <ConfirmationDialog
        isOpen
        onClose={onClose}
        onConfirm={vi.fn()}
        title="Suspend User"
        description="Suspend this user?"
        isLoading={false}
      />,
    );

    fireEvent.keyDown(document, { key: "Escape" });

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("does not close on Escape while loading", () => {
    const onClose = vi.fn();

    render(
      <ConfirmationDialog
        isOpen
        onClose={onClose}
        onConfirm={vi.fn()}
        title="Suspend User"
        description="Suspend this user?"
        isLoading
      />,
    );

    fireEvent.keyDown(document, { key: "Escape" });

    expect(onClose).not.toHaveBeenCalled();
  });

  it("focuses the first interactive element when opened", () => {
    render(
      <ConfirmationDialog
        isOpen
        onClose={vi.fn()}
        onConfirm={vi.fn()}
        title="Suspend User"
        description="Suspend this user?"
        isLoading={false}
      />,
    );

    expect(screen.getByRole("button", { name: "Cancel" })).toHaveFocus();
  });
});