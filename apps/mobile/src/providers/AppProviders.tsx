import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { PropsWithChildren, useState } from "react";
import { SafeAreaProvider } from "react-native-safe-area-context";

import { AuthProvider } from "../auth/AuthProvider";
import { ExpensesProvider } from "../expenses/ExpensesProvider";
import { MileageProvider } from "../mileage/MileageProvider";
import { SubmissionsProvider } from "../submissions/SubmissionsProvider";

export function AppProviders({ children }: PropsWithChildren) {
  const [queryClient] = useState(() => new QueryClient());

  return (
    <SafeAreaProvider>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <SubmissionsProvider>
            <ExpensesProvider>
              <MileageProvider>{children}</MileageProvider>
            </ExpensesProvider>
          </SubmissionsProvider>
        </AuthProvider>
      </QueryClientProvider>
    </SafeAreaProvider>
  );
}
