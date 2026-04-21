export type ExpenseCategory = "gas" | "food" | "hotel" | "travel" | "other";

export type ExpensePayload = {
  amount: string;
  category: ExpenseCategory;
  date: string;
  receipt: {
    mimeType: string | null;
    name: string;
    uri: string;
  };
};

export type ExpenseRecord = ExpensePayload & {
  createdAt: string;
  id: string;
};
