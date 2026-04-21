import type { PropsWithChildren } from "react";
import { StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { colors, spacing } from "../theme/tokens";

type ScreenShellProps = PropsWithChildren<{
  insetBottom?: boolean;
  padded?: boolean;
}>;

export function ScreenShell({
  children,
  insetBottom = false,
  padded = true,
}: ScreenShellProps) {
  return (
    <SafeAreaView edges={insetBottom ? ["top", "bottom"] : ["top"]} style={styles.safeArea}>
      <View style={[styles.content, padded && styles.padded]}>{children}</View>
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
  padded: {
    paddingHorizontal: spacing.md,
  },
});
