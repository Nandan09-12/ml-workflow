import { EmptyStateCard } from "../../src/components/EmptyStateCard";
import { ScreenShell } from "../../src/components/ScreenShell";

export default function OfflineScreen() {
  return (
    <ScreenShell insetBottom padded>
      <EmptyStateCard
        title="Offline Tickets"
        description="Offline submission sync can be layered in here after we define the local storage and sync queue."
      />
    </ScreenShell>
  );
}
