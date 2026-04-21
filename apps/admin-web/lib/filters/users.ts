import type { AccountStatus, UserRecord, UserRole } from "@/lib/types/domain";

const allValue = "ALL" as const;
const roleValues = ["ADMIN", "DRIVE_TESTER"] as const satisfies readonly UserRole[];
const accountStatusValues = ["PENDING_APPROVAL", "APPROVED", "REJECTED", "SUSPENDED"] as const satisfies readonly AccountStatus[];

export interface UsersFilterState {
  role: UserRole | typeof allValue;
  accountStatus: AccountStatus | typeof allValue;
  query: string;
  page: number;
  pageSize: number;
}

export interface PaginatedUsers {
  items: UserRecord[];
  page: number;
  pageSize: number;
  totalItems: number;
  totalPages: number;
}

export const defaultUsersFilters: UsersFilterState = {
  role: allValue,
  accountStatus: allValue,
  query: "",
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

export function parseUsersFilters(input: URLSearchParams | string | undefined): UsersFilterState {
  const searchParams = asSearchParams(input);

  return {
    role: parseEnumValue(searchParams.get("role"), roleValues),
    accountStatus: parseEnumValue(searchParams.get("account_status"), accountStatusValues),
    query: searchParams.get("query") ?? defaultUsersFilters.query,
    page: parsePositiveInt(searchParams.get("page"), defaultUsersFilters.page),
    pageSize: parsePositiveInt(searchParams.get("page_size"), defaultUsersFilters.pageSize),
  };
}

export function buildUsersSearchParams(filters: UsersFilterState): string {
  const searchParams = new URLSearchParams();

  if (filters.role !== allValue) {
    searchParams.set("role", filters.role);
  }

  if (filters.accountStatus !== allValue) {
    searchParams.set("account_status", filters.accountStatus);
  }

  if (filters.query.trim()) {
    searchParams.set("query", filters.query.trim());
  }

  if (filters.page !== defaultUsersFilters.page) {
    searchParams.set("page", String(filters.page));
  }

  if (filters.pageSize !== defaultUsersFilters.pageSize) {
    searchParams.set("page_size", String(filters.pageSize));
  }

  return searchParams.toString();
}

export function hasActiveUsersFilters(filters: UsersFilterState): boolean {
  return buildUsersSearchParams(filters).length > 0;
}

export function filterUsers(records: UserRecord[], filters: UsersFilterState): UserRecord[] {
  const query = filters.query.trim().toLowerCase();

  return records.filter((user) => {
    if (filters.role !== allValue && user.requestedRole !== filters.role && user.approvedRole !== filters.role) {
      return false;
    }

    if (filters.accountStatus !== allValue && user.accountStatus !== filters.accountStatus) {
      return false;
    }

    if (query) {
      const matchesQuery = user.fullName.toLowerCase().includes(query)
        || user.email.toLowerCase().includes(query);

      if (!matchesQuery) {
        return false;
      }
    }

    return true;
  });
}

export function paginateUsers(records: UserRecord[], filters: UsersFilterState): PaginatedUsers {
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