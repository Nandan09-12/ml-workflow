import { StyleSheet, Text, TextInput, View } from "react-native";

import { ProjectGrid } from "../../src/components/ProjectGrid";
import { ScreenShell } from "../../src/components/ScreenShell";
import { colors, radius, spacing, typography } from "../../src/theme/tokens";

export default function ProjectsScreen() {
  return (
    <ScreenShell insetBottom padded>
      <View style={styles.content}>
        <Text style={styles.pageTitle}>Projects</Text>

        <View style={styles.searchBox}>
          <TextInput placeholder="Search Projects..." placeholderTextColor="#A0A5B6" />
        </View>

        <Text style={styles.sectionTitle}>TMO</Text>
        <ProjectGrid />
      </View>
    </ScreenShell>
  );
}

const styles = StyleSheet.create({
  content: {
    flex: 1,
  },
  pageTitle: {
    color: "#303030",
    fontSize: 24,
    fontWeight: "400",
    marginBottom: spacing.md,
  },
  searchBox: {
    backgroundColor: colors.surface,
    borderColor: "#E2E6EF",
    borderRadius: radius.sm,
    borderWidth: 1,
    minHeight: 48,
    paddingHorizontal: spacing.md,
    paddingVertical: 12,
    shadowColor: "#5F647A",
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.08,
    shadowRadius: 12,
  },
  sectionTitle: {
    color: "#141414",
    fontSize: typography.section,
    fontWeight: "800",
    marginTop: spacing.lg,
  },
});
