import * as DocumentPicker from "expo-document-picker";
import { router } from "expo-router";
import { useMemo } from "react";
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { useState } from "react";

import { ScreenShell } from "../../src/components/ScreenShell";
import { useMileage } from "../../src/mileage/MileageContext";
import type { MileagePayload } from "../../src/mileage/types";
import { colors, radius, spacing, typography } from "../../src/theme/tokens";

type FieldErrors = Partial<
  Record<"date" | "endMileage" | "endTime" | "odometerImage" | "startMileage" | "startTime", string>
>;

export default function MileageTrackerScreen() {
  const { mileages, saveMileage } = useMileage();
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
  const [date, setDate] = useState(defaults.date);
  const [startTime, setStartTime] = useState(defaults.time);
  const [startMileage, setStartMileage] = useState("");
  const [endTime, setEndTime] = useState(defaults.time);
  const [endMileage, setEndMileage] = useState("");
  const [odometerImage, setOdometerImage] = useState<MileagePayload["odometerImage"] | null>(null);
  const [errors, setErrors] = useState<FieldErrors>({});

  const pickOdometerImage = async () => {
    const result = await DocumentPicker.getDocumentAsync({
      copyToCacheDirectory: true,
      multiple: false,
      type: ["image/*"],
    });

    if (result.canceled) {
      return;
    }

    const asset = result.assets[0];
    setOdometerImage({
      mimeType: asset.mimeType ?? null,
      name: asset.name,
      uri: asset.uri,
    });
  };

  const handleSave = () => {
    const nextErrors: FieldErrors = {};

    if (!date.trim()) {
      nextErrors.date = "Date is required";
    }
    if (!startTime.trim()) {
      nextErrors.startTime = "Start time is required";
    }
    if (!startMileage.trim()) {
      nextErrors.startMileage = "Start mileage is required";
    }
    if (!endTime.trim()) {
      nextErrors.endTime = "End time is required";
    }
    if (!endMileage.trim()) {
      nextErrors.endMileage = "End mileage is required";
    }
    if (!odometerImage) {
      nextErrors.odometerImage = "Odometer image is required";
    }

    setErrors(nextErrors);

    if (Object.keys(nextErrors).length > 0 || !odometerImage) {
      return;
    }

    saveMileage({
      date,
      endMileage,
      endTime,
      odometerImage,
      startMileage,
      startTime,
    });
  };

  return (
    <ScreenShell padded>
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
          <Field error={errors.date} label="Date">
            <TextInput
              onChangeText={setDate}
              placeholder="YYYY-MM-DD"
              placeholderTextColor="#9AA8BE"
              style={styles.inputField}
              value={date}
            />
          </Field>

          <Field error={errors.startTime} label="Start time">
            <TextInput
              onChangeText={setStartTime}
              placeholder="Start time"
              placeholderTextColor="#9AA8BE"
              style={styles.inputField}
              value={startTime}
            />
          </Field>

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

          <Field error={errors.endTime} label="End time">
            <TextInput
              onChangeText={setEndTime}
              placeholder="End time"
              placeholderTextColor="#9AA8BE"
              style={styles.inputField}
              value={endTime}
            />
          </Field>

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

          <Field error={errors.odometerImage} label="Odometer image">
            <Pressable onPress={pickOdometerImage} style={styles.imageButton}>
              <Text style={styles.imageButtonLabel}>
                {odometerImage ? odometerImage.name : "Take / choose odometer image"}
              </Text>
            </Pressable>
          </Field>
        </View>

        <Pressable onPress={handleSave} style={styles.saveButton}>
          <Text style={styles.saveButtonLabel}>Save mileage</Text>
        </Pressable>

        {mileages.length > 0 ? (
          <View style={styles.payloadCard}>
            <Text style={styles.payloadTitle}>Latest payload</Text>
            <Text style={styles.payloadText}>{JSON.stringify(mileages[0], null, 2)}</Text>
          </View>
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
  },
  saveButtonLabel: {
    color: colors.surface,
    fontSize: typography.title,
    fontWeight: "800",
  },
  payloadCard: {
    backgroundColor: "#F4F8FE",
    borderColor: "#D8E4F5",
    borderRadius: 24,
    borderWidth: 1.5,
    marginTop: spacing.xl,
    padding: spacing.lg,
  },
  payloadTitle: {
    color: "#182742",
    fontSize: 18,
    fontWeight: "800",
    marginBottom: spacing.md,
  },
  payloadText: {
    color: "#51657F",
    fontSize: 13,
    lineHeight: 18,
  },
});
