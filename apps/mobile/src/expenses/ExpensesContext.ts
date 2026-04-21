import { createContext, useContext } from "react";

import type { ExpensePayload, ExpenseRecord } from "./types";

export type ExpensesContextValue = {
  expenses: ExpenseRecord[];
  saveExpense: (payload: ExpensePayload) => ExpenseRecord;
};

export const ExpensesContext = createContext<ExpensesContextValue | null>(null);

export function useExpenses() {
  const value = useContext(ExpensesContext);

  if (!value) {
    throw new Error("useExpenses must be used inside ExpensesProvider");
  }

  return value;
}
