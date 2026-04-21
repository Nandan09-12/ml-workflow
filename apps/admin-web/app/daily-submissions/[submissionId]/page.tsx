import { DailySubmissionDetailPage } from "@/components/features/daily-submission-detail-page";

interface DailySubmissionDetailRouteProps {
  params: Promise<{ submissionId: string }>;
}

export default async function DailySubmissionDetailRoute({ params }: DailySubmissionDetailRouteProps) {
  const { submissionId } = await params;
  return <DailySubmissionDetailPage submissionId={submissionId} />;
}
