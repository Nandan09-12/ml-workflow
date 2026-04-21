import { Suspense } from "react";
import { UsersPage } from "@/components/features/users-page";

export default function UsersRoute() {
  return (
    <Suspense fallback={<div className="rounded-panel border border-line bg-panel p-6 text-sm text-neutral">Loading users...</div>}>
      <UsersPage />
    </Suspense>
  );
}
