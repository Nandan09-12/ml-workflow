import { router } from "expo-router";
import { useMemo, useState } from "react";
import { Modal, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { ApiClientError } from "@ml-workflow/api-client";

import { ScreenShell } from "../../src/components/ScreenShell";
import { apiClient } from "../../src/lib/api";
import { useSubmissions } from "../../src/submissions/SubmissionsContext";
import { colors, radius, spacing, typography } from "../../src/theme/tokens";

const regionOptions = ["NE-UP", "Central", "South"] as const;
const shiftOptions = ["AM", "PM"] as const;

type FieldErrors = Partial<Record<
  | "workDate"
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

const weekdayLabels = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"] as const;

function normalizeDate(date: Date) {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}

function getMonthStart(date: Date) {
  return new Date(date.getFullYear(), date.getMonth(), 1);
}

function padDatePart(value: number) {
  return value.toString().padStart(2, "0");
}

function formatDisplayDate(date: Date) {
  return `${padDatePart(date.getMonth() + 1)}-${padDatePart(date.getDate())}-${date.getFullYear()}`;
}

function formatApiDate(date: Date) {
  return `${date.getFullYear()}-${padDatePart(date.getMonth() + 1)}-${padDatePart(date.getDate())}`;
}

function parseDisplayDate(value: string) {
  const match = /^(\d{2})-(\d{2})-(\d{4})$/.exec(value.trim());

  if (!match) {
    return null;
  }

  const month = Number(match[1]);
  const day = Number(match[2]);
  const year = Number(match[3]);

  if (month < 1 || month > 12 || day < 1 || day > 31) {
    return null;
  }

  const parsed = new Date(year, month - 1, day);

  if (
    parsed.getFullYear() !== year ||
    parsed.getMonth() !== month - 1 ||
    parsed.getDate() !== day
  ) {
    return null;
  }

  return normalizeDate(parsed);
}

function formatDateInput(value: string) {
  const digits = value.replace(/\D/g, "").slice(0, 8);

  if (digits.length <= 2) {
    return digits;
  }

  if (digits.length <= 4) {
    return `${digits.slice(0, 2)}-${digits.slice(2)}`;
  }

  return `${digits.slice(0, 2)}-${digits.slice(2, 4)}-${digits.slice(4)}`;
}

function validateWorkDate(value: string) {
  const parsedDate = parseDisplayDate(value);

  if (!parsedDate) {
    return {
      error: "Enter date as MM-DD-YYYY",
      parsedDate: null,
    };
  }

  if (parsedDate > normalizeDate(new Date())) {
    return {
      error: "Work date cannot be in the future",
      parsedDate: null,
    };
  }

  return {
    error: null,
    parsedDate,
  };
}

function isSameDate(left: Date, right: Date) {
  return (
    left.getFullYear() === right.getFullYear() &&
    left.getMonth() === right.getMonth() &&
    left.getDate() === right.getDate()
  );
}

function buildCalendarDays(month: Date) {
  const monthStart = getMonthStart(month);
  const firstCellDate = new Date(
    monthStart.getFullYear(),
    monthStart.getMonth(),
    1 - monthStart.getDay(),
  );

  return Array.from({ length: 42 }, (_, index) => {
    const date = new Date(
      firstCellDate.getFullYear(),
      firstCellDate.getMonth(),
      firstCellDate.getDate() + index,
    );

    return {
      date,
      inCurrentMonth: date.getMonth() === monthStart.getMonth(),
      key: `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}`,
    };
  });
}

export default function DtCheckinNewScreen() {
  const { addSubmission } = useSubmissions();
  const initialDate = useMemo(() => normalizeDate(new Date()), []);
  const formattedTime = useMemo(
    () =>
      new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),
    [],
  );

  const [region, setRegion] = useState<(typeof regionOptions)[number]>("NE-UP");
  const [shift, setShift] = useState<(typeof shiftOptions)[number]>("AM");
  const [openDropdown, setOpenDropdown] = useState<"region" | "shift" | null>(null);
  const [selectedDate, setSelectedDate] = useState(initialDate);
  const [workDateInput, setWorkDateInput] = useState(() => formatDisplayDate(initialDate));
  const [calendarMonth, setCalendarMonth] = useState(() => getMonthStart(initialDate));
  const [isCalendarOpen, setIsCalendarOpen] = useState(false);
  const [teamNumber, setTeamNumber] = useState("");
  const [ticketNumber, setTicketNumber] = useState("");
  const [workorderName, setWorkorderName] = useState("");
  const [numberOfGrids, setNumberOfGrids] = useState("");
  const [errors, setErrors] = useState<FieldErrors>({});
  const [isSaving, setIsSaving] = useState(false);
  const calendarDays = useMemo(() => buildCalendarDays(calendarMonth), [calendarMonth]);
  const calendarHeading = useMemo(
    () =>
      calendarMonth.toLocaleDateString("en-US", {
        month: "long",
        year: "numeric",
      }),
    [calendarMonth],
  );

  const applySelectedDate = (date: Date) => {
    const normalizedDate = normalizeDate(date);

    setSelectedDate(normalizedDate);
    setWorkDateInput(formatDisplayDate(normalizedDate));
    setCalendarMonth(getMonthStart(normalizedDate));
    setErrors((current) => ({ ...current, workDate: undefined }));
  };

  const handleWorkDateBlur = () => {
    const result = validateWorkDate(workDateInput);

    if (result.error || !result.parsedDate) {
      setErrors((current) => ({ ...current, workDate: result.error ?? undefined }));
      return;
    }

    applySelectedDate(result.parsedDate);
  };

  const handleSaveAsOngoing = async () => {
    const nextErrors: FieldErrors = {};
    const total = Number(numberOfGrids);
    const workDateResult = validateWorkDate(workDateInput);

    if (workDateResult.error) {
      nextErrors.workDate = workDateResult.error;
    }
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
      const apiWorkDate = formatApiDate(workDateResult.parsedDate ?? selectedDate);

      const response = await apiClient.post<StartDriveResponse>("/api/v1/submissions", {
        region: regionToApiValue[region],
        shift,
        team_number: teamNumber.trim(),
        ticket_number: ticketNumber.trim(),
        total_grids: total,
        work_date: apiWorkDate,
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
        workDate: response.work_date ?? apiWorkDate,
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
    <ScreenShell backFallbackHref="/(tabs)/dt-checkin" padded scrollable={false}>
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
          <Field error={errors.workDate} label="Work date">
            <View style={styles.dateInputRow}>
              <TextInput
                keyboardType="number-pad"
                maxLength={10}
                onBlur={handleWorkDateBlur}
                onChangeText={(value) => {
                  setWorkDateInput(formatDateInput(value));
                  setErrors((current) => ({ ...current, workDate: undefined }));
                }}
                placeholder="MM-DD-YYYY"
                placeholderTextColor="#9AA8BE"
                style={styles.dateInputField}
                value={workDateInput}
              />
              <Pressable
                onPress={() => {
                  setOpenDropdown(null);
                  setIsCalendarOpen(true);
                }}
                style={styles.calendarButton}
              >
                <Text style={styles.calendarButtonText}>Calendar</Text>
              </Pressable>
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

      <Modal
        animationType="fade"
        onRequestClose={() => setIsCalendarOpen(false)}
        transparent
        visible={isCalendarOpen}
      >
        <View style={styles.modalBackdrop}>
          <View style={styles.calendarModal}>
            <View style={styles.calendarHeader}>
              <Text style={styles.calendarTitle}>Select work date</Text>
              <Pressable onPress={() => setIsCalendarOpen(false)} style={styles.calendarHeaderButton}>
                <Text style={styles.calendarHeaderButtonText}>Close</Text>
              </Pressable>
            </View>

            <View style={styles.calendarNavRow}>
              <Pressable
                onPress={() =>
                  setCalendarMonth(
                    (current) => new Date(current.getFullYear(), current.getMonth() - 1, 1),
                  )
                }
                style={styles.calendarNavButton}
              >
                <Text style={styles.calendarNavButtonText}>{"<"}</Text>
              </Pressable>

              <Text style={styles.calendarMonthLabel}>{calendarHeading}</Text>

              <Pressable
                onPress={() =>
                  setCalendarMonth(
                    (current) => new Date(current.getFullYear(), current.getMonth() + 1, 1),
                  )
                }
                style={styles.calendarNavButton}
              >
                <Text style={styles.calendarNavButtonText}>{">"}</Text>
              </Pressable>
            </View>

            <View style={styles.calendarWeekdays}>
              {weekdayLabels.map((label) => (
                <Text key={label} style={styles.calendarWeekdayText}>
                  {label}
                </Text>
              ))}
            </View>

            <View style={styles.calendarGrid}>
              {calendarDays.map((day) => {
                const isSelected = isSameDate(day.date, selectedDate);

                return (
                  <Pressable
                    key={day.key}
                    onPress={() => {
                      applySelectedDate(day.date);
                      setIsCalendarOpen(false);
                    }}
                    style={[
                      styles.calendarDayButton,
                      !day.inCurrentMonth && styles.calendarDayButtonMuted,
                      isSelected && styles.calendarDayButtonSelected,
                    ]}
                  >
                    <Text
                      style={[
                        styles.calendarDayText,
                        !day.inCurrentMonth && styles.calendarDayTextMuted,
                        isSelected && styles.calendarDayTextSelected,
                      ]}
                    >
                      {day.date.getDate()}
                    </Text>
                  </Pressable>
                );
              })}
            </View>
          </View>
        </View>
      </Modal>
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
  dateInputRow: {
    flexDirection: "row",
    gap: spacing.sm,
  },
  dateInputField: {
    backgroundColor: "#F4F8FE",
    borderColor: "#D8E4F5",
    borderRadius: 20,
    borderWidth: 1.5,
    color: "#1A2842",
    flex: 1,
    fontSize: 22,
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
  calendarButton: {
    alignItems: "center",
    backgroundColor: "#EAF1FB",
    borderRadius: 20,
    justifyContent: "center",
    minHeight: 62,
    minWidth: 116,
    paddingHorizontal: spacing.md,
  },
  calendarButtonText: {
    color: "#24334E",
    fontSize: 16,
    fontWeight: "700",
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
  modalBackdrop: {
    alignItems: "center",
    backgroundColor: "rgba(10, 21, 39, 0.35)",
    flex: 1,
    justifyContent: "center",
    paddingHorizontal: spacing.lg,
  },
  calendarModal: {
    backgroundColor: colors.surface,
    borderRadius: 28,
    padding: spacing.lg,
    width: "100%",
  },
  calendarHeader: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
  },
  calendarTitle: {
    color: "#182742",
    fontSize: 20,
    fontWeight: "800",
  },
  calendarHeaderButton: {
    backgroundColor: "#EAF1FB",
    borderRadius: radius.lg,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  calendarHeaderButtonText: {
    color: "#24334E",
    fontSize: 15,
    fontWeight: "700",
  },
  calendarNavRow: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: spacing.lg,
  },
  calendarNavButton: {
    alignItems: "center",
    backgroundColor: "#F4F8FE",
    borderRadius: radius.lg,
    height: 44,
    justifyContent: "center",
    width: 44,
  },
  calendarNavButtonText: {
    color: "#24334E",
    fontSize: 18,
    fontWeight: "700",
  },
  calendarMonthLabel: {
    color: "#182742",
    fontSize: 18,
    fontWeight: "700",
  },
  calendarWeekdays: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: spacing.lg,
  },
  calendarWeekdayText: {
    color: "#6C819F",
    flex: 1,
    fontSize: 12,
    fontWeight: "700",
    textAlign: "center",
  },
  calendarGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between",
    marginTop: spacing.sm,
  },
  calendarDayButton: {
    alignItems: "center",
    borderRadius: 16,
    justifyContent: "center",
    marginBottom: spacing.xs,
    minHeight: 44,
    width: "14%",
  },
  calendarDayButtonMuted: {
    backgroundColor: "#F8FAFD",
  },
  calendarDayButtonSelected: {
    backgroundColor: "#2466D8",
  },
  calendarDayText: {
    color: "#1A2842",
    fontSize: 15,
    fontWeight: "600",
  },
  calendarDayTextMuted: {
    color: "#9AA8BE",
  },
  calendarDayTextSelected: {
    color: colors.surface,
  },
});
