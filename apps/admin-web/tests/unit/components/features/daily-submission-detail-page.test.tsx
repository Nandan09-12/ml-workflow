import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { DailySubmissionDetailPage } from "@/components/features/daily-submission-detail-page";

describe("DailySubmissionDetailPage", () => {
  it("shows the file pending warning for checked-out submissions without an active file", () => {
    render(<DailySubmissionDetailPage submissionId="sub-1" />);

    expect(screen.getByText("Closeout file is missing")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Download Attachment" })).not.toBeInTheDocument();
  });

  it("shows attachment actions for submissions with an active file", () => {
    render(<DailySubmissionDetailPage submissionId="sub-2" />);

    expect(screen.queryByText("Closeout file is missing")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Download Attachment" })).toBeInTheDocument();
    expect(screen.getByText("closeout.csv")).toBeInTheDocument();
  });

  it("falls back to the first mock submission when the requested id does not exist", () => {
    render(<DailySubmissionDetailPage submissionId="missing-submission" />);

    expect(screen.getByRole("heading", { name: "Priya Shah / WO-SF-118" })).toBeInTheDocument();
  });

  it("renders related parent workorder summary values", () => {
    render(<DailySubmissionDetailPage submissionId="sub-2" />);

    expect(screen.getByText("Parent Workorder")).toBeInTheDocument();
    expect(screen.getByText("WO-NE-401")).toBeInTheDocument();
    expect(screen.getByText("NE-UP")).toBeInTheDocument();
    expect(screen.getByText("68% complete across all child daily submissions")).toBeInTheDocument();
  });
});