import { router } from "expo-router";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { AppIcon } from "../../src/components/AppIcon";
import { ScreenShell } from "../../src/components/ScreenShell";
import { colors, radius, spacing, typography } from "../../src/theme/tokens";

const fccOptions = [
  {
    id: "dt-checkin",
    icon: "checkin" as const,
    iconBackground: "#E8F0FF",
    title: "DT CHECKIN",
    description: "Drive tester attendance and field check-in flow.",
  },
  {
    id: "dt-expenses",
    icon: "expenses" as const,
    iconBackground: "#FFF2E7",
    title: "DT EXPENSES",
    description: "Expense submission and review flow for FCC work.",
  },
  {
    id: "mileage-tracker",
    icon: "mileage" as const,
    iconBackground: "#EAF8EF",
    title: "MILEAGE TRACKER",
    description: "Travel distance and reimbursement tracking.",
  },
];

export default function FccScreen() {
  return (
    <ScreenShell padded>
      <View style={styles.header}>
        <Pressable onPress={() => router.back()}>
          <Text style={styles.backLink}>Back</Text>
        </Pressable>
        <Text style={styles.title}>FCC</Text>
        <Text style={styles.subtitle}>Choose one workflow to build next.</Text>
      </View>

      <View style={styles.list}>
        {fccOptions.map((option) => (
          <Pressable
            key={option.id}
            onPress={() => {
              if (option.id === "dt-checkin") {
                router.push("/(tabs)/dt-checkin");
              }
              if (option.id === "dt-expenses") {
                router.push("/(tabs)/dt-expenses");
              }
              if (option.id === "mileage-tracker") {
                router.push("/(tabs)/mileage-tracker");
              }
            }}
            style={({ pressed }) => [styles.card, pressed && styles.pressed]}
          >
            <View style={styles.cardTopRow}>
              <View style={[styles.iconWrap, { backgroundColor: option.iconBackground }]}>
                <AppIcon color={colors.brand} name={option.icon} size={24} />
              </View>
              <View style={styles.copyWrap}>
                <Text style={styles.cardTitle}>{option.title}</Text>
                <Text style={styles.cardDescription}>{option.description}</Text>
              </View>
            </View>
            <View style={styles.cardFooter}>
              <Text style={styles.cardMeta}>Tap to open module</Text>
              <Text style={styles.cardArrow}>→</Text>
            </View>
          </Pressable>
        ))}
      </View>
    </ScreenShell>
  );
}

const styles = StyleSheet.create({
  header: {
    marginTop: spacing.md,
  },
  backLink: {
    color: "#3478F6",
    fontSize: typography.body,
    fontWeight: "600",
  },
  title: {
    color: colors.textPrimary,
    fontSize: 34,
    fontWeight: "800",
    marginTop: spacing.md,
  },
  subtitle: {
    color: colors.textSecondary,
    fontSize: typography.body,
    marginTop: spacing.sm,
  },
  list: {
    gap: spacing.md,
    marginTop: spacing.xl,
  },
  card: {
    backgroundColor: colors.surface,
    borderColor: "#DCE4F3",
    borderRadius: 28,
    borderWidth: 1.5,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.lg,
    shadowColor: "#1B214A",
    shadowOffset: { width: 0, height: 12 },
    shadowOpacity: 0.08,
    shadowRadius: 18,
  },
  pressed: {
    opacity: 0.9,
    transform: [{ scale: 0.992 }],
  },
  cardTopRow: {
    alignItems: "flex-start",
    flexDirection: "row",
    gap: spacing.md,
  },
  iconWrap: {
    alignItems: "center",
    borderRadius: 18,
    height: 52,
    justifyContent: "center",
    width: 52,
  },
  copyWrap: {
    flex: 1,
  },
  cardTitle: {
    color: colors.textPrimary,
    fontSize: 18,
    fontWeight: "800",
  },
  cardDescription: {
    color: colors.textSecondary,
    fontSize: typography.body,
    lineHeight: 22,
    marginTop: spacing.xs,
  },
  cardFooter: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: spacing.lg,
  },
  cardMeta: {
    color: "#6E7FA1",
    fontSize: typography.caption,
    fontWeight: "700",
    letterSpacing: 0.4,
  },
  cardArrow: {
    color: "#2F67E5",
    fontSize: 22,
    fontWeight: "800",
  },
});
