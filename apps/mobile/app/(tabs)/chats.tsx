import { EmptyStateCard } from "../../src/components/EmptyStateCard";
import { ScreenShell } from "../../src/components/ScreenShell";

export default function ChatsScreen() {
  return (
    <ScreenShell insetBottom padded showBackButton={false}>
      <EmptyStateCard
        title="Chats"
        description="Team conversations can land here once the backend contract for messages is ready."
      />
    </ScreenShell>
  );
}
