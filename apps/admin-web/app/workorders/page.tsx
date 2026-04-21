import { Suspense } from "react";
import { WorkordersPage } from "@/components/features/workorders-page";

export default function WorkordersRoute() {
  return (
    <Suspense fallback={<div className="rounded-panel border border-line bg-panel p-6 text-sm text-neutral">Loading workorders...</div>}>
      <WorkordersPage />
    </Suspense>
  );
}
