import type { Href } from "expo-router";
import { useRouter } from "expo-router";
import { Pressable, StyleSheet, Text } from "react-native";

import { colors } from "../theme/tokens";

type BackButtonProps = {
  fallbackHref?: Href;
};

export function BackButton({ fallbackHref }: BackButtonProps) {
  const router = useRouter();
  const canGoBack = router.canGoBack();

  const handlePress = () => {
    if (canGoBack) {
      router.back();
      return;
    }

    if (fallbackHref) {
      router.replace(fallbackHref);
    }
  };

  if (!canGoBack && !fallbackHref) {
    return null;
  }

  return (
    <Pressable
      accessibilityLabel="Go back"
      accessibilityRole="button"
      hitSlop={12}
      onPress={handlePress}
      style={({ pressed }) => [styles.button, pressed && styles.buttonPressed]}
    >
      <Text style={styles.icon}>‹</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    alignItems: "center",
    backgroundColor: "rgba(255, 255, 255, 0.96)",
    borderColor: "#DCE4F3",
    borderRadius: 999,
    borderWidth: 1,
    height: 40,
    justifyContent: "center",
    shadowColor: "#1B214A",
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.08,
    shadowRadius: 12,
    width: 40,
  },
  buttonPressed: {
    opacity: 0.82,
  },
  icon: {
    color: colors.textPrimary,
    fontSize: 26,
    fontWeight: "700",
    lineHeight: 28,
    marginLeft: -2,
  },
});
