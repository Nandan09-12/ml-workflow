import { createContext, useContext } from "react";

import type { EndMileagePayload, MileageEntry, StartMileagePayload } from "./types";

export type MileageContextValue = {
  currentMileage: MileageEntry | null;
  isLoading: boolean;
  endShift: (payload: EndMileagePayload) => Promise<MileageEntry>;
  loadMileageForDate: (workDate: string) => Promise<MileageEntry | null>;
  startShift: (payload: StartMileagePayload) => Promise<MileageEntry>;
};

export const MileageContext = createContext<MileageContextValue | null>(null);

export function useMileage() {
  const value = useContext(MileageContext);

  if (!value) {
    throw new Error("useMileage must be used inside MileageProvider");
  }

  return value;
}
