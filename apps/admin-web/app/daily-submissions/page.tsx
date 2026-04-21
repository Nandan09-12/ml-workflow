import { Suspense } from "react";
import { DailySubmissionsPage } from "@/components/features/daily-submissions-page";

export default function DailySubmissionsRoute() {
  return (
    <Suspense fallback={<div className="rounded-panel border border-line bg-panel p-6 text-sm text-neutral">Loading daily submissions...</div>}>
      <DailySubmissionsPage />
    </Suspense>
  );
}
