import { createContext, useContext } from "react";

import type { MileagePayload, MileageRecord } from "./types";

export type MileageContextValue = {
  mileages: MileageRecord[];
  saveMileage: (payload: MileagePayload) => MileageRecord;
};

export const MileageContext = createContext<MileageContextValue | null>(null);

export function useMileage() {
  const value = useContext(MileageContext);

  if (!value) {
    throw new Error("useMileage must be used inside MileageProvider");
  }

  return value;
}
