import * as DocumentPicker from "expo-document-picker";
import { router } from "expo-router";
import { ApiClientError } from "@ml-workflow/api-client";
import { useEffect, useMemo, useState } from "react";
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";

import { ScreenShell } from "../../src/components/ScreenShell";
import { useExpenses } from "../../src/expenses/ExpensesContext";
import type { ExpenseCategory, ExpensePayload } from "../../src/expenses/types";
import { colors, radius, spacing, typography } from "../../src/theme/tokens";

const categoryOptions: ExpenseCategory[] = ["gas", "food", "room", "other"];

type FieldErrors = Partial<Record<"amount" | "date" | "receipt", string>>;

export default function DtExpensesScreen() {
  const { expenses, loadExpenses, saveExpense } = useExpenses();
  const today = useMemo(() => new Date().toISOString().slice(0, 10), []);
  const [date, setDate] = useState(today);
  const [amount, setAmount] = useState("");
  const [category, setCategory] = useState<ExpenseCategory>("gas");
  const [categoryOpen, setCategoryOpen] = useState(false);
  const [receipt, setReceipt] = useState<ExpensePayload["receipt"] | null>(null);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    void loadExpenses();
  }, [loadExpenses]);

  const pickReceipt = async () => {
    const result = await DocumentPicker.getDocumentAsync({
      copyToCacheDirectory: true,
      multiple: false,
      type: ["image/*"],
    });

    if (result.canceled) {
      return;
    }

    const asset = result.assets[0];
    setReceipt({
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
    if (!amount.trim()) {
      nextErrors.amount = "Amount is required";
    }
    if (!receipt) {
      nextErrors.receipt = "Receipt image is required";
    }

    setErrors(nextErrors);

    if (Object.keys(nextErrors).length > 0 || !receipt) {
      return;
    }

    try {
      await saveExpense({
        amount,
        category,
        date,
        receipt,
      });
      setAmount("");
      setCategory("gas");
      setCategoryOpen(false);
      setReceipt(null);
      setErrors({});
    } catch (error: unknown) {
      setFormError(
        error instanceof ApiClientError ? error.message : "Unable to save expense right now.",
      );
    }
  };

  return (
    <ScreenShell padded>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.topRow}>
          <View>
            <Text style={styles.eyebrow}>DT EXPENSES</Text>
            <Text style={styles.heading}>New expense</Text>
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

          <Field error={errors.amount} label="Amount">
            <TextInput
              keyboardType="decimal-pad"
              onChangeText={setAmount}
              placeholder="Amount"
              placeholderTextColor="#9AA8BE"
              style={styles.inputField}
              value={amount}
            />
          </Field>

          <Field error={errors.receipt} label="Receipt">
            <Pressable onPress={pickReceipt} style={styles.receiptButton}>
              <Text style={styles.receiptButtonLabel}>
                {receipt ? receipt.name : "Take / choose receipt image"}
              </Text>
            </Pressable>
          </Field>

          <Field label="Category">
            <Pressable
              onPress={() => setCategoryOpen((current) => !current)}
              style={styles.dropdownTrigger}
            >
              <Text style={styles.valueText}>{category.toUpperCase()}</Text>
              <Text style={styles.chevron}>{categoryOpen ? "^" : "v"}</Text>
            </Pressable>
            {categoryOpen ? (
              <View style={styles.dropdownMenu}>
                {categoryOptions.map((option) => (
                  <Pressable
                    key={option}
                    onPress={() => {
                      setCategory(option);
                      setCategoryOpen(false);
                    }}
                    style={styles.dropdownOption}
                  >
                    <Text
                      style={[
                        styles.dropdownOptionText,
                        option === category && styles.dropdownOptionTextActive,
                      ]}
                    >
                      {option.toUpperCase()}
                    </Text>
                  </Pressable>
                ))}
              </View>
            ) : null}
          </Field>

        </View>

        <Pressable onPress={handleSave} style={styles.saveButton}>
          <Text style={styles.saveButtonLabel}>Save expense</Text>
        </Pressable>

        {formError ? <Text style={styles.formError}>{formError}</Text> : null}

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
  receiptButton: {
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
  receiptButtonLabel: {
    color: "#51657F",
    fontSize: 18,
    fontWeight: "500",
    textAlign: "center",
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
  formError: {
    color: "#C43F5A",
    fontSize: typography.caption,
    marginTop: spacing.sm,
  },
});
