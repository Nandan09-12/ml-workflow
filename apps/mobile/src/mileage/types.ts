export type MileagePayload = {
  date: string;
  endMileage: string;
  endTime: string;
  odometerImage: {
    mimeType: string | null;
    name: string;
    uri: string;
  };
  startMileage: string;
  startTime: string;
};

export type MileageRecord = MileagePayload & {
  createdAt: string;
  id: string;
};
