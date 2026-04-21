import { PropsWithChildren, useMemo, useState } from "react";

import { MileageContext } from "./MileageContext";
import type { MileagePayload, MileageRecord } from "./types";

export function MileageProvider({ children }: PropsWithChildren) {
  const [mileages, setMileages] = useState<MileageRecord[]>([]);

  const value = useMemo(
    () => ({
      mileages,
      saveMileage: (payload: MileagePayload) => {
        const record: MileageRecord = {
          ...payload,
          createdAt: new Date().toISOString(),
          id: String(Date.now()),
        };

        setMileages((current) => [record, ...current]);
        return record;
      },
    }),
    [mileages],
  );

  return <MileageContext.Provider value={value}>{children}</MileageContext.Provider>;
}
