import { WorkorderDetailPage } from "@/components/features/workorder-detail-page";

interface WorkorderDetailRouteProps {
  params: Promise<{ workorderId: string }>;
}

export default async function WorkorderDetailRoute({ params }: WorkorderDetailRouteProps) {
  const { workorderId } = await params;
  return <WorkorderDetailPage workorderId={workorderId} />;
}
