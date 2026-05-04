import { EmptyStateCard } from "../../src/components/EmptyStateCard";
import { ScreenShell } from "../../src/components/ScreenShell";

export default function NotificationsScreen() {
  return (
    <ScreenShell insetBottom padded showBackButton={false}>
      <EmptyStateCard
        title="Notifications"
        description="Approval alerts, submission reminders, and backend status notifications can live here."
      />
    </ScreenShell>
  );
}
