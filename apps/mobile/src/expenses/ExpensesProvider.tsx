import { PropsWithChildren, useMemo, useState } from "react";

import { ExpensesContext } from "./ExpensesContext";
import type { ExpensePayload, ExpenseRecord } from "./types";

export function ExpensesProvider({ children }: PropsWithChildren) {
  const [expenses, setExpenses] = useState<ExpenseRecord[]>([]);

  const value = useMemo(
    () => ({
      expenses,
      saveExpense: (payload: ExpensePayload) => {
        const record: ExpenseRecord = {
          ...payload,
          createdAt: new Date().toISOString(),
          id: String(Date.now()),
        };

        setExpenses((current) => [record, ...current]);
        return record;
      },
    }),
    [expenses],
  );

  return <ExpensesContext.Provider value={value}>{children}</ExpensesContext.Provider>;
}
