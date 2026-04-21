export type ExpenseCategory = "gas" | "food" | "room" | "other";

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

export type ExpenseRecord = {
  amount: number;
  category: ExpenseCategory;
  createdAt: string;
  date: string;
  id: string;
  ownerUserId: string;
  receiptFileName: string;
};
