import type { SubmissionRecord, SubmissionStatus, Region, Shift } from "@/lib/types/domain";

const allValue = "ALL" as const;
const regionValues = ["NE_UP", "CENTRAL", "SOUTH_FLORIDA"] as const satisfies readonly Region[];
const shiftValues = ["AM", "PM"] as const satisfies readonly Shift[];
const submissionStatusValues = ["IN_PROGRESS", "CHECKED_OUT", "COMPLETED"] as const satisfies readonly SubmissionStatus[];

export interface DailySubmissionsFilterState {
  workDate: string;
  region: Region | typeof allValue;
  shift: Shift | typeof allValue;
  submissionStatus: SubmissionStatus | typeof allValue;
  fileSubmissionPending: "true" | "false" | typeof allValue;
  workorderCode: string;
  tester: string;
  page: number;
  pageSize: number;
}

export interface PaginatedSubmissions {
  items: SubmissionRecord[];
  page: number;
  pageSize: number;
  totalItems: number;
  totalPages: number;
}

export const defaultDailySubmissionsFilters: DailySubmissionsFilterState = {
  workDate: "",
  region: allValue,
  shift: allValue,
  submissionStatus: allValue,
  fileSubmissionPending: allValue,
  workorderCode: "",
  tester: "",
  page: 1,
  pageSize: 20,
};

function asSearchParams(input: URLSearchParams | string | undefined): URLSearchParams {
  if (input instanceof URLSearchParams) {
    return input;
  }

  return new URLSearchParams(input ?? "");
}

function parseEnumValue<T extends string>(
  value: string | null,
  allowedValues: readonly T[],
): T | typeof allValue {
  if (!value) {
    return allValue;
  }

  return allowedValues.includes(value as T) ? (value as T) : allValue;
}

function parsePositiveInt(value: string | null, fallbackValue: number): number {
  const parsedValue = Number(value);

  if (!Number.isInteger(parsedValue) || parsedValue < 1) {
    return fallbackValue;
  }

  return parsedValue;
}

export function parseDailySubmissionsFilters(
  input: URLSearchParams | string | undefined,
): DailySubmissionsFilterState {
  const searchParams = asSearchParams(input);

  return {
    workDate: searchParams.get("work_date") ?? defaultDailySubmissionsFilters.workDate,
    region: parseEnumValue(searchParams.get("region"), regionValues),
    shift: parseEnumValue(searchParams.get("shift"), shiftValues),
    submissionStatus: parseEnumValue(searchParams.get("submission_status"), submissionStatusValues),
    fileSubmissionPending:
      searchParams.get("file_submission_pending") === "true"
        ? "true"
        : searchParams.get("file_submission_pending") === "false"
          ? "false"
          : allValue,
    workorderCode: searchParams.get("workorder_code") ?? defaultDailySubmissionsFilters.workorderCode,
    tester: searchParams.get("tester") ?? defaultDailySubmissionsFilters.tester,
    page: parsePositiveInt(searchParams.get("page"), defaultDailySubmissionsFilters.page),
    pageSize: parsePositiveInt(searchParams.get("page_size"), defaultDailySubmissionsFilters.pageSize),
  };
}

export function buildDailySubmissionsSearchParams(filters: DailySubmissionsFilterState): string {
  const searchParams = new URLSearchParams();

  if (filters.workDate) {
    searchParams.set("work_date", filters.workDate);
  }

  if (filters.region !== allValue) {
    searchParams.set("region", filters.region);
  }

  if (filters.shift !== allValue) {
    searchParams.set("shift", filters.shift);
  }

  if (filters.submissionStatus !== allValue) {
    searchParams.set("submission_status", filters.submissionStatus);
  }

  if (filters.fileSubmissionPending !== allValue) {
    searchParams.set("file_submission_pending", filters.fileSubmissionPending);
  }

  if (filters.workorderCode.trim()) {
    searchParams.set("workorder_code", filters.workorderCode.trim());
  }

  if (filters.tester.trim()) {
    searchParams.set("tester", filters.tester.trim());
  }

  if (filters.page !== defaultDailySubmissionsFilters.page) {
    searchParams.set("page", String(filters.page));
  }

  if (filters.pageSize !== defaultDailySubmissionsFilters.pageSize) {
    searchParams.set("page_size", String(filters.pageSize));
  }

  return searchParams.toString();
}

export function hasActiveDailySubmissionsFilters(filters: DailySubmissionsFilterState): boolean {
  return buildDailySubmissionsSearchParams(filters).length > 0;
}

export function filterDailySubmissions(
  records: SubmissionRecord[],
  filters: DailySubmissionsFilterState,
): SubmissionRecord[] {
  const testerQuery = filters.tester.trim().toLowerCase();
  const workorderQuery = filters.workorderCode.trim().toLowerCase();

  return records.filter((submission) => {
    if (filters.workDate && submission.workDate !== filters.workDate) {
      return false;
    }

    if (filters.region !== allValue && submission.region !== filters.region) {
      return false;
    }

    if (filters.shift !== allValue && submission.shift !== filters.shift) {
      return false;
    }

    if (filters.submissionStatus !== allValue && submission.status !== filters.submissionStatus) {
      return false;
    }

    if (filters.fileSubmissionPending !== allValue) {
      const pendingValue = filters.fileSubmissionPending === "true";
      if (submission.fileSubmissionPending !== pendingValue) {
        return false;
      }
    }

    if (workorderQuery && !submission.workorderCode.toLowerCase().includes(workorderQuery)) {
      return false;
    }

    if (testerQuery) {
      const matchesTester = submission.testerName.toLowerCase().includes(testerQuery)
        || submission.testerEmail.toLowerCase().includes(testerQuery)
        || submission.ticketNumber.toLowerCase().includes(testerQuery);

      if (!matchesTester) {
        return false;
      }
    }

    return true;
  });
}

export function paginateDailySubmissions(
  records: SubmissionRecord[],
  filters: DailySubmissionsFilterState,
): PaginatedSubmissions {
  const totalItems = records.length;
  const totalPages = Math.max(1, Math.ceil(totalItems / filters.pageSize));
  const page = Math.min(filters.page, totalPages);
  const startIndex = (page - 1) * filters.pageSize;
  const endIndex = startIndex + filters.pageSize;

  return {
    items: records.slice(startIndex, endIndex),
    page,
    pageSize: filters.pageSize,
    totalItems,
    totalPages,
  };
}