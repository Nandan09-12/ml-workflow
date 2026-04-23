import * as DocumentPicker from "expo-document-picker";
import { router, useFocusEffect } from "expo-router";
import { ApiClientError } from "@ml-workflow/api-client";
import { useCallback, useMemo, useState } from "react";
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";

import { ScreenShell } from "../../src/components/ScreenShell";
import { useExpenses } from "../../src/expenses/ExpensesContext";
import type { ExpenseCategory, ExpensePayload, ExpenseRecord } from "../../src/expenses/types";
import { colors, radius, spacing, typography } from "../../src/theme/tokens";

const categoryOptions: ExpenseCategory[] = ["gas", "food", "room", "other"];

type FieldErrors = Partial<Record<"amount" | "date" | "receipt", string>>;
type ViewMode = "list" | "form";

function padDatePart(value: number) {
  return value.toString().padStart(2, "0");
}

function formatApiDate(date: Date) {
  return `${date.getFullYear()}-${padDatePart(date.getMonth() + 1)}-${padDatePart(date.getDate())}`;
}

function formatExpenseDate(dateString: string) {
  const [year, month, day] = dateString.split("-").map(Number);
  const date = new Date(year, month - 1, day);

  return date.toLocaleDateString("en-US", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function formatExpenseAmount(amount: number) {
  return new Intl.NumberFormat("en-US", {
    currency: "USD",
    style: "currency",
  }).format(amount);
}

function categoryLabel(category: ExpenseRecord["category"]) {
  return category.toUpperCase();
}

export default function DtExpensesScreen() {
  const { expenses, isLoading, loadExpenses, saveExpense } = useExpenses();
  const today = useMemo(() => formatApiDate(new Date()), []);
  const [viewMode, setViewMode] = useState<ViewMode>("list");
  const [date, setDate] = useState(today);
  const [amount, setAmount] = useState("");
  const [category, setCategory] = useState<ExpenseCategory>("gas");
  const [categoryOpen, setCategoryOpen] = useState(false);
  const [receipt, setReceipt] = useState<ExpensePayload["receipt"] | null>(null);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const resetForm = useCallback(() => {
    setDate(today);
    setAmount("");
    setCategory("gas");
    setCategoryOpen(false);
    setReceipt(null);
    setErrors({});
    setFormError(null);
  }, [today]);

  const openNewExpense = useCallback(() => {
    resetForm();
    setViewMode("form");
  }, [resetForm]);

  useFocusEffect(
    useCallback(() => {
      let active = true;

      const run = async () => {
        try {
          setLoadError(null);
          const items = await loadExpenses();

          if (!active) {
            return;
          }

          if (items.length > 0) {
            setViewMode("list");
          }
        } catch (error) {
          if (!active) {
            return;
          }

          setLoadError(
            error instanceof ApiClientError
              ? error.message
              : "Unable to load expenses right now.",
          );
        }
      };

      void run();

      return () => {
        active = false;
      };
    }, [loadExpenses]),
  );

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
    setErrors((current) => ({ ...current, receipt: undefined }));
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

    setIsSaving(true);

    try {
      await saveExpense({
        amount,
        category,
        date,
        receipt,
      });
      resetForm();
      setViewMode("list");
    } catch (error: unknown) {
      setFormError(
        error instanceof ApiClientError ? error.message : "Unable to save expense right now.",
      );
    } finally {
      setIsSaving(false);
    }
  };

  const showList = viewMode === "list";

  return (
    <ScreenShell padded>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.topRow}>
          <View>
            <Text style={styles.eyebrow}>DT EXPENSES</Text>
            <Text style={styles.heading}>{showList ? "My expenses" : "New expense"}</Text>
          </View>
          {showList ? (
            <Pressable onPress={() => router.replace("/(tabs)/fcc")} style={styles.modulesButton}>
              <Text style={styles.modulesLabel}>Modules</Text>
            </Pressable>
          ) : (
            <Pressable
              onPress={() => {
                setCategoryOpen(false);
                setViewMode("list");
              }}
              style={styles.modulesButton}
            >
              <Text style={styles.modulesLabel}>Back</Text>
            </Pressable>
          )}
        </View>

        {loadError ? <Text style={styles.loadErrorText}>{loadError}</Text> : null}

        {showList ? (
          <View style={styles.cardList}>
            {!isLoading && expenses.length === 0 ? (
              <View style={styles.emptyCard}>
                <Text style={styles.emptyTitle}>No expenses found</Text>
                <Text style={styles.emptySubtitle}>
                  You have not logged any expenses yet. Use the button below to add a new one.
                </Text>
              </View>
            ) : null}

            {expenses.map((expense) => (
              <View key={expense.id} style={styles.expenseCard}>
                <View style={styles.expenseHeader}>
                  <Text style={styles.expenseAmount}>{formatExpenseAmount(expense.amount)}</Text>
                  <View style={styles.categoryChip}>
                    <Text style={styles.categoryChipText}>{categoryLabel(expense.category)}</Text>
                  </View>
                </View>
                <Text style={styles.expenseMeta}>{formatExpenseDate(expense.date)}</Text>
                <Text style={styles.expenseReceipt}>Receipt: {expense.receiptFileName}</Text>
              </View>
            ))}
          </View>
        ) : (
          <>
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

            <Pressable disabled={isSaving} onPress={handleSave} style={styles.saveButton}>
              <Text style={styles.saveButtonLabel}>
                {isSaving ? "Saving..." : "Save expense"}
              </Text>
            </Pressable>

            {formError ? <Text style={styles.formError}>{formError}</Text> : null}
          </>
        )}
      </ScrollView>

      {showList ? (
        <View style={styles.footer}>
          <Pressable onPress={openNewExpense} style={styles.newButton}>
            <Text style={styles.newButtonLabel}>+ New expense</Text>
          </Pressable>
        </View>
      ) : null}
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
    minWidth: 104,
    paddingHorizontal: spacing.md,
    paddingVertical: 14,
  },
  modulesLabel: {
    color: "#24334E",
    fontSize: 18,
    fontWeight: "600",
    textAlign: "center",
  },
  loadErrorText: {
    color: "#C43F5A",
    fontSize: typography.caption,
    marginTop: spacing.lg,
  },
  cardList: {
    gap: spacing.lg,
    marginTop: spacing.xl,
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
  expenseCard: {
    backgroundColor: colors.surface,
    borderColor: "#D8E4F5",
    borderRadius: 30,
    borderWidth: 1.5,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.lg,
  },
  expenseHeader: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
  },
  expenseAmount: {
    color: "#111A2A",
    flex: 1,
    fontSize: 24,
    fontWeight: "800",
    paddingRight: spacing.md,
  },
  categoryChip: {
    backgroundColor: "#E9EFF8",
    borderRadius: radius.pill,
    paddingHorizontal: spacing.lg,
    paddingVertical: 10,
  },
  categoryChipText: {
    color: "#6B7E99",
    fontSize: 14,
    fontWeight: "800",
  },
  expenseMeta: {
    color: "#7084A0",
    fontSize: 18,
    fontWeight: "500",
    marginTop: spacing.lg,
  },
  expenseReceipt: {
    color: "#51657F",
    fontSize: 16,
    lineHeight: 22,
    marginTop: spacing.sm,
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
