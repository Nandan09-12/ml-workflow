import type { Href } from "expo-router";
import { useRouter } from "expo-router";
import type { PropsWithChildren } from "react";
import { ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { BackButton } from "./BackButton";
import { colors, spacing } from "../theme/tokens";

type ScreenShellProps = PropsWithChildren<{
  backFallbackHref?: Href;
  insetBottom?: boolean;
  padded?: boolean;
  scrollable?: boolean;
  showBackButton?: boolean;
}>;

export function ScreenShell({
  backFallbackHref,
  children,
  insetBottom = false,
  padded = true,
  scrollable = true,
  showBackButton = true,
}: ScreenShellProps) {
  const router = useRouter();
  const shouldRenderBackButton = showBackButton && (router.canGoBack() || !!backFallbackHref);

  return (
    <SafeAreaView edges={insetBottom ? ["top", "bottom"] : ["top"]} style={styles.safeArea}>
      {shouldRenderBackButton ? (
        <View style={[styles.backRow, padded && styles.padded]}>
          <BackButton fallbackHref={backFallbackHref} />
        </View>
      ) : null}
      {scrollable ? (
        <ScrollView
          contentContainerStyle={[styles.scrollContent, padded && styles.padded]}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
          style={styles.content}
        >
          {children}
        </ScrollView>
      ) : (
        <View style={[styles.content, padded && styles.padded]}>{children}</View>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    backgroundColor: colors.surface,
    flex: 1,
  },
  content: {
    flex: 1,
  },
  backRow: {
    paddingBottom: spacing.sm,
    paddingTop: spacing.xs,
  },
  scrollContent: {
    flexGrow: 1,
  },
  padded: {
    paddingHorizontal: spacing.md,
  },
});
