import { router } from "expo-router";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";

import { BrandHeader } from "../../src/components/BrandHeader";
import { ScreenShell } from "../../src/components/ScreenShell";
import { colors, radius, spacing, typography } from "../../src/theme/tokens";

export default function MicrosoftLoginScreen() {
  return (
    <ScreenShell padded>
      <View style={styles.content}>
        <BrandHeader />

        <View style={styles.card}>
          <Text style={styles.microsoftWordmark}>Microsoft</Text>
          <Text style={styles.title}>Sign in</Text>

          <TextInput
            autoCapitalize="none"
            keyboardType="email-address"
            placeholder="Email, phone, or Skype"
            placeholderTextColor="#6F768B"
            style={styles.input}
          />

          <Text style={styles.link}>No account? Create one!</Text>
          <Text style={styles.link}>Can’t access your account?</Text>

          <Pressable onPress={() => router.replace("/(auth)/login")} style={styles.nextButton}>
            <Text style={styles.nextButtonText}>Next</Text>
          </Pressable>

          <Pressable onPress={() => router.replace("/(auth)/login")} style={styles.secondaryButton}>
            <Text style={styles.secondaryButtonText}>Close</Text>
          </Pressable>
        </View>
      </View>
    </ScreenShell>
  );
}

const styles = StyleSheet.create({
  content: {
    flex: 1,
    justifyContent: "center",
  },
  card: {
    backgroundColor: "#FFFFFF",
    borderRadius: radius.md,
    marginTop: spacing.xl,
    padding: spacing.xl,
  },
  microsoftWordmark: {
    color: "#1F1F1F",
    fontSize: 18,
    fontWeight: "700",
  },
  title: {
    color: "#1F1F1F",
    fontSize: 34,
    fontWeight: "600",
    marginTop: spacing.lg,
  },
  input: {
    borderBottomColor: "#9AA3B8",
    borderBottomWidth: 1,
    color: "#1F1F1F",
    fontSize: typography.body,
    marginTop: spacing.xl,
    minHeight: 52,
  },
  link: {
    color: "#1A5FB4",
    fontSize: typography.body,
    marginTop: spacing.md,
  },
  nextButton: {
    alignItems: "center",
    alignSelf: "flex-end",
    backgroundColor: "#0067B8",
    borderRadius: radius.sm,
    justifyContent: "center",
    marginTop: spacing.xl,
    minHeight: 44,
    minWidth: 112,
    paddingHorizontal: spacing.lg,
  },
  nextButtonText: {
    color: "#FFFFFF",
    fontSize: typography.body,
    fontWeight: "700",
  },
  secondaryButton: {
    alignItems: "center",
    justifyContent: "center",
    marginTop: spacing.xl,
    minHeight: 44,
  },
  secondaryButtonText: {
    color: colors.textSecondary,
    fontSize: typography.body,
    fontWeight: "600",
  },
});
