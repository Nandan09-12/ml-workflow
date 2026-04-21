import { ApiClientError } from "@ml-workflow/api-client";
import { PropsWithChildren, useCallback, useMemo, useState } from "react";

import { MileageContext } from "./MileageContext";
import type {
  EndMileagePayload,
  MileageEntry,
  MileageImageAsset,
  StartMileagePayload,
} from "./types";
import { apiClient } from "../lib/api";

type BackendMileageEntry = {
  end_mileage: number | null;
  end_odometer_file_name: string | null;
  ended_at: string | null;
  id: string;
  is_completed: boolean;
  owner_user_id: string;
  start_mileage: number;
  start_odometer_file_name: string;
  started_at: string;
  work_date: string;
};

function mapMileageEntry(entry: BackendMileageEntry): MileageEntry {
  return {
    endMileage: entry.end_mileage,
    endOdometerFileName: entry.end_odometer_file_name,
    endedAt: entry.ended_at,
    id: entry.id,
    isCompleted: entry.is_completed,
    ownerUserId: entry.owner_user_id,
    startMileage: entry.start_mileage,
    startOdometerFileName: entry.start_odometer_file_name,
    startedAt: entry.started_at,
    workDate: entry.work_date,
  };
}

function appendImage(formData: FormData, image: MileageImageAsset) {
  formData.append(
    "odometer_image",
    {
      uri: image.uri,
      name: image.name,
      type: image.mimeType ?? "image/jpeg",
    } as never,
  );
}

export function MileageProvider({ children }: PropsWithChildren) {
  const [currentMileage, setCurrentMileage] = useState<MileageEntry | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const loadMileageForDate = useCallback(async (workDate: string) => {
    setIsLoading(true);
    try {
      const response = await apiClient.get<BackendMileageEntry | null>("/api/v1/mileage", {
        query: { work_date: workDate },
      });
      const nextEntry = response ? mapMileageEntry(response) : null;
      setCurrentMileage(nextEntry);
      return nextEntry;
    } catch (error) {
      if (error instanceof ApiClientError && error.status === 404) {
        setCurrentMileage(null);
        return null;
      }
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const startShift = useCallback(async (payload: StartMileagePayload) => {
    const formData = new FormData();
    formData.append("work_date", payload.workDate);
    formData.append("start_mileage", payload.startMileage);
    formData.append("started_at", new Date().toISOString());
    appendImage(formData, payload.odometerImage);

    const response = await apiClient.post<BackendMileageEntry>("/api/v1/mileage/start", formData);
    const nextEntry = mapMileageEntry(response);
    setCurrentMileage(nextEntry);
    return nextEntry;
  }, []);

  const endShift = useCallback(async (payload: EndMileagePayload) => {
    const formData = new FormData();
    formData.append("work_date", payload.workDate);
    formData.append("end_mileage", payload.endMileage);
    formData.append("ended_at", new Date().toISOString());
    appendImage(formData, payload.odometerImage);

    const response = await apiClient.post<BackendMileageEntry>("/api/v1/mileage/end", formData);
    const nextEntry = mapMileageEntry(response);
    setCurrentMileage(nextEntry);
    return nextEntry;
  }, []);

  const value = useMemo(
    () => ({
      currentMileage,
      isLoading,
      loadMileageForDate,
      startShift,
      endShift,
    }),
    [currentMileage, endShift, isLoading, loadMileageForDate, startShift],
  );

  return <MileageContext.Provider value={value}>{children}</MileageContext.Provider>;
}
