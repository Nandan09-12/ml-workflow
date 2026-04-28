import * as DocumentPicker from "expo-document-picker";
import { ApiClientError } from "@ml-workflow/api-client";
import { router } from "expo-router";
import { useEffect, useMemo } from "react";
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { useState } from "react";

import { ScreenShell } from "../../src/components/ScreenShell";
import { useMileage } from "../../src/mileage/MileageContext";
import type { EndMileagePayload, MileageImageAsset, StartMileagePayload } from "../../src/mileage/types";
import { colors, radius, spacing, typography } from "../../src/theme/tokens";

type FieldErrors = Partial<
  Record<"date" | "endMileage" | "endOdometerImage" | "startMileage" | "startOdometerImage", string>
>;

export default function MileageTrackerScreen() {
  const { currentMileage, endShift, isLoading, loadMileageForDate, startShift } = useMileage();
  const defaults = useMemo(() => {
    const now = new Date();
    return {
      date: now.toISOString().slice(0, 10),
      time: now.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),
    };
  }, []);
  const [date] = useState(defaults.date);
  const [startMileage, setStartMileage] = useState("");
  const [endMileage, setEndMileage] = useState("");
  const [startOdometerImage, setStartOdometerImage] = useState<MileageImageAsset | null>(null);
  const [endOdometerImage, setEndOdometerImage] = useState<MileageImageAsset | null>(null);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    void loadMileageForDate(date).catch((error) => {
      setFormError(error instanceof Error ? error.message : "Unable to load mileage entry.");
    });
  }, [date, loadMileageForDate]);

  const pickOdometerImage = async (setter: (asset: MileageImageAsset | null) => void) => {
    const result = await DocumentPicker.getDocumentAsync({
      copyToCacheDirectory: true,
      multiple: false,
      type: ["image/*"],
    });

    if (result.canceled) {
      return;
    }

    const asset = result.assets[0];
    setter({
      mimeType: asset.mimeType ?? null,
      name: asset.name,
      uri: asset.uri,
    });
  };

  const handleSave = async () => {
    const nextErrors: FieldErrors = {};
    setFormError(null);

    if (!date.trim()) {
      nextErrors.date = "Date is required";
    }
    if (!currentMileage && !startMileage.trim()) {
      nextErrors.startMileage = "Start mileage is required";
    }
    if (!currentMileage && !startOdometerImage) {
      nextErrors.startOdometerImage = "Start odometer image is required";
    }
    if (currentMileage && !currentMileage.isCompleted && !endMileage.trim()) {
      nextErrors.endMileage = "End mileage is required";
    }
    if (currentMileage && !currentMileage.isCompleted && !endOdometerImage) {
      nextErrors.endOdometerImage = "End odometer image is required";
    }

    setErrors(nextErrors);

    if (Object.keys(nextErrors).length > 0) {
      return;
    }

    setIsSubmitting(true);
    try {
      if (!currentMileage) {
        await startShift({
          odometerImage: startOdometerImage as StartMileagePayload["odometerImage"],
          startMileage,
          workDate: date,
        });
        setStartOdometerImage(null);
        setStartMileage("");
      } else if (!currentMileage.isCompleted) {
        await endShift({
          endMileage,
          odometerImage: endOdometerImage as EndMileagePayload["odometerImage"],
          workDate: date,
        });
        setEndMileage("");
        setEndOdometerImage(null);
      }
    } catch (error) {
      if (error instanceof ApiClientError) {
        setFormError(error.message);
      } else {
        setFormError(error instanceof Error ? error.message : "Unable to save mileage entry.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const startTimeLabel = currentMileage
    ? new Date(currentMileage.startedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    : defaults.time;
  const endTimeLabel =
    currentMileage?.endedAt != null
      ? new Date(currentMileage.endedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
      : defaults.time;
  const isStartMode = currentMileage == null;
  const isEndMode = currentMileage != null && !currentMileage.isCompleted;
  const isCompletedMode = currentMileage?.isCompleted === true;

  return (
    <ScreenShell backFallbackHref="/(tabs)/fcc" padded scrollable={false}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.topRow}>
          <View>
            <Text style={styles.eyebrow}>MILEAGE TRACKER</Text>
            <Text style={styles.heading}>New mileage entry</Text>
          </View>
          <Pressable onPress={() => router.replace("/(tabs)/fcc")} style={styles.closeButton}>
            <Text style={styles.closeLabel}>Close</Text>
          </Pressable>
        </View>

        <View style={styles.form}>
          <InfoField label="Date" value={date} />

          {currentMileage ? (
            <View style={styles.summaryCard}>
              <Text style={styles.summaryTitle}>Shift started</Text>
              <SummaryRow label="Start time" value={startTimeLabel} />
              <SummaryRow label="Start mileage" value={String(currentMileage.startMileage)} />
              <SummaryRow label="Start odometer" value={currentMileage.startOdometerFileName} />
            </View>
          ) : null}

          {isStartMode ? (
            <>
              <InfoField label="Start time" value={startTimeLabel} />
              <Field error={errors.startMileage} label="Start mileage">
                <TextInput
                  keyboardType="number-pad"
                  onChangeText={setStartMileage}
                  placeholder="Start mileage"
                  placeholderTextColor="#9AA8BE"
                  style={styles.inputField}
                  value={startMileage}
                />
              </Field>
              <Field error={errors.startOdometerImage} label="Start odometer image">
                <Pressable onPress={() => void pickOdometerImage(setStartOdometerImage)} style={styles.imageButton}>
                  <Text style={styles.imageButtonLabel}>
                    {startOdometerImage ? startOdometerImage.name : "Take / choose start odometer image"}
                  </Text>
                </Pressable>
              </Field>
            </>
          ) : null}

          {isEndMode ? (
            <>
              <InfoField label="End time" value={endTimeLabel} />
              <Field error={errors.endMileage} label="End mileage">
                <TextInput
                  keyboardType="number-pad"
                  onChangeText={setEndMileage}
                  placeholder="End mileage"
                  placeholderTextColor="#9AA8BE"
                  style={styles.inputField}
                  value={endMileage}
                />
              </Field>
              <Field error={errors.endOdometerImage} label="End odometer image">
                <Pressable onPress={() => void pickOdometerImage(setEndOdometerImage)} style={styles.imageButton}>
                  <Text style={styles.imageButtonLabel}>
                    {endOdometerImage ? endOdometerImage.name : "Take / choose end odometer image"}
                  </Text>
                </Pressable>
              </Field>
            </>
          ) : null}

          {isCompletedMode ? (
            <View style={styles.summaryCard}>
              <Text style={styles.summaryTitle}>Shift completed</Text>
              <SummaryRow label="End time" value={endTimeLabel} />
              <SummaryRow label="End mileage" value={String(currentMileage.endMileage ?? "")} />
              <SummaryRow label="End odometer" value={currentMileage.endOdometerFileName ?? "-"} />
            </View>
          ) : null}
        </View>

        {formError ? <Text style={styles.formError}>{formError}</Text> : null}

        {!isCompletedMode ? (
          <Pressable disabled={isSubmitting || isLoading} onPress={() => void handleSave()} style={styles.saveButton}>
            <Text style={styles.saveButtonLabel}>
              {isSubmitting
                ? "Saving..."
                : isStartMode
                  ? "Start shift"
                  : "End shift"}
            </Text>
          </Pressable>
        ) : null}
      </ScrollView>
    </ScreenShell>
  );
}

function Field({
  children,
  error,
  label,
}: {
  children: React.ReactNode;
  error?: string;
  label: string;
}) {
  return (
    <View style={styles.fieldBlock}>
      <Text style={styles.fieldLabel}>{label}</Text>
      {children}
      {error ? <Text style={styles.errorText}>{error}</Text> : null}
    </View>
  );
}

function InfoField({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.fieldBlock}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <View style={styles.infoField}>
        <Text style={styles.infoFieldText}>{value}</Text>
      </View>
    </View>
  );
}

function SummaryRow({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.summaryRow}>
      <Text style={styles.summaryLabel}>{label}</Text>
      <Text style={styles.summaryValue}>{value}</Text>
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
  form: {
    gap: spacing.md,
    marginTop: spacing.xl,
  },
  fieldBlock: {
    gap: spacing.sm,
  },
  fieldLabel: {
    color: "#6C819F",
    fontSize: 16,
    fontWeight: "700",
  },
  errorText: {
    color: "#C43F5A",
    fontSize: typography.caption,
  },
  formError: {
    color: "#C43F5A",
    fontSize: typography.body,
    marginTop: spacing.lg,
    textAlign: "center",
  },
  infoField: {
    backgroundColor: "#F8FBFF",
    borderColor: "#D8E4F5",
    borderRadius: 20,
    borderWidth: 1.5,
    minHeight: 62,
    justifyContent: "center",
    paddingHorizontal: spacing.lg,
  },
  infoFieldText: {
    color: "#1A2842",
    fontSize: 20,
    fontWeight: "600",
  },
  inputField: {
    backgroundColor: "#F4F8FE",
    borderColor: "#D8E4F5",
    borderRadius: 20,
    borderWidth: 1.5,
    color: "#1A2842",
    fontSize: 22,
    minHeight: 62,
    paddingHorizontal: spacing.lg,
  },
  imageButton: {
    alignItems: "center",
    backgroundColor: "#F4F8FE",
    borderColor: "#D8E4F5",
    borderRadius: 20,
    borderStyle: "dashed",
    borderWidth: 1.5,
    justifyContent: "center",
    minHeight: 72,
    paddingHorizontal: spacing.lg,
  },
  imageButtonLabel: {
    color: "#51657F",
    fontSize: 18,
    fontWeight: "500",
    textAlign: "center",
  },
  saveButton: {
    alignItems: "center",
    backgroundColor: "#2466D8",
    borderRadius: 24,
    justifyContent: "center",
    marginTop: spacing.xl,
    minHeight: 72,
    opacity: 1,
  },
  saveButtonLabel: {
    color: colors.surface,
    fontSize: typography.title,
    fontWeight: "800",
  },
  summaryCard: {
    backgroundColor: "#F8FBFF",
    borderColor: "#D8E4F5",
    borderRadius: 24,
    borderWidth: 1.5,
    padding: spacing.lg,
  },
  summaryTitle: {
    color: "#182742",
    fontSize: 18,
    fontWeight: "800",
    marginBottom: spacing.md,
  },
  summaryRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: spacing.sm,
  },
  summaryLabel: {
    color: "#6C819F",
    fontSize: 15,
    fontWeight: "600",
  },
  summaryValue: {
    color: "#1A2842",
    fontSize: 15,
    fontWeight: "700",
  },
});
