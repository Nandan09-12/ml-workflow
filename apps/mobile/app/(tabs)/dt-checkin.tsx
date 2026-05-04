import { router, useFocusEffect, useLocalSearchParams } from "expo-router";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { ApiClientError } from "@ml-workflow/api-client";

import { ScreenShell } from "../../src/components/ScreenShell";
import { useSubmissions } from "../../src/submissions/SubmissionsContext";
import type { SubmissionRecord } from "../../src/submissions/types";
import { colors, radius, spacing, typography } from "../../src/theme/tokens";

const filters = ["Today", "Ongoing", "Completed", "Attachments"] as const;

function formatWorkDate(dateString: string) {
  const [year, month, day] = dateString.split("-").map(Number);
  const date = new Date(year, month - 1, day);

  return date.toLocaleDateString("en-US", {
    day: "numeric",
    month: "short",
  });
}

function regionLabel(region: SubmissionRecord["region"]) {
  if (region === "NE-UP") {
    return "NORTHEAST";
  }

  return region.toUpperCase();
}

export default function DtCheckinScreen() {
  const { filter } = useLocalSearchParams<{ filter?: string }>();
  const { isLoading, loadSubmissions, submissions } = useSubmissions();
  const [selectedFilter, setSelectedFilter] = useState<(typeof filters)[number]>("Today");
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    if (filter === "Ongoing" || filter === "Completed" || filter === "Attachments" || filter === "Today") {
      setSelectedFilter(filter);
    }
  }, [filter]);

  useFocusEffect(
    useCallback(() => {
      let active = true;

      const run = async () => {
        try {
          setLoadError(null);
          await loadSubmissions();
        } catch (error) {
          if (!active) {
            return;
          }
          setLoadError(
            error instanceof ApiClientError
              ? error.message
              : "Unable to load submissions right now.",
          );
        }
      };

      void run();

      return () => {
        active = false;
      };
    }, [loadSubmissions]),
  );

  const visibleSubmissions = useMemo(() => {
    if (selectedFilter === "Today") {
      const today = new Date().toISOString().slice(0, 10);
      return submissions.filter((submission) => submission.workDate === today);
    }

    if (selectedFilter === "Ongoing") {
      return submissions.filter((submission) => submission.status === "ONGOING");
    }

    if (selectedFilter === "Completed") {
      return submissions.filter((submission) => submission.status === "COMPLETED");
    }

    return submissions.filter((submission) => submission.status === "ATTACHMENTS");
  }, [selectedFilter, submissions]);

  return (
    <ScreenShell backFallbackHref="/(tabs)/fcc" padded scrollable={false}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.topRow}>
          <View>
            <Text style={styles.eyebrow}>DRIVE TESTER CHECK-IN</Text>
            <Text style={styles.heading}>My submissions</Text>
          </View>
          <Pressable onPress={() => router.back()} style={styles.modulesButton}>
            <Text style={styles.modulesLabel}>Modules</Text>
          </Pressable>
        </View>

        {loadError ? <Text style={styles.errorText}>{loadError}</Text> : null}

        <View style={styles.filterRow}>
          {filters.map((filterName) => (
            <Pressable
              key={filterName}
              onPress={() => setSelectedFilter(filterName)}
              style={[
                styles.filterChip,
                selectedFilter === filterName && styles.filterChipActive,
              ]}
            >
              <Text
                style={[
                  styles.filterText,
                  selectedFilter === filterName && styles.filterTextActive,
                ]}
              >
                {filterName}
              </Text>
            </Pressable>
          ))}
        </View>

        <View style={styles.cardList}>
          {!isLoading && visibleSubmissions.length === 0 ? (
            <View style={styles.emptyCard}>
              <Text style={styles.emptyTitle}>No submissions found</Text>
              <Text style={styles.emptySubtitle}>
                {selectedFilter === "Today"
                  ? "You do not have any submissions for today yet."
                  : `No submissions match the ${selectedFilter.toLowerCase()} filter.`}
              </Text>
            </View>
          ) : null}
          {visibleSubmissions.map((submission) => (
            <Pressable
              key={submission.id}
              onPress={() =>
                router.push({
                  params: { id: submission.id },
                  pathname: "/(tabs)/dt-checkin-detail",
                })
              }
              style={({ pressed }) => [styles.submissionCard, pressed && styles.submissionCardPressed]}
            >
              <View style={styles.submissionHeader}>
                <Text style={styles.submissionTitle}>
                  {submission.workorderName} / {submission.shift}
                </Text>
                <View
                  style={[
                    styles.statusChip,
                    submission.status === "ATTACHMENTS" ? styles.statusWarning : styles.statusNeutral,
                  ]}
                >
                  <Text
                    style={[
                      styles.statusText,
                      submission.status === "ATTACHMENTS" ? styles.statusWarningText : styles.statusNeutralText,
                    ]}
                  >
                    {submission.status === "ATTACHMENTS"
                      ? "Attachment pending"
                      : submission.status === "COMPLETED"
                      ? "Completed"
                      : "Ongoing"}
                  </Text>
                </View>
              </View>
              <Text style={styles.submissionMeta}>
                {regionLabel(submission.region)} • {formatWorkDate(submission.workDate)} • Ticket{" "}
                {submission.ticketNumber || "TBD"}
              </Text>
            </Pressable>
          ))}
        </View>
      </ScrollView>

      <View style={styles.footer}>
        <Pressable onPress={() => router.push("/(tabs)/dt-checkin-new")} style={styles.newButton}>
          <Text style={styles.newButtonLabel}>+ New submission</Text>
        </Pressable>
      </View>
    </ScreenShell>
  );
}

const styles = StyleSheet.create({
  content: {
    paddingBottom: 120,
  },
  topRow: {
    alignItems: "flex-start",
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: spacing.sm,
  },
  eyebrow: {
    color: "#2466D8",
    fontSize: 14,
    fontWeight: "800",
    letterSpacing: 2,
  },
  heading: {
    color: "#182742",
    fontSize: 28,
    fontWeight: "800",
    marginTop: spacing.lg,
  },
  modulesButton: {
    backgroundColor: "#EAF1FB",
    borderRadius: radius.lg,
    minWidth: 108,
    paddingHorizontal: spacing.md,
    paddingVertical: 14,
  },
  modulesLabel: {
    color: "#24334E",
    fontSize: 18,
    fontWeight: "600",
    textAlign: "center",
  },
  filterRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: spacing.xl,
  },
  errorText: {
    color: "#C43F5A",
    fontSize: typography.caption,
    marginTop: spacing.lg,
  },
  filterChip: {
    backgroundColor: "#EAF1FB",
    borderRadius: radius.pill,
    minWidth: "23%",
    paddingHorizontal: spacing.sm,
    paddingVertical: 12,
  },
  filterChipActive: {
    backgroundColor: "#E5F0FF",
  },
  filterText: {
    color: "#677C9B",
    fontSize: 15,
    fontWeight: "700",
    textAlign: "center",
  },
  filterTextActive: {
    color: "#2466D8",
  },
  cardList: {
    gap: spacing.lg,
    marginTop: spacing.lg,
  },
  emptyCard: {
    backgroundColor: "#F8FBFF",
    borderColor: "#D8E4F5",
    borderRadius: 26,
    borderWidth: 1.5,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.xl,
  },
  emptyTitle: {
    color: "#182742",
    fontSize: 20,
    fontWeight: "800",
  },
  emptySubtitle: {
    color: "#7084A0",
    fontSize: 16,
    lineHeight: 22,
    marginTop: spacing.sm,
  },
  submissionCard: {
    backgroundColor: colors.surface,
    borderColor: "#D8E4F5",
    borderRadius: 30,
    borderWidth: 1.5,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.lg,
  },
  submissionCardPressed: {
    opacity: 0.88,
  },
  submissionHeader: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
  },
  submissionTitle: {
    color: "#111A2A",
    fontSize: 24,
    fontWeight: "800",
    flex: 1,
    paddingRight: spacing.md,
  },
  statusChip: {
    borderRadius: radius.pill,
    paddingHorizontal: spacing.lg,
    paddingVertical: 10,
  },
  statusWarning: {
    backgroundColor: "#FFF0CC",
  },
  statusNeutral: {
    backgroundColor: "#E9EFF8",
  },
  statusText: {
    fontSize: 14,
    fontWeight: "800",
  },
  statusWarningText: {
    color: "#BF7800",
  },
  statusNeutralText: {
    color: "#6B7E99",
  },
  submissionMeta: {
    color: "#7084A0",
    fontSize: 18,
    fontWeight: "500",
    marginTop: spacing.lg,
  },
  footer: {
    alignItems: "flex-end",
    bottom: spacing.lg,
    left: spacing.md,
    position: "absolute",
    right: spacing.md,
  },
  newButton: {
    backgroundColor: "#2466D8",
    borderRadius: 24,
    minWidth: 220,
    paddingHorizontal: spacing.xl,
    paddingVertical: 20,
    shadowColor: "#2466D8",
    shadowOffset: { width: 0, height: 12 },
    shadowOpacity: 0.22,
    shadowRadius: 18,
  },
  newButtonLabel: {
    color: colors.surface,
    fontSize: 20,
    fontWeight: "700",
    textAlign: "center",
  },
});
