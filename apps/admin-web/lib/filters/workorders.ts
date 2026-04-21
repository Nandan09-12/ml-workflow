import type { Region, WorkorderRecord, WorkorderStatus } from "@/lib/types/domain";

const allValue = "ALL" as const;
const regionValues = ["NE_UP", "CENTRAL", "SOUTH_FLORIDA"] as const satisfies readonly Region[];
const statusValues = ["ACTIVE", "COMPLETED"] as const satisfies readonly WorkorderStatus[];

export interface WorkordersFilterState {
  workorderCode: string;
  region: Region | typeof allValue;
  status: WorkorderStatus | typeof allValue;
  dateFrom: string;
  dateTo: string;
  page: number;
  pageSize: number;
}

export interface PaginatedWorkorders {
  items: WorkorderRecord[];
  page: number;
  pageSize: number;
  totalItems: number;
  totalPages: number;
}

export const defaultWorkordersFilters: WorkordersFilterState = {
  workorderCode: "",
  region: allValue,
  status: allValue,
  dateFrom: "",
  dateTo: "",
  page: 1,
  pageSize: 20,
};

function asSearchParams(input: URLSearchParams | string | undefined): URLSearchParams {
  if (input instanceof URLSearchParams) {
    return input;
  }

  return new URLSearchParams(input ?? "");
}

function parseEnumValue<T extends string>(value: string | null, allowedValues: readonly T[]): T | typeof allValue {
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

function workorderDate(value: string): string {
  return value.slice(0, 10);
}

export function parseWorkordersFilters(input: URLSearchParams | string | undefined): WorkordersFilterState {
  const searchParams = asSearchParams(input);

  return {
    workorderCode: searchParams.get("workorder_code") ?? defaultWorkordersFilters.workorderCode,
    region: parseEnumValue(searchParams.get("region"), regionValues),
    status: parseEnumValue(searchParams.get("status"), statusValues),
    dateFrom: searchParams.get("date_from") ?? defaultWorkordersFilters.dateFrom,
    dateTo: searchParams.get("date_to") ?? defaultWorkordersFilters.dateTo,
    page: parsePositiveInt(searchParams.get("page"), defaultWorkordersFilters.page),
    pageSize: parsePositiveInt(searchParams.get("page_size"), defaultWorkordersFilters.pageSize),
  };
}

export function buildWorkordersSearchParams(filters: WorkordersFilterState): string {
  const searchParams = new URLSearchParams();

  if (filters.workorderCode.trim()) {
    searchParams.set("workorder_code", filters.workorderCode.trim());
  }

  if (filters.region !== allValue) {
    searchParams.set("region", filters.region);
  }

  if (filters.status !== allValue) {
    searchParams.set("status", filters.status);
  }

  if (filters.dateFrom) {
    searchParams.set("date_from", filters.dateFrom);
  }

  if (filters.dateTo) {
    searchParams.set("date_to", filters.dateTo);
  }

  if (filters.page !== defaultWorkordersFilters.page) {
    searchParams.set("page", String(filters.page));
  }

  if (filters.pageSize !== defaultWorkordersFilters.pageSize) {
    searchParams.set("page_size", String(filters.pageSize));
  }

  return searchParams.toString();
}

export function hasActiveWorkordersFilters(filters: WorkordersFilterState): boolean {
  return buildWorkordersSearchParams(filters).length > 0;
}

export function filterWorkorders(records: WorkorderRecord[], filters: WorkordersFilterState): WorkorderRecord[] {
  const workorderQuery = filters.workorderCode.trim().toLowerCase();

  return records.filter((workorder) => {
    const createdDate = workorderDate(workorder.createdAt);

    if (workorderQuery && !workorder.workorderCode.toLowerCase().includes(workorderQuery)) {
      return false;
    }

    if (filters.region !== allValue && workorder.region !== filters.region) {
      return false;
    }

    if (filters.status !== allValue && workorder.status !== filters.status) {
      return false;
    }

    if (filters.dateFrom && createdDate < filters.dateFrom) {
      return false;
    }

    if (filters.dateTo && createdDate > filters.dateTo) {
      return false;
    }

    return true;
  });
}

export function paginateWorkorders(records: WorkorderRecord[], filters: WorkordersFilterState): PaginatedWorkorders {
  const totalItems = records.length;
  const totalPages = Math.max(1, Math.ceil(totalItems / filters.pageSize));
  const page = Math.min(filters.page, totalPages);
  const startIndex = (page - 1) * filters.pageSize;

  return {
    items: records.slice(startIndex, startIndex + filters.pageSize),
    page,
    pageSize: filters.pageSize,
    totalItems,
    totalPages,
  };
}