import { router } from "expo-router";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { useAuth } from "../src/auth/AuthContext";
import { BrandHeader } from "../src/components/BrandHeader";
import { ScreenShell } from "../src/components/ScreenShell";
import { colors, radius, spacing, typography } from "../src/theme/tokens";

export default function PendingApprovalScreen() {
  const { errorMessage, isSubmitting, refreshApprovalStatus, signOut, user } = useAuth();

  const onRefreshStatus = async () => {
    const result = await refreshApprovalStatus();

    if (result === "APPROVED") {
      router.replace("/(tabs)/projects");
    }
  };

  return (
    <ScreenShell padded>
      <View style={styles.content}>
        <BrandHeader />
        <View style={styles.card}>
          <Text style={styles.title}>Approval pending</Text>
          <Text style={styles.body}>
            {user?.email ?? "Your account"} has been created and is waiting for admin approval.
          </Text>
          <Text style={styles.body}>
            Once your access is approved, this app will take you straight to Projects.
          </Text>

          {errorMessage ? <Text style={styles.errorText}>{errorMessage}</Text> : null}

          <Pressable onPress={onRefreshStatus} style={styles.secondaryButton}>
            <Text style={styles.secondaryButtonText}>
              {isSubmitting ? "CHECKING..." : "CHECK APPROVAL STATUS"}
            </Text>
          </Pressable>

          <Pressable
            onPress={async () => {
              await signOut();
              router.replace("/(auth)/login");
            }}
            style={styles.button}
          >
            <Text style={styles.buttonText}>SIGN OUT</Text>
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
    backgroundColor: "#F4F6FA",
    borderRadius: radius.lg,
    marginTop: spacing.xl,
    padding: spacing.xl,
  },
  title: {
    color: colors.textPrimary,
    fontSize: 26,
    fontWeight: "800",
  },
  body: {
    color: colors.textSecondary,
    fontSize: typography.body,
    lineHeight: 24,
    marginTop: spacing.md,
  },
  errorText: {
    color: "#C43F5A",
    fontSize: typography.caption,
    lineHeight: 18,
    marginTop: spacing.lg,
  },
  secondaryButton: {
    alignItems: "center",
    backgroundColor: "#E5E9F5",
    borderRadius: radius.sm,
    marginTop: spacing.xl,
    minHeight: 50,
    justifyContent: "center",
  },
  secondaryButtonText: {
    color: colors.textPrimary,
    fontSize: typography.body,
    fontWeight: "700",
    letterSpacing: 0.6,
  },
  button: {
    alignItems: "center",
    backgroundColor: colors.brand,
    borderRadius: radius.sm,
    marginTop: spacing.md,
    minHeight: 50,
    justifyContent: "center",
  },
  buttonText: {
    color: "#FFFFFF",
    fontSize: typography.body,
    fontWeight: "800",
    letterSpacing: 1.2,
  },
});
