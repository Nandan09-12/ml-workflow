import { Pressable, StyleSheet, Text } from "react-native";

import { useAuth } from "../../src/auth/AuthContext";
import { ScreenShell } from "../../src/components/ScreenShell";
import { colors, radius, spacing, typography } from "../../src/theme/tokens";

export default function SettingsScreen() {
  const { signOut, user } = useAuth();

  return (
    <ScreenShell insetBottom padded>
      <Text style={styles.heading}>Settings</Text>
      <Text style={styles.email}>{user?.email}</Text>

      <Pressable onPress={signOut} style={styles.button}>
        <Text style={styles.buttonText}>SIGN OUT</Text>
      </Pressable>
    </ScreenShell>
  );
}

const styles = StyleSheet.create({
  heading: {
    color: colors.textPrimary,
    fontSize: 24,
    fontWeight: "800",
    marginTop: spacing.md,
  },
  email: {
    color: colors.textSecondary,
    fontSize: typography.body,
    marginTop: spacing.sm,
  },
  button: {
    alignItems: "center",
    backgroundColor: colors.brand,
    borderRadius: radius.sm,
    justifyContent: "center",
    marginTop: spacing.xl,
    minHeight: 52,
  },
  buttonText: {
    color: "#FFFFFF",
    fontSize: typography.body,
    fontWeight: "800",
    letterSpacing: 1.2,
  },
});
