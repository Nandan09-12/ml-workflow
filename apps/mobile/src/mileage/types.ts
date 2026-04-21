export type MileageImageAsset = {
  mimeType: string | null;
  name: string;
  uri: string;
};

export type MileageEntry = {
  endMileage: number | null;
  endOdometerFileName: string | null;
  endedAt: string | null;
  id: string;
  isCompleted: boolean;
  ownerUserId: string;
  startMileage: number;
  startOdometerFileName: string;
  startedAt: string;
  workDate: string;
};

export type StartMileagePayload = {
  odometerImage: MileageImageAsset;
  startMileage: string;
  workDate: string;
};

export type EndMileagePayload = {
  endMileage: string;
  odometerImage: MileageImageAsset;
  workDate: string;
};
