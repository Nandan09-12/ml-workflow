/**
 * API Contract Tests
 *
 * These tests call the REAL running backend at INTEGRATION_API_URL and assert that
 * every field the frontend hooks read actually exists in the API response.
 *
 * If the backend renames or removes a field these tests fail — protecting against
 * silent undefined values appearing in the UI after a backend change.
 *
 * Required env vars (tests are skipped when absent):
 *   INTEGRATION_API_URL   — e.g. http://localhost:8000/api/v1
 *   INTEGRATION_API_TOKEN — a valid Supabase JWT for an approved ADMIN user
 *
 * Run with:
 *   pnpm --filter admin-web test:integration
 */

import { describe, it, expect, beforeAll } from "vitest";

const BASE_URL = process.env.INTEGRATION_API_URL ?? "http://localhost:8000/api/v1";
const TOKEN = process.env.INTEGRATION_API_TOKEN ?? "";
const hasCredentials = TOKEN.length > 0;

// ---------------------------------------------------------------------------
// Helper — raw fetch with bearer token, unwraps the {success, data} envelope
// ---------------------------------------------------------------------------
async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: {
      Authorization: `Bearer ${TOKEN}`,
      "Content-Type": "application/json",
    },
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${res.statusText} — ${path}\n${text}`);
  }

  const envelope = await res.json();

  if (envelope.success !== true) {
    throw new Error(
      `API returned success=false for ${path}: ${JSON.stringify(envelope.error)}`,
    );
  }

  return envelope.data as T;
}

// ---------------------------------------------------------------------------
// Helpers to assert required keys exist and are not undefined
// ---------------------------------------------------------------------------
function assertKeys<T extends object>(label: string, obj: T, keys: (keyof T | string)[]) {
  for (const key of keys) {
    expect(
      Object.prototype.hasOwnProperty.call(obj, key),
      `${label} is missing field "${String(key)}" — this will cause undefined in the UI`,
    ).toBe(true);
  }
}

function assertItemShape(label: string, item: Record<string, unknown>) {
  expect(item).toBeDefined();
  expect(typeof item).toBe("object");
  expect(item).not.toBeNull();
  expect(label).toBeTruthy(); // sanity
}

// ---------------------------------------------------------------------------
// Pagination helpers
// ---------------------------------------------------------------------------
function assertNestedPagination(data: Record<string, unknown>) {
  expect(data, "response.pagination should exist").toHaveProperty("pagination");
  const p = data.pagination as Record<string, unknown>;
  assertKeys("pagination", p, ["page", "page_size", "total", "total_pages"]);
  expect(typeof p.page).toBe("number");
  expect(typeof p.page_size).toBe("number");
  expect(typeof p.total).toBe("number");
  expect(typeof p.total_pages).toBe("number");
}

function assertFlatPagination(data: Record<string, unknown>) {
  assertKeys("top-level pagination", data, ["page", "page_size", "total", "total_pages"]);
  expect(typeof data.page).toBe("number");
  expect(typeof data.page_size).toBe("number");
  expect(typeof data.total).toBe("number");
  expect(typeof data.total_pages).toBe("number");
}

// ---------------------------------------------------------------------------
// GET /admin/submissions
// Fields read by useAdminSubmissions → mapItem()
// ---------------------------------------------------------------------------
describe.skipIf(!hasCredentials)("GET /admin/submissions — contract", () => {
  let data: Record<string, unknown>;

  beforeAll(async () => {
    data = await apiFetch("/admin/submissions?page_size=1");
  });

  it("returns {items, pagination} envelope shape", () => {
    expect(data).toHaveProperty("items");
    expect(Array.isArray(data.items)).toBe(true);
    assertNestedPagination(data);
  });

  it("each item has all fields useAdminSubmissions reads", () => {
    const items = data.items as Record<string, unknown>[];
    if (items.length === 0) {
      console.warn("⚠️  /admin/submissions returned 0 items — field-level assertions skipped");
      return;
    }

    const item = items[0];
    assertItemShape("submission item", item);

    // Fields the hook maps directly
    assertKeys("submission item", item, [
      "id",
      "work_date",
      "submitter_name_snapshot",
      "submitter_email_snapshot",
      "shift",
      "ticket_number",
      "completed_grids",
      "skipped_grids",
      "force_tested_grids",
      "status",
      "file_submission_pending",
      "started_at",
      "ended_at",
      "updated_at",
    ]);

    // file_submission_pending must be a boolean (not null/string)
    expect(
      typeof item.file_submission_pending,
      "file_submission_pending must be boolean — hook uses it as bool to set fileState",
    ).toBe("boolean");

    // workorder_summary may be null for orphaned submissions, but if present must have these keys
    if (item.workorder_summary !== null && item.workorder_summary !== undefined) {
      const ws = item.workorder_summary as Record<string, unknown>;
      assertKeys("workorder_summary", ws, [
        "workorder_code",
        "region",
        "status",
        "total_grids",
        "completed_grids",
        "skipped_grids",
      ]);
    }
  });

  it("pagination values are numbers and logically consistent", () => {
    const p = data.pagination as Record<string, unknown>;
    expect(p.page).toBeGreaterThanOrEqual(1);
    expect(p.page_size).toBeGreaterThanOrEqual(1);
    expect(p.total).toBeGreaterThanOrEqual(0);
    expect(p.total_pages).toBeGreaterThanOrEqual(0);
  });

  it("status filter passes through to API (returns only matching status)", async () => {
    const filtered = await apiFetch<Record<string, unknown>>(
      "/admin/submissions?status=COMPLETED&page_size=5",
    );
    const items = filtered.items as Record<string, unknown>[];
    for (const item of items) {
      expect(item.status, "status filter returned wrong status value").toBe("COMPLETED");
    }
  });

  it("shift filter passes through correctly", async () => {
    const filtered = await apiFetch<Record<string, unknown>>(
      "/admin/submissions?shift=AM&page_size=5",
    );
    const items = filtered.items as Record<string, unknown>[];
    for (const item of items) {
      expect(item.shift).toBe("AM");
    }
  });
});

// ---------------------------------------------------------------------------
// GET /admin/workorders
// Fields read by useAdminWorkorders → mapItem()
// IMPORTANT: this endpoint uses FLAT pagination (not nested)
// ---------------------------------------------------------------------------
describe.skipIf(!hasCredentials)("GET /admin/workorders — contract", () => {
  let data: Record<string, unknown>;

  beforeAll(async () => {
    data = await apiFetch("/admin/workorders?page_size=1");
  });

  it("returns {items, total, page, page_size, total_pages} — flat pagination", () => {
    expect(data).toHaveProperty("items");
    expect(Array.isArray(data.items)).toBe(true);
    assertFlatPagination(data);
  });

  it("each item has all fields useAdminWorkorders reads", () => {
    const items = data.items as Record<string, unknown>[];
    if (items.length === 0) {
      console.warn("⚠️  /admin/workorders returned 0 items — field-level assertions skipped");
      return;
    }

    const item = items[0];
    assertItemShape("workorder item", item);

    assertKeys("workorder item", item, [
      "id",
      "workorder_code",
      "region",
      "status",
      "total_grids",
      "completed_grids",
      "skipped_grids",
      "remaining_grids",
      "progress_percent",
      "created_at",
      "updated_at",
    ]);

    // Numeric fields used in progress bar must be numbers
    for (const field of ["total_grids", "completed_grids", "skipped_grids", "remaining_grids", "progress_percent"]) {
      expect(
        typeof item[field],
        `workorder.${field} must be a number`,
      ).toBe("number");
    }

    // remaining_grids must equal total - completed - skipped
    const total = item.total_grids as number;
    const completed = item.completed_grids as number;
    const skipped = item.skipped_grids as number;
    const remaining = item.remaining_grids as number;
    expect(
      remaining,
      "remaining_grids must equal total_grids - completed_grids - skipped_grids",
    ).toBe(total - completed - skipped);
  });

  it("flat pagination values are logically consistent", () => {
    expect(data.page).toBeGreaterThanOrEqual(1);
    expect(data.page_size).toBeGreaterThanOrEqual(1);
    expect(data.total).toBeGreaterThanOrEqual(0);
    expect(data.total_pages).toBeGreaterThanOrEqual(0);
  });

  it("region filter passes through correctly", async () => {
    const filtered = await apiFetch<Record<string, unknown>>(
      "/admin/workorders?region=NE_UP&page_size=5",
    );
    const items = filtered.items as Record<string, unknown>[];
    for (const item of items) {
      expect(item.region).toBe("NE_UP");
    }
  });

  it("status filter passes through correctly", async () => {
    const filtered = await apiFetch<Record<string, unknown>>(
      "/admin/workorders?status=ACTIVE&page_size=5",
    );
    const items = filtered.items as Record<string, unknown>[];
    for (const item of items) {
      expect(item.status).toBe("ACTIVE");
    }
  });
});

// ---------------------------------------------------------------------------
// GET /admin/users
// Fields read by useAdminUsers → mapItem()
// ---------------------------------------------------------------------------
describe.skipIf(!hasCredentials)("GET /admin/users — contract", () => {
  let data: Record<string, unknown>;

  beforeAll(async () => {
    data = await apiFetch("/admin/users?page_size=1");
  });

  it("returns {items, pagination} envelope shape", () => {
    expect(data).toHaveProperty("items");
    expect(Array.isArray(data.items)).toBe(true);
    assertNestedPagination(data);
  });

  it("each item has all fields useAdminUsers reads", () => {
    const items = data.items as Record<string, unknown>[];
    if (items.length === 0) {
      console.warn("⚠️  /admin/users returned 0 items — field-level assertions skipped");
      return;
    }

    const item = items[0];
    assertItemShape("user item", item);

    assertKeys("user item", item, [
      "id",
      "full_name",
      "email",
      "requested_role",
      "approved_role",
      "account_status",
      "created_at",
      "approved_at",
    ]);

    // full_name must be a string (hook maps to fullName)
    expect(typeof item.full_name).toBe("string");
    // email must be a string
    expect(typeof item.email).toBe("string");
  });

  it("requested_role filter passes through correctly", async () => {
    const filtered = await apiFetch<Record<string, unknown>>(
      "/admin/users?requested_role=DRIVE_TESTER&page_size=5",
    );
    const items = filtered.items as Record<string, unknown>[];
    for (const item of items) {
      expect(item.requested_role).toBe("DRIVE_TESTER");
    }
  });

  it("account_status filter passes through correctly", async () => {
    const filtered = await apiFetch<Record<string, unknown>>(
      "/admin/users?account_status=APPROVED&page_size=5",
    );
    const items = filtered.items as Record<string, unknown>[];
    for (const item of items) {
      expect(item.account_status).toBe("APPROVED");
    }
  });
});

// ---------------------------------------------------------------------------
// GET /admin/users/pending
// Fields read by usePendingUsers → mapItem()
// Shape: { items, count } — no pagination
// ---------------------------------------------------------------------------
describe.skipIf(!hasCredentials)("GET /admin/users/pending — contract", () => {
  let data: Record<string, unknown>;

  beforeAll(async () => {
    data = await apiFetch("/admin/users/pending");
  });

  it("returns {items, count} — no pagination object", () => {
    expect(data).toHaveProperty("items");
    expect(data).toHaveProperty("count");
    expect(Array.isArray(data.items)).toBe(true);
    expect(typeof data.count).toBe("number");
    // Must NOT have a nested pagination object
    expect(data).not.toHaveProperty("pagination");
  });

  it("count matches items.length", () => {
    const items = data.items as unknown[];
    expect(data.count).toBe(items.length);
  });

  it("each pending user item has required fields", () => {
    const items = data.items as Record<string, unknown>[];
    if (items.length === 0) return; // no pending users right now — that's fine

    for (const item of items) {
      assertKeys("pending user item", item, [
        "id",
        "full_name",
        "email",
        "requested_role",
        "approved_role",
        "account_status",
        "created_at",
        "approved_at",
      ]);
      // All pending users must have account_status = PENDING_APPROVAL
      expect(
        item.account_status,
        "pending user must have account_status=PENDING_APPROVAL",
      ).toBe("PENDING_APPROVAL");
    }
  });
});

// ---------------------------------------------------------------------------
// GET /admin/dashboard/no-submission-yet
// Fields read by useNoSubmissionYet → mapItem()
// Shape: { work_date, note, items, count, pagination }
// ---------------------------------------------------------------------------
describe.skipIf(!hasCredentials)("GET /admin/dashboard/no-submission-yet — contract", () => {
  const today = new Date().toISOString().split("T")[0];
  let data: Record<string, unknown>;

  beforeAll(async () => {
    data = await apiFetch(`/admin/dashboard/no-submission-yet?work_date=${today}`);
  });

  it("returns required top-level fields", () => {
    assertKeys("no-submission-yet response", data, [
      "work_date",
      "note",
      "items",
      "count",
      "pagination",
    ]);
    expect(Array.isArray(data.items)).toBe(true);
    expect(typeof data.count).toBe("number");
    expect(typeof data.note).toBe("string");
    expect(data.work_date).toBe(today);
  });

  it("has nested pagination", () => {
    assertNestedPagination(data);
  });

  it("count matches items.length for page 1", () => {
    // count is the total, items is the page — count >= items.length
    const items = data.items as unknown[];
    expect(data.count as number).toBeGreaterThanOrEqual(items.length);
  });

  it("each item has fields useNoSubmissionYet reads (id, full_name, email)", () => {
    const items = data.items as Record<string, unknown>[];
    if (items.length === 0) return;

    for (const item of items) {
      assertKeys("no-submission-yet item", item, ["id", "full_name", "email"]);
      expect(typeof item.full_name).toBe("string");
      expect(typeof item.email).toBe("string");
    }
  });
});

// ---------------------------------------------------------------------------
// GET /admin/dashboard/summary
// Fields read by useDashboardSummary
// ---------------------------------------------------------------------------
describe.skipIf(!hasCredentials)("GET /admin/dashboard/summary — contract", () => {
  const today = new Date().toISOString().split("T")[0];
  let data: Record<string, unknown>;

  beforeAll(async () => {
    data = await apiFetch(`/admin/dashboard/summary?work_date=${today}`);
  });

  it("returns all fields useDashboardSummary reads", () => {
    assertKeys("dashboard summary", data, [
      "active_workorders",
      "completed_workorders",
      "ongoing_submissions",
      "completed_submissions",
      "no_submission_yet",
    ]);
  });

  it("all count fields are non-negative numbers", () => {
    for (const field of [
      "active_workorders",
      "completed_workorders",
      "ongoing_submissions",
      "completed_submissions",
      "no_submission_yet",
    ]) {
      expect(
        typeof data[field],
        `dashboard.${field} must be a number`,
      ).toBe("number");
      expect(data[field] as number).toBeGreaterThanOrEqual(0);
    }
  });
});

// ---------------------------------------------------------------------------
// Success envelope shape — all endpoints must wrap in {success, data}
// ---------------------------------------------------------------------------
describe.skipIf(!hasCredentials)("API envelope contract — all admin endpoints", () => {
  const endpoints = [
    "/admin/submissions?page_size=1",
    "/admin/workorders?page_size=1",
    "/admin/users?page_size=1",
    "/admin/users/pending",
    `/admin/dashboard/no-submission-yet?work_date=${new Date().toISOString().split("T")[0]}`,
    `/admin/dashboard/summary?work_date=${new Date().toISOString().split("T")[0]}`,
  ];

  for (const endpoint of endpoints) {
    it(`${endpoint} returns {success: true, data: ...}`, async () => {
      const res = await fetch(`${BASE_URL}${endpoint}`, {
        headers: { Authorization: `Bearer ${TOKEN}` },
      });

      expect(res.ok, `${endpoint} returned HTTP ${res.status}`).toBe(true);

      const envelope = await res.json();
      expect(envelope.success, `${endpoint} envelope.success must be true`).toBe(true);
      expect(envelope).toHaveProperty("data");
      expect(envelope.data).not.toBeNull();
    });
  }
});

// ---------------------------------------------------------------------------
// Auth contract — 401 without token, not 500
// ---------------------------------------------------------------------------
describe("Auth contract — unauthenticated requests return 401", () => {
  const endpoints = [
    "/admin/submissions",
    "/admin/workorders",
    "/admin/users",
  ];

  for (const endpoint of endpoints) {
    it(`${endpoint} returns 401 without auth header`, async () => {
      const res = await fetch(`${BASE_URL}${endpoint}`);
      expect(
        res.status,
        `${endpoint} should return 401 without auth, got ${res.status}`,
      ).toBe(401);
    });
  }
});

// ---------------------------------------------------------------------------
// Wave 5 — GET /admin/submissions/{id}
// Fields read by useAdminSubmission → mapItem()
// ---------------------------------------------------------------------------
describe.skipIf(!hasCredentials)("GET /admin/submissions/{id} — contract", () => {
  let submissionId: string;
  let item: Record<string, unknown>;

  beforeAll(async () => {
    // Fetch the first available submission to get a real ID
    const list = await apiFetch<Record<string, unknown>>("/admin/submissions?page_size=1");
    const items = list.items as Record<string, unknown>[];
    if (items.length === 0) return;
    submissionId = items[0].id as string;
    item = await apiFetch(`/admin/submissions/${submissionId}`);
  });

  it("returns the submission as a flat object (not paginated)", () => {
    if (!submissionId) return;
    expect(typeof item).toBe("object");
    expect(item).not.toHaveProperty("items");
    expect(item).not.toHaveProperty("pagination");
  });

  it("has all fields useAdminSubmission reads including version_number", () => {
    if (!submissionId) return;
    assertKeys("submission detail", item, [
      "id",
      "work_date",
      "submitter_name_snapshot",
      "submitter_email_snapshot",
      "shift",
      "ticket_number",
      "completed_grids",
      "skipped_grids",
      "force_tested_grids",
      "status",
      "file_submission_pending",
      "started_at",
      "ended_at",
      "updated_at",
      "version_number",
    ]);
  });

  it("version_number is a positive integer (required for optimistic concurrency)", () => {
    if (!submissionId) return;
    expect(typeof item.version_number).toBe("number");
    expect(item.version_number as number).toBeGreaterThanOrEqual(1);
  });

  it("workorder_summary field exists (may be null, but must be present)", () => {
    if (!submissionId) return;
    expect(Object.prototype.hasOwnProperty.call(item, "workorder_summary")).toBe(true);
    // If present and non-null, assert sub-fields
    if (item.workorder_summary !== null && item.workorder_summary !== undefined) {
      const ws = item.workorder_summary as Record<string, unknown>;
      assertKeys("workorder_summary", ws, [
        "workorder_code",
        "region",
        "status",
        "total_grids",
        "completed_grids",
        "skipped_grids",
        "remaining_grids",
        "progress_percent",
      ]);
    }
  });

  it("404 for a non-existent submission ID", async () => {
    const res = await fetch(`${BASE_URL}/admin/submissions/non-existent-id-000`, {
      headers: { Authorization: `Bearer ${TOKEN}` },
    });
    expect(res.status).toBe(404);
  });
});

// ---------------------------------------------------------------------------
// Wave 5 — GET /admin/submissions/{id}/audit
// Fields read by useSubmissionAudit
// ---------------------------------------------------------------------------
describe.skipIf(!hasCredentials)("GET /admin/submissions/{id}/audit — contract", () => {
  let submissionId: string;
  let data: Record<string, unknown>;

  beforeAll(async () => {
    const list = await apiFetch<Record<string, unknown>>("/admin/submissions?page_size=1");
    const items = list.items as Record<string, unknown>[];
    if (items.length === 0) return;
    submissionId = items[0].id as string;
    data = await apiFetch(`/admin/submissions/${submissionId}/audit`);
  });

  it("returns {items, count} shape", () => {
    if (!submissionId) return;
    expect(data).toHaveProperty("items");
    expect(data).toHaveProperty("count");
    expect(Array.isArray(data.items)).toBe(true);
    expect(typeof data.count).toBe("number");
  });

  it("count matches items.length", () => {
    if (!submissionId) return;
    const items = data.items as unknown[];
    expect(data.count).toBe(items.length);
  });

  it("each audit item has required fields", () => {
    if (!submissionId) return;
    const items = data.items as Record<string, unknown>[];
    if (items.length === 0) return;

    for (const item of items) {
      assertKeys("audit item", item, [
        "id",
        "submission_id",
        "changed_by_user_id",
        "changed_at",
        "change_type",
        "before_snapshot",
        "after_snapshot",
      ]);
      expect(typeof item.change_type).toBe("string");
      expect(typeof item.changed_at).toBe("string");
    }
  });
});

// ---------------------------------------------------------------------------
// Wave 5 — GET /admin/submissions/{id}/attachments/history
// Fields read by useSubmissionAttachmentHistory
// ---------------------------------------------------------------------------
describe.skipIf(!hasCredentials)("GET /admin/submissions/{id}/attachments/history — contract", () => {
  let submissionId: string;
  let data: Record<string, unknown>;

  beforeAll(async () => {
    const list = await apiFetch<Record<string, unknown>>("/admin/submissions?page_size=1");
    const items = list.items as Record<string, unknown>[];
    if (items.length === 0) return;
    submissionId = items[0].id as string;
    data = await apiFetch(`/admin/submissions/${submissionId}/attachments/history`);
  });

  it("returns {items, count} shape", () => {
    if (!submissionId) return;
    expect(data).toHaveProperty("items");
    expect(data).toHaveProperty("count");
    expect(Array.isArray(data.items)).toBe(true);
    expect(typeof data.count).toBe("number");
  });

  it("each attachment item has required fields", () => {
    if (!submissionId) return;
    const items = data.items as Record<string, unknown>[];
    if (items.length === 0) return;

    for (const item of items) {
      assertKeys("attachment history item", item, [
        "id",
        "submission_id",
        "file_name",
        "bucket_name",
        "object_path",
        "mime_type",
        "file_extension",
        "file_size_bytes",
        "uploaded_by_user_id",
        "uploaded_at",
        "is_active",
      ]);
      expect(typeof item.file_name).toBe("string");
      expect(typeof item.is_active).toBe("boolean");
      expect(typeof item.file_size_bytes).toBe("number");
    }
  });
});

// ---------------------------------------------------------------------------
// Wave 5 — GET /admin/workorders/{id}
// Fields read by useAdminWorkorder
// ---------------------------------------------------------------------------
describe.skipIf(!hasCredentials)("GET /admin/workorders/{id} — contract", () => {
  let workorderId: string;
  let item: Record<string, unknown>;

  beforeAll(async () => {
    const list = await apiFetch<Record<string, unknown>>("/admin/workorders?page_size=1");
    const items = list.items as Record<string, unknown>[];
    if (items.length === 0) return;
    workorderId = items[0].id as string;
    item = await apiFetch(`/admin/workorders/${workorderId}`);
  });

  it("returns a flat workorder object with submissions array", () => {
    if (!workorderId) return;
    expect(typeof item).toBe("object");
    expect(item).toHaveProperty("submissions");
    expect(Array.isArray(item.submissions)).toBe(true);
  });

  it("has all workorder-level fields useAdminWorkorder maps", () => {
    if (!workorderId) return;
    assertKeys("workorder detail", item, [
      "id",
      "workorder_code",
      "region",
      "status",
      "total_grids",
      "completed_grids",
      "skipped_grids",
      "remaining_grids",
      "progress_percent",
      "created_at",
      "updated_at",
    ]);
    expect(typeof item.remaining_grids).toBe("number");
    expect(typeof item.progress_percent).toBe("number");
  });

  it("each submission in submissions array has version_number", () => {
    if (!workorderId) return;
    const subs = item.submissions as Record<string, unknown>[];
    if (subs.length === 0) return;

    for (const sub of subs) {
      assertKeys("child submission", sub, [
        "id",
        "work_date",
        "submitter_name_snapshot",
        "shift",
        "ticket_number",
        "completed_grids",
        "skipped_grids",
        "force_tested_grids",
        "status",
        "version_number",
        "started_at",
        "ended_at",
        "file_submission_pending",
      ]);
      expect(
        typeof sub.version_number,
        "child submission.version_number must be a number",
      ).toBe("number");
    }
  });

  it("404 for a non-existent workorder ID", async () => {
    const res = await fetch(`${BASE_URL}/admin/workorders/non-existent-id-000`, {
      headers: { Authorization: `Bearer ${TOKEN}` },
    });
    expect(res.status).toBe(404);
  });
});

// ---------------------------------------------------------------------------
// Wave 5 — GET /admin/reports/submissions/export
// Returns CSV blob (skipEnvelope: true)
// ---------------------------------------------------------------------------
describe.skipIf(!hasCredentials)("GET /admin/reports/submissions/export — contract", () => {
  it("returns text/csv content-type (not JSON envelope)", async () => {
    const res = await fetch(`${BASE_URL}/admin/reports/submissions/export`, {
      headers: { Authorization: `Bearer ${TOKEN}` },
    });
    expect(res.ok, `export endpoint returned HTTP ${res.status}`).toBe(true);
    const contentType = res.headers.get("content-type") ?? "";
    expect(
      contentType.includes("csv") || contentType.includes("text/"),
      `Expected CSV content-type, got: ${contentType}`,
    ).toBe(true);
  });

  it("accepts filter params without error", async () => {
    const res = await fetch(
      `${BASE_URL}/admin/reports/submissions/export?status=COMPLETED`,
      { headers: { Authorization: `Bearer ${TOKEN}` } },
    );
    expect(res.ok).toBe(true);
  });

  it("returns 401 without auth header", async () => {
    const res = await fetch(`${BASE_URL}/admin/reports/submissions/export`);
    expect(res.status).toBe(401);
  });
});

// ---------------------------------------------------------------------------
// Wave 5 — Auth on mutation endpoints (401 without token)
// ---------------------------------------------------------------------------
describe("Auth contract — Wave 5 mutation endpoints return 401 without token", () => {
  const mutationEndpoints = [
    { method: "POST", path: "/admin/users/some-user-id/approve" },
    { method: "POST", path: "/admin/users/some-user-id/reject" },
    { method: "POST", path: "/admin/users/some-user-id/suspend" },
    { method: "POST", path: "/admin/submissions/some-sub-id/reopen" },
    { method: "PATCH", path: "/admin/submissions/some-sub-id" },
    { method: "PATCH", path: "/admin/workorders/some-wo-id" },
  ];

  for (const { method, path } of mutationEndpoints) {
    it(`${method} ${path} returns 401 without auth header`, async () => {
      const res = await fetch(`${BASE_URL}${path}`, {
        method,
        headers: { "Content-Type": "application/json" },
        body: "{}",
      });
      expect(
        res.status,
        `${method} ${path} should return 401 without auth, got ${res.status}`,
      ).toBe(401);
    });
  }
});
