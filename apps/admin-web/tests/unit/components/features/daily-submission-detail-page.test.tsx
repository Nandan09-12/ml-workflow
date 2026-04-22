import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { DailySubmissionDetailPage } from "@/components/features/daily-submission-detail-page";
import { submissions } from "@/lib/mock/data";

const sub1 = submissions.find((s) => s.id === "sub-1")!;
const sub2 = submissions.find((s) => s.id === "sub-2")!;

vi.mock("@/lib/hooks/use-admin-submission", () => ({
  useAdminSubmission: vi.fn((id: string) => {
    const found = submissions.find((s) => s.id === id) ?? submissions[0];
    return { submission: found, isLoading: false, isError: false, error: null, isFallback: false };
  }),
}));

vi.mock("@/lib/hooks/use-submission-audit", () => ({
  useSubmissionAudit: vi.fn(() => ({ items: [], count: 0, isLoading: false, isError: false, error: null })),
}));

vi.mock("@/lib/hooks/use-submission-attachment-history", () => ({
  useSubmissionAttachmentHistory: vi.fn(() => ({ items: [], count: 0, isLoading: false, isError: false, error: null })),
}));

vi.mock("@/lib/hooks/use-edit-submission", () => ({
  useEditSubmission: vi.fn(() => ({ mutate: vi.fn(), isPending: false, isError: false, error: null })),
}));

vi.mock("@/lib/hooks/use-reopen-submission", () => ({
  useReopenSubmission: vi.fn(() => ({ mutate: vi.fn(), isPending: false, isError: false, error: null })),
}));

vi.mock("@/lib/hooks/use-attachment-download", () => ({
  useAttachmentDownload: vi.fn(() => ({
    mutate: vi.fn(),
    isPending: false,
    isError: false,
    error: null,
  })),
}));

describe("DailySubmissionDetailPage", () => {
  it("shows the file pending warning for checked-out submissions without an active file", () => {
    render(<DailySubmissionDetailPage submissionId={sub1.id} />);

    expect(screen.getByText("Closeout file is missing")).toBeInTheDocument();
  });

  it("shows no file-pending warning for submissions with an active file", () => {
    render(<DailySubmissionDetailPage submissionId={sub2.id} />);

    expect(screen.queryByText("Closeout file is missing")).not.toBeInTheDocument();
  });

  it("falls back to the first mock submission when the requested id does not exist", () => {
    render(<DailySubmissionDetailPage submissionId="missing-submission" />);

    expect(screen.getByRole("heading", { name: "Priya Shah / WO-SF-118" })).toBeInTheDocument();
  });

  it("renders parent workorder section", () => {
    render(<DailySubmissionDetailPage submissionId={sub2.id} />);

    expect(screen.getByText("Parent Workorder")).toBeInTheDocument();
    expect(screen.getByText("WO-NE-401")).toBeInTheDocument();
    expect(screen.getByText("NE-UP")).toBeInTheDocument();
  });
});
