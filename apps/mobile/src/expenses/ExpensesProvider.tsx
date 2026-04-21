import { PropsWithChildren, useCallback, useMemo, useState } from "react";

import { apiClient } from "../lib/api";
import { ExpensesContext } from "./ExpensesContext";
import type { ExpensePayload, ExpenseRecord } from "./types";

type BackendExpenseEntry = {
  amount: number;
  category: string;
  created_at: string;
  expense_date: string;
  id: string;
  owner_user_id: string;
  receipt_file_name: string;
};

type ListExpensesResponse = {
  count: number;
  items: BackendExpenseEntry[];
};

function toExpenseRecord(entry: BackendExpenseEntry): ExpenseRecord {
  return {
    amount: entry.amount,
    category: entry.category as ExpenseRecord["category"],
    createdAt: entry.created_at,
    date: entry.expense_date,
    id: entry.id,
    ownerUserId: entry.owner_user_id,
    receiptFileName: entry.receipt_file_name,
  };
}

export function ExpensesProvider({ children }: PropsWithChildren) {
  const [expenses, setExpenses] = useState<ExpenseRecord[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const loadExpenses = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await apiClient.get<ListExpensesResponse>("/api/v1/expenses");
      const mapped = data.items.map(toExpenseRecord);
      setExpenses(mapped);
      return mapped;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const saveExpense = useCallback(async (payload: ExpensePayload) => {
    const formData = new FormData();
    formData.append("expense_date", payload.date);
    formData.append("amount", payload.amount);
    formData.append("category", payload.category);
    formData.append("receipt", {
      uri: payload.receipt.uri,
      name: payload.receipt.name,
      type: payload.receipt.mimeType ?? "image/jpeg",
    } as unknown as Blob);

    const created = await apiClient.post<BackendExpenseEntry>("/api/v1/expenses", formData);
    const mapped = toExpenseRecord(created);
    setExpenses((current) => [mapped, ...current]);
    return mapped;
  }, []);

  const value = useMemo(
    () => ({
      expenses,
      isLoading,
      loadExpenses,
      saveExpense,
    }),
    [expenses, isLoading, loadExpenses, saveExpense],
  );

  return <ExpensesContext.Provider value={value}>{children}</ExpensesContext.Provider>;
}
