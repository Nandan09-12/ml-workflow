import { router } from "expo-router";
import { useMemo, useState } from "react";
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { ApiClientError } from "@ml-workflow/api-client";

import { ScreenShell } from "../../src/components/ScreenShell";
import { apiClient } from "../../src/lib/api";
import { useSubmissions } from "../../src/submissions/SubmissionsContext";
import { colors, radius, spacing, typography } from "../../src/theme/tokens";

const regionOptions = ["NE-UP", "Central", "South"] as const;
const shiftOptions = ["AM", "PM"] as const;

type FieldErrors = Partial<Record<
  | "teamNumber"
  | "ticketNumber"
  | "workorderName"
  | "numberOfGrids"
  | "form",
  string
>>;

type StartDriveResponse = {
  id: string;
  version_number: number;
  work_date: string;
  shift: "AM" | "PM";
  team_number: string | null;
  ticket_number: string | null;
  completed_grids: number;
  skipped_grids: number;
  workorder_summary: {
    workorder_code: string;
    total_grids: number;
    region: "NE_UP" | "CENTRAL" | "SOUTH_FLORIDA";
  } | null;
};

const regionToApiValue = {
  Central: "CENTRAL",
  "NE-UP": "NE_UP",
  South: "SOUTH_FLORIDA",
} as const;

export default function DtCheckinNewScreen() {
  const { addSubmission } = useSubmissions();
  const { formattedDate, formattedTime } = useMemo(() => {
    const now = new Date();

    return {
      formattedDate: now.toISOString().slice(0, 10),
      formattedTime: now.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),
    };
  }, []);

  const [region, setRegion] = useState<(typeof regionOptions)[number]>("NE-UP");
  const [shift, setShift] = useState<(typeof shiftOptions)[number]>("AM");
  const [openDropdown, setOpenDropdown] = useState<"region" | "shift" | null>(null);
  const [teamNumber, setTeamNumber] = useState("");
  const [ticketNumber, setTicketNumber] = useState("");
  const [workorderName, setWorkorderName] = useState("");
  const [numberOfGrids, setNumberOfGrids] = useState("");
  const [errors, setErrors] = useState<FieldErrors>({});
  const [isSaving, setIsSaving] = useState(false);

  const handleSaveAsOngoing = async () => {
    const nextErrors: FieldErrors = {};
    const total = Number(numberOfGrids);

    if (!teamNumber.trim()) {
      nextErrors.teamNumber = "Team number is required";
    }
    if (!ticketNumber.trim()) {
      nextErrors.ticketNumber = "Ticket number is required";
    }
    if (!workorderName.trim()) {
      nextErrors.workorderName = "Work order name is required";
    }
    if (!numberOfGrids.trim()) {
      nextErrors.numberOfGrids = "Number of grids is required";
    } else if (Number.isNaN(total) || total <= 0) {
      nextErrors.numberOfGrids = "Enter a valid grid count";
    }

    setErrors(nextErrors);

    if (Object.keys(nextErrors).length > 0) {
      return;
    }

    setIsSaving(true);

    try {
      const response = await apiClient.post<StartDriveResponse>("/api/v1/submissions", {
        region: regionToApiValue[region],
        shift,
        team_number: teamNumber.trim(),
        ticket_number: ticketNumber.trim(),
        total_grids: total,
        work_date: formattedDate,
        workorder_code: workorderName.trim(),
      });

      const apiTotalGrids = response.workorder_summary?.total_grids ?? total;
      const apiCompletedGrids = response.completed_grids ?? 0;
      const apiSkippedGrids = response.skipped_grids ?? 0;

      addSubmission({
        backendVersionNumber: response.version_number,
        workorderName: response.workorder_summary?.workorder_code ?? workorderName.trim(),
        completedGrids: apiCompletedGrids,
        numberOfGrids: apiTotalGrids,
        pendingGrids: Math.max(apiTotalGrids - apiCompletedGrids - apiSkippedGrids, 0),
        region,
        skippedGrids: apiSkippedGrids,
        shift,
        startTime: formattedTime,
        teamNumber: response.team_number ?? teamNumber.trim(),
        ticketNumber: response.ticket_number ?? ticketNumber.trim(),
        workDate: response.work_date ?? formattedDate,
      });

      router.replace({
        params: { filter: "Ongoing" },
        pathname: "/(tabs)/dt-checkin",
      });
    } catch (error) {
      setErrors({
        form:
          error instanceof ApiClientError
            ? error.message
            : "Unable to save this submission right now.",
      });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <ScreenShell padded>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.topRow}>
          <View>
            <Text style={styles.eyebrow}>DRIVE TESTER CHECK-IN</Text>
            <Text style={styles.heading}>New submission</Text>
          </View>
          <Pressable onPress={() => router.replace("/(tabs)/fcc")} style={styles.closeButton}>
            <Text style={styles.closeLabel}>Close</Text>
          </Pressable>
        </View>

        <View style={styles.form}>
          <Field label="Work date">
            <View style={styles.valueField}>
              <Text style={styles.valueText}>{formattedDate}</Text>
            </View>
          </Field>

          <Field label="Region">
            <Pressable
              onPress={() => setOpenDropdown((current) => (current === "region" ? null : "region"))}
              style={styles.dropdownTrigger}
            >
              <Text style={styles.valueText}>{region}</Text>
              <Text style={styles.chevron}>{openDropdown === "region" ? "^" : "v"}</Text>
            </Pressable>
            {openDropdown === "region" ? (
              <View style={styles.dropdownMenu}>
                {regionOptions.map((option) => (
                  <Pressable
                    key={option}
                    onPress={() => {
                      setRegion(option);
                      setOpenDropdown(null);
                    }}
                    style={styles.dropdownOption}
                  >
                    <Text
                      style={[
                        styles.dropdownOptionText,
                        option === region && styles.dropdownOptionTextActive,
                      ]}
                    >
                      {option}
                    </Text>
                  </Pressable>
                ))}
              </View>
            ) : null}
          </Field>

          <Field label="Shift">
            <Pressable
              onPress={() => setOpenDropdown((current) => (current === "shift" ? null : "shift"))}
              style={styles.dropdownTrigger}
            >
              <Text style={styles.valueText}>{shift}</Text>
              <Text style={styles.chevron}>{openDropdown === "shift" ? "^" : "v"}</Text>
            </Pressable>
            {openDropdown === "shift" ? (
              <View style={styles.dropdownMenu}>
                {shiftOptions.map((option) => (
                  <Pressable
                    key={option}
                    onPress={() => {
                      setShift(option);
                      setOpenDropdown(null);
                    }}
                    style={styles.dropdownOption}
                  >
                    <Text
                      style={[
                        styles.dropdownOptionText,
                        option === shift && styles.dropdownOptionTextActive,
                      ]}
                    >
                      {option}
                    </Text>
                  </Pressable>
                ))}
              </View>
            ) : null}
          </Field>

          <Field label="Start time">
            <View style={styles.valueField}>
              <Text style={styles.valueText}>{formattedTime}</Text>
            </View>
          </Field>

          <Field error={errors.teamNumber} label="Team number">
            <TextInput
              keyboardType="number-pad"
              onChangeText={setTeamNumber}
              placeholder="Team number"
              placeholderTextColor="#9AA8BE"
              style={styles.inputField}
              value={teamNumber}
            />
          </Field>

          <Field error={errors.ticketNumber} label="Ticket number">
            <TextInput
              keyboardType="number-pad"
              onChangeText={setTicketNumber}
              placeholder="Ticket number"
              placeholderTextColor="#9AA8BE"
              style={styles.inputField}
              value={ticketNumber}
            />
          </Field>

          <Field error={errors.workorderName} label="Work order name">
            <TextInput
              onChangeText={setWorkorderName}
              placeholder="Work order name"
              placeholderTextColor="#9AA8BE"
              style={styles.inputField}
              value={workorderName}
            />
          </Field>

          <Field error={errors.numberOfGrids} label="Number of grids">
            <TextInput
              keyboardType="number-pad"
              onChangeText={setNumberOfGrids}
              placeholder="Number of grids"
              placeholderTextColor="#9AA8BE"
              style={styles.inputField}
              value={numberOfGrids}
            />
          </Field>
        </View>

        {errors.form ? <Text style={styles.formError}>{errors.form}</Text> : null}

        <Pressable onPress={handleSaveAsOngoing} style={styles.saveButton}>
          <Text style={styles.saveButtonLabel}>
            {isSaving ? "Saving..." : "Start Driving"}
          </Text>
        </Pressable>
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
  valueField: {
    alignItems: "center",
    backgroundColor: "#F4F8FE",
    borderColor: "#D8E4F5",
    borderRadius: 20,
    borderWidth: 1.5,
    flexDirection: "row",
    minHeight: 62,
    paddingHorizontal: spacing.lg,
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
  dropdownTrigger: {
    alignItems: "center",
    backgroundColor: "#F4F8FE",
    borderColor: "#D8E4F5",
    borderRadius: 20,
    borderWidth: 1.5,
    flexDirection: "row",
    justifyContent: "space-between",
    minHeight: 62,
    paddingHorizontal: spacing.lg,
  },
  valueText: {
    color: "#1A2842",
    fontSize: 22,
    fontWeight: "500",
  },
  chevron: {
    color: "#6C819F",
    fontSize: 18,
    fontWeight: "700",
  },
  dropdownMenu: {
    backgroundColor: colors.surface,
    borderColor: "#D8E4F5",
    borderRadius: 20,
    borderWidth: 1.5,
    overflow: "hidden",
  },
  dropdownOption: {
    paddingHorizontal: spacing.lg,
    paddingVertical: 14,
  },
  dropdownOptionText: {
    color: "#51657F",
    fontSize: 18,
    fontWeight: "500",
  },
  dropdownOptionTextActive: {
    color: "#2466D8",
    fontWeight: "700",
  },
  saveButton: {
    alignItems: "center",
    backgroundColor: "#EAF1FB",
    borderRadius: 24,
    justifyContent: "center",
    marginTop: spacing.xl,
    minHeight: 72,
  },
  saveButtonLabel: {
    color: "#1C2740",
    fontSize: typography.title,
    fontWeight: "500",
  },
  formError: {
    color: "#C43F5A",
    fontSize: typography.caption,
    lineHeight: 18,
    marginTop: spacing.lg,
  },
});
