import { router, useLocalSearchParams, useSegments } from "expo-router";
import * as DocumentPicker from "expo-document-picker";
import { useEffect, useMemo, useState } from "react";
import { Modal, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import Svg, { Circle } from "react-native-svg";
import { ApiClientError } from "@ml-workflow/api-client";

import { ScreenShell } from "../../src/components/ScreenShell";
import { apiClient } from "../../src/lib/api";
import { useSubmissions } from "../../src/submissions/SubmissionsContext";
import type { Attachment } from "../../src/submissions/types";
import { colors, radius, spacing, typography } from "../../src/theme/tokens";

type SubmissionMutationResponse = {
  id: string;
  version_number: number;
  completed_grids: number;
  skipped_grids: number;
  force_tested_grids: number;
  status: "IN_PROGRESS" | "CHECKED_OUT" | "COMPLETED";
  ended_at: string | null;
  completed_at?: string | null;
};

export default function DtCheckinDetailScreen() {
  const { id } = useLocalSearchParams<{ id?: string }>();
  const { submissions, updateSubmission } = useSubmissions();
  const submission = submissions.find((item) => item.id === id);
  const [numberOfGrids, setNumberOfGrids] = useState("");
  const [completedGrids, setCompletedGrids] = useState("");
  const [skippedGrids, setSkippedGrids] = useState("");
  const [forceTestedGrids, setForceTestedGrids] = useState("");
  const [endTime, setEndTime] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [actionMode, setActionMode] = useState<"grid-update" | "end-workorder" | null>(null);
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [isSaving, setIsSaving] = useState(false);

  if (!submission) {
    return (
      <ScreenShell backFallbackHref="/(tabs)/dt-checkin" padded scrollable={false}>
        <View style={styles.emptyState}>
          <Text style={styles.emptyTitle}>Submission not found</Text>
          <Pressable onPress={() => router.replace("/(tabs)/dt-checkin")}>
            <Text style={styles.backLink}>Back to submissions</Text>
          </Pressable>
        </View>
      </ScreenShell>
    );
  }

  useEffect(() => {
    setNumberOfGrids(String(submission.numberOfGrids));
    setCompletedGrids(String(submission.completedGrids));
    setSkippedGrids(submission.skippedGrids > 0 ? String(submission.skippedGrids) : "");
    setForceTestedGrids(
      submission.forceTestedGrids !== undefined ? String(submission.forceTestedGrids) : "",
    );
    setEndTime(submission.endTime ?? "");
    if (submission.attachments) {
      setAttachments(submission.attachments);
    }
  }, [
    submission.completedGrids,
    submission.endTime,
    submission.forceTestedGrids,
    submission.numberOfGrids,
    submission.skippedGrids,
    submission.attachments,
  ]);

  const segments = useSegments();
  const isDetailActive = segments[segments.length - 1] === "dt-checkin-detail";
  const editable = submission.status === "ONGOING";
  const isAttachmentMode = submission.status === "ATTACHMENTS";
  const showActionModal = editable && actionMode === null;

  useEffect(() => {
    if (isDetailActive && editable) {
      setActionMode(null);
      setEndTime("");
      setError(null);
    }
  }, [isDetailActive, editable, id]);

  // Auto-populate end time when end-workorder is selected
  useEffect(() => {
    if (actionMode === "end-workorder") {
      const now = new Date();
      const formattedTime = now.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      });
      setEndTime(formattedTime);
    }
  }, [actionMode]);

  const derivedCounts = useMemo(() => {
    const total = Number(numberOfGrids) || 0;
    const completed = Number(completedGrids) || 0;
    const skipped = Number(skippedGrids) || 0;
    const pending = Math.max(total - completed - skipped, 0);

    return { completed, pending, skipped, total };
  }, [completedGrids, numberOfGrids, skippedGrids]);

  const completion = derivedCounts.total
    ? Math.round((derivedCounts.completed / derivedCounts.total) * 100)
    : 0;
  const radiusValue = 52;
  const circumference = 2 * Math.PI * radiusValue;
  const progress = circumference - (completion / 100) * circumference;

  const handlePickDocument = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: [
          "text/csv",
          "application/csv",
          "application/vnd.ms-excel",
          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ],
      });

      if (!result.canceled && result.assets && result.assets.length > 0) {
        const asset = result.assets[0];
        const newAttachment: Attachment = {
          id: String(Date.now()),
          name: asset.name || "Unnamed file",
          type: asset.mimeType || "application/octet-stream",
          uri: asset.uri,
        };

        setAttachments((prev) => [...prev, newAttachment]);
      }
    } catch (err) {
      setError("Failed to pick document");
    }
  };

  const handleRemoveAttachment = (attachmentId: string) => {
    setAttachments((prev) => prev.filter((att) => att.id !== attachmentId));
  };

  const handleSaveAttachments = async () => {
    if (!skippedGrids.trim() || !forceTestedGrids.trim() || attachments.length === 0) {
      setError("Everything is mandatory to complete the work order.");
      return;
    }

    const total = Number(numberOfGrids);
    const completed = Number(completedGrids);
    const skipped = Number(skippedGrids);
    const forceTested = Number(forceTestedGrids);

    if (
      Number.isNaN(total) ||
      Number.isNaN(completed) ||
      Number.isNaN(skipped) ||
      Number.isNaN(forceTested) ||
      total <= 0 ||
      completed < 0 ||
      skipped < 0 ||
      forceTested < 0
    ) {
      setError("Enter valid non-negative values before completing the work order.");
      return;
    }

    if (completed + skipped > total) {
      setError("Completed grids and skipped grids cannot exceed total grids.");
      return;
    }

    if (!submission.backendVersionNumber) {
      setError("This submission is not linked to the backend yet.");
      return;
    }

    setIsSaving(true);

    try {
      const updated = await apiClient.patch<SubmissionMutationResponse>(
        `/api/v1/submissions/${submission.id}`,
        {
          completed_grids: completed,
          force_tested_grids: forceTested,
          skipped_grids: skipped,
          version_number: submission.backendVersionNumber,
        },
      );

      let activeVersion = updated.version_number;

      for (const attachment of attachments) {
        const formData = new FormData();
        formData.append(
          "file",
          {
            name: attachment.name,
            type: attachment.type,
            uri: attachment.uri,
          } as never,
        );

        await apiClient.post(
          `/api/v1/submissions/${submission.id}/attachments`,
          formData,
        );
      }

      const completedResponse = await apiClient.post<SubmissionMutationResponse>(
        `/api/v1/submissions/${submission.id}/complete`,
      );
      activeVersion = completedResponse.version_number;

      updateSubmission(submission.id, {
        attachments,
        backendVersionNumber: activeVersion,
        completedGrids: completedResponse.completed_grids,
        forceTestedGrids: completedResponse.force_tested_grids,
        pendingGrids: Math.max(total - completedResponse.completed_grids - completedResponse.skipped_grids, 0),
        skippedGrids: completedResponse.skipped_grids,
        status: "COMPLETED",
      });
      setError(null);

      router.push({
        params: { filter: "Completed" },
        pathname: "/(tabs)/dt-checkin",
      });
    } catch (err) {
      setError(
        err instanceof ApiClientError
          ? err.message
          : "Unable to complete the work order right now.",
      );
    } finally {
      setIsSaving(false);
    }
  };

  const handleSave = async () => {
    const { completed, total } = derivedCounts;

    if (
      Number.isNaN(total) ||
      Number.isNaN(completed) ||
      total <= 0 ||
      completed < 0
    ) {
      setError("Enter valid non-negative grid counts.");
      return;
    }

    if (completed > total) {
      setError("Completed grids cannot exceed total grids.");
      return;
    }

    if (!submission.backendVersionNumber) {
      setError("This submission is not linked to the backend yet.");
      return;
    }

    setIsSaving(true);

    try {
    if (actionMode === "end-workorder") {
        const updated = await apiClient.patch<SubmissionMutationResponse>(
          `/api/v1/submissions/${submission.id}`,
          {
            completed_grids: completed,
            version_number: submission.backendVersionNumber,
          },
        );

        const checkedOut = await apiClient.post<SubmissionMutationResponse>(
          `/api/v1/submissions/${submission.id}/end-drive`,
        );

        const endedAt = checkedOut.ended_at
          ? new Date(checkedOut.ended_at).toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            })
          : endTime.trim();

        updateSubmission(submission.id, {
          backendVersionNumber: checkedOut.version_number,
          completedGrids: updated.completed_grids,
          endTime: endedAt,
          numberOfGrids: total,
          pendingGrids: Math.max(total - updated.completed_grids, 0),
          status: "ATTACHMENTS",
        });

        setEndTime(endedAt);
        setError(null);
        router.push({
          params: { filter: "Attachments" },
          pathname: "/(tabs)/dt-checkin",
        });
        return;
    }

      const updated = await apiClient.patch<SubmissionMutationResponse>(
        `/api/v1/submissions/${submission.id}`,
        {
          completed_grids: completed,
          version_number: submission.backendVersionNumber,
        },
      );

      updateSubmission(submission.id, {
        backendVersionNumber: updated.version_number,
        completedGrids: updated.completed_grids,
        numberOfGrids: total,
        pendingGrids: Math.max(total - updated.completed_grids, 0),
      });

      setError(null);
      router.push({
        params: { filter: "Ongoing" },
        pathname: "/(tabs)/dt-checkin",
      });
    } catch (err) {
      setError(
        err instanceof ApiClientError
          ? err.message
          : "Unable to save this work order right now.",
      );
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <>
      <Modal transparent visible={showActionModal} animationType="fade">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Select Action</Text>
            <Text style={styles.modalSubtitle}>What would you like to do?</Text>

            <Pressable
              onPress={() => {
                setActionMode("grid-update");
              }}
              style={styles.actionButton}
            >
              <Text style={styles.actionButtonText}>Update Grid Counts</Text>
              <Text style={styles.actionButtonDesc}>Update grid counts for this workorder</Text>
            </Pressable>

            <Pressable
              onPress={() => {
                setActionMode("end-workorder");
              }}
              style={styles.actionButton}
            >
              <Text style={styles.actionButtonText}>End Workorder</Text>
              <Text style={styles.actionButtonDesc}>Complete workorder and move to attachments</Text>
            </Pressable>
          </View>
        </View>
      </Modal>

      <ScreenShell backFallbackHref="/(tabs)/dt-checkin" padded scrollable={false}>
        <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
          <View style={styles.topRow}>
            <View>
              <Text style={styles.eyebrow}>DRIVE TESTER CHECK-IN</Text>
              <Text style={styles.heading}>{submission.workorderName}</Text>
            </View>
            <Pressable onPress={() => router.back()} style={styles.closeButton}>
              <Text style={styles.closeLabel}>Close</Text>
            </Pressable>
          </View>

          <View style={styles.progressCard}>
            <View>
              <Text style={styles.progressLabel}>Completion</Text>
              <Text style={styles.progressValue}>{completion}%</Text>
              <Text style={styles.progressMeta}>
                {derivedCounts.completed} of {derivedCounts.total} grids completed
              </Text>
            </View>

            <View style={styles.chartWrap}>
              <Svg height="120" width="120">
                <Circle
                  cx="60"
                  cy="60"
                  fill="none"
                  r={radiusValue}
                  stroke="#E7EDF7"
                  strokeWidth="14"
                />
                <Circle
                  cx="60"
                  cy="60"
                  fill="none"
                  r={radiusValue}
                  rotation="-90"
                  origin="60,60"
                  stroke="#2466D8"
                  strokeDasharray={`${circumference} ${circumference}`}
                  strokeDashoffset={progress}
                  strokeLinecap="round"
                  strokeWidth="14"
                />
              </Svg>
              <View style={styles.chartCenter}>
                <Text style={styles.chartCenterText}>{completion}%</Text>
              </View>
            </View>
          </View>

          <View style={styles.gridCountsCard}>
            <View style={styles.gridCountsHeader}>
              <Text style={styles.gridCountsTitle}>Grid counts</Text>
              <Text style={styles.gridCountsNote}>LIVE PROGRESS</Text>
            </View>

            <View style={styles.gridWrap}>
              <CountCard
                editable={editable || isAttachmentMode}
                label="Number of grids"
                onChangeText={setNumberOfGrids}
                value={numberOfGrids}
              />
              <CountCard
                editable={editable || isAttachmentMode}
                label="Completed grids"
                onChangeText={setCompletedGrids}
                value={completedGrids}
              />
            </View>

            {actionMode === "end-workorder" && (
              <View style={styles.fieldBlock}>
                <Text style={styles.endTimeLabel}>End Time</Text>
                <TextInput
                  editable={editable}
                  onChangeText={setEndTime}
                  placeholder="e.g., 05:30 PM"
                  placeholderTextColor="#9699A8"
                  style={styles.endTimeInput}
                  value={endTime}
                />
              </View>
            )}

            {isAttachmentMode && (
              <View style={styles.attachmentsCard}>
                <Text style={styles.attachmentsTitle}>Complete work order</Text>

                <View style={styles.gridWrap}>
                  <CountCard
                    editable
                    label="Skipped grids"
                    onChangeText={setSkippedGrids}
                    value={skippedGrids}
                  />
                  <CountCard
                    editable
                    label="Force tested grids"
                    onChangeText={setForceTestedGrids}
                    value={forceTestedGrids}
                  />
                </View>

                <View style={styles.fieldBlock}>
                  <Text style={styles.endTimeLabel}>Completed at</Text>
                  <View style={styles.endTimeDisplay}>
                    <Text style={styles.endTimeDisplayText}>{submission.endTime ?? endTime}</Text>
                  </View>
                </View>

                {attachments.length > 0 && (
                  <View style={styles.attachmentsList}>
                    {attachments.map((attachment) => (
                      <View key={attachment.id} style={styles.attachmentItem}>
                        <Text style={styles.attachmentName} numberOfLines={1}>
                          {attachment.name}
                        </Text>
                        <Pressable
                          onPress={() => handleRemoveAttachment(attachment.id)}
                          style={styles.removeButton}
                        >
                          <Text style={styles.removeButtonText}>✕</Text>
                        </Pressable>
                      </View>
                    ))}
                  </View>
                )}

                <Pressable onPress={handlePickDocument} style={styles.addAttachmentButton}>
                  <Text style={styles.addAttachmentButtonText}>+ Add Attachment</Text>
                </Pressable>

                {error ? <Text style={styles.errorText}>{error}</Text> : null}
                <Pressable onPress={handleSaveAttachments} style={styles.saveButton}>
                  <Text style={styles.saveButtonLabel}>
                    {isSaving ? "Completing..." : "Complete work order"}
                  </Text>
                </Pressable>
              </View>
            )}

            {editable ? (
              <>
                {error ? <Text style={styles.errorText}>{error}</Text> : null}
                <Pressable onPress={handleSave} style={styles.saveButton}>
                  <Text style={styles.saveButtonLabel}>
                    {isSaving
                      ? "Saving..."
                      : actionMode === "end-workorder"
                      ? "Save and End Workorder"
                      : "Save grid counts"}
                  </Text>
                </Pressable>
              </>
            ) : null}
          </View>
        </ScrollView>
      </ScreenShell>
    </>
  );
}

function CountCard({
  editable,
  label,
  onChangeText,
  value,
}: {
  editable: boolean;
  label: string;
  onChangeText: (value: string) => void;
  value: string;
}) {
  return (
    <View style={styles.countCard}>
      <Text style={styles.countLabel}>{label}</Text>
      {editable ? (
        <TextInput
          keyboardType="number-pad"
          onChangeText={onChangeText}
          style={styles.countInput}
          value={value}
        />
      ) : (
        <Text style={styles.countValue}>{value}</Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  content: {
    paddingBottom: spacing.xxl,
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
  closeButton: {
    backgroundColor: "#EAF1FB",
    borderRadius: radius.lg,
    minWidth: 104,
    paddingHorizontal: spacing.md,
    paddingVertical: 14,
  },
  closeLabel: {
    color: "#24334E",
    fontSize: 18,
    fontWeight: "600",
    textAlign: "center",
  },
  progressCard: {
    alignItems: "center",
    backgroundColor: colors.surface,
    borderColor: "#D8E4F5",
    borderRadius: 28,
    borderWidth: 1.5,
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: spacing.xl,
    padding: spacing.lg,
  },
  progressLabel: {
    color: "#6C819F",
    fontSize: 16,
    fontWeight: "700",
  },
  progressValue: {
    color: "#182742",
    fontSize: 34,
    fontWeight: "800",
    marginTop: spacing.sm,
  },
  progressMeta: {
    color: "#7084A0",
    fontSize: typography.body,
    lineHeight: 22,
    marginTop: spacing.sm,
    maxWidth: 160,
  },
  chartWrap: {
    alignItems: "center",
    height: 120,
    justifyContent: "center",
    position: "relative",
    width: 120,
  },
  chartCenter: {
    alignItems: "center",
    justifyContent: "center",
    position: "absolute",
  },
  chartCenterText: {
    color: "#2466D8",
    fontSize: 24,
    fontWeight: "800",
  },
  gridCountsCard: {
    backgroundColor: colors.surface,
    borderColor: "#D8E4F5",
    borderRadius: 28,
    borderWidth: 1.5,
    marginTop: spacing.xl,
    padding: spacing.lg,
  },
  gridCountsHeader: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
  },
  gridCountsTitle: {
    color: "#182742",
    fontSize: 19,
    fontWeight: "800",
  },
  gridCountsNote: {
    color: "#2466D8",
    fontSize: 14,
    fontWeight: "800",
    letterSpacing: 2,
  },
  gridWrap: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.md,
    justifyContent: "space-between",
    marginTop: spacing.lg,
  },
  countCard: {
    backgroundColor: "#F4F8FE",
    borderColor: "#D8E4F5",
    borderRadius: 24,
    borderWidth: 1.5,
    minHeight: 118,
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.lg,
    width: "47.5%",
  },
  countLabel: {
    color: "#6C819F",
    fontSize: 16,
    fontWeight: "700",
  },
  countValue: {
    color: "#1A2842",
    fontSize: 24,
    fontWeight: "500",
    marginTop: spacing.lg,
  },
  countInput: {
    color: "#1A2842",
    fontSize: 24,
    fontWeight: "500",
    marginTop: spacing.lg,
    paddingVertical: 0,
  },
  errorText: {
    color: "#C43F5A",
    fontSize: typography.caption,
    marginTop: spacing.md,
  },
  saveButton: {
    alignItems: "center",
    backgroundColor: "#EAF1FB",
    borderRadius: 20,
    justifyContent: "center",
    marginTop: spacing.lg,
    minHeight: 56,
  },
  saveButtonLabel: {
    color: "#1C2740",
    fontSize: typography.body,
    fontWeight: "700",
  },
  emptyState: {
    alignItems: "center",
    flex: 1,
    justifyContent: "center",
  },
  emptyTitle: {
    color: "#182742",
    fontSize: 24,
    fontWeight: "800",
  },
  backLink: {
    color: "#2466D8",
    fontSize: typography.body,
    fontWeight: "600",
    marginTop: spacing.md,
  },
  modalOverlay: {
    alignItems: "center",
    backgroundColor: "rgba(0, 0, 0, 0.5)",
    flex: 1,
    justifyContent: "center",
  },
  modalContent: {
    backgroundColor: colors.surface,
    borderRadius: 24,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.xl,
    width: "85%",
  },
  modalTitle: {
    color: "#182742",
    fontSize: 24,
    fontWeight: "800",
    textAlign: "center",
  },
  modalSubtitle: {
    color: "#6C819F",
    fontSize: typography.body,
    marginBottom: spacing.lg,
    marginTop: spacing.sm,
    textAlign: "center",
  },
  actionButton: {
    alignItems: "flex-start",
    borderColor: "#D8E4F5",
    borderRadius: 16,
    borderWidth: 1.5,
    marginBottom: spacing.md,
    padding: spacing.lg,
  },
  actionButtonText: {
    color: "#182742",
    fontSize: 18,
    fontWeight: "700",
  },
  actionButtonDesc: {
    color: "#6C819F",
    fontSize: typography.caption,
    marginTop: spacing.xs,
  },
  fieldBlock: {
    marginTop: spacing.lg,
  },
  endTimeLabel: {
    color: "#6C819F",
    fontSize: 16,
    fontWeight: "700",
    marginBottom: spacing.sm,
  },
  endTimeInput: {
    borderBottomColor: "#B7BCCA",
    borderBottomWidth: 1,
    color: "#1A2842",
    fontSize: typography.body,
    minHeight: 50,
  },
  endTimeDisplay: {
    backgroundColor: "#F4F8FE",
    borderColor: "#D8E4F5",
    borderRadius: 16,
    borderWidth: 1.5,
    minHeight: 52,
    justifyContent: "center",
    paddingHorizontal: spacing.md,
  },
  endTimeDisplayText: {
    color: "#1A2842",
    fontSize: typography.body,
    fontWeight: "600",
  },
  attachmentsCard: {
    backgroundColor: colors.surface,
    borderColor: "#D8E4F5",
    borderRadius: 28,
    borderWidth: 1.5,
    marginTop: spacing.xl,
    padding: spacing.lg,
  },
  attachmentsTitle: {
    color: "#182742",
    fontSize: 19,
    fontWeight: "800",
    marginBottom: spacing.lg,
  },
  attachmentsList: {
    marginBottom: spacing.lg,
  },
  attachmentItem: {
    alignItems: "center",
    backgroundColor: "#F4F8FE",
    borderColor: "#D8E4F5",
    borderRadius: 12,
    borderWidth: 1,
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: spacing.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  attachmentName: {
    color: "#1A2842",
    flex: 1,
    fontSize: typography.body,
    fontWeight: "500",
  },
  removeButton: {
    alignItems: "center",
    justifyContent: "center",
    paddingLeft: spacing.md,
    width: 30,
  },
  removeButtonText: {
    color: "#C43F5A",
    fontSize: 18,
    fontWeight: "bold",
  },
  addAttachmentButton: {
    alignItems: "center",
    backgroundColor: "#F4F8FE",
    borderColor: "#D8E4F5",
    borderRadius: 12,
    borderWidth: 1.5,
    borderStyle: "dashed",
    justifyContent: "center",
    marginBottom: spacing.lg,
    minHeight: 50,
  },
  addAttachmentButtonText: {
    color: "#2466D8",
    fontSize: typography.body,
    fontWeight: "600",
  },
});
