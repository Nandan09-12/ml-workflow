import { Stack, useRouter, useSegments } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { useEffect } from "react";

import { useAuth } from "../src/auth/AuthContext";
import { AppProviders } from "../src/providers/AppProviders";

function RootNavigator() {
  const { authStatus, isHydrating } = useAuth();
  const router = useRouter();
  const segments = useSegments();

  useEffect(() => {
    if (isHydrating) {
      return;
    }

    const atRoot = segments[0] == null;
    const inAuthGroup = segments[0] === "(auth)";
    const inTabsGroup = segments[0] === "(tabs)";

    if (authStatus === "SIGNED_OUT" && !inAuthGroup && !atRoot) {
      router.replace("/(auth)/login");
      return;
    }

    if (authStatus === "PENDING_APPROVAL" && segments[0] !== "pending-approval") {
      router.replace("/pending-approval");
      return;
    }

    if (authStatus === "APPROVED" && !inTabsGroup) {
      router.replace("/(tabs)/projects");
    }
  }, [authStatus, isHydrating, router, segments]);

  return <Stack screenOptions={{ headerShown: false }} />;
}

export default function RootLayout() {
  return (
    <AppProviders>
      <StatusBar style="dark" />
      <RootNavigator />
    </AppProviders>
  );
}
