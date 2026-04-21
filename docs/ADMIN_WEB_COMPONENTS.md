# Admin Web Components

## Purpose
This file defines the reusable component inventory for the Admin Web frontend.

Build these components before duplicating page-specific markup. Keep components typed and small.

## Layout Components
AdminShell:

- Wraps the sidebar, topbar, and page content.
- Owns responsive layout.
- Receives current admin user.

Sidebar:

- Shows ML Technologies brand.
- Shows primary navigation.
- Highlights active route.

Topbar:

- Shows page title.
- Shows optional search field.
- Shows notification placeholder.
- Shows current admin identity.

PageHeader:

- Shows section label, title, subtitle, and action slot.

Panel:

- Bordered content container for dashboard sections, tables, forms, and detail sections.

## Navigation Components
NavItem:

- Icon plus label.
- Active and hover states.

Breadcrumbs:

- Useful for detail pages such as Workorder Detail and Daily Submission Detail.

## Data Display Components
StatusBadge:

- Supports daily submission status.
- Supports workorder status.
- Supports account status.
- Supports role badges.
- Supports file state.

Canonical values:

```text
IN_PROGRESS
CHECKED_OUT
COMPLETED
ACTIVE
APPROVED
PENDING_APPROVAL
REJECTED
SUSPENDED
ADMIN
DRIVE_TESTER
FILE_PENDING
ATTACHED
NOT_REQUIRED
```

MetricCard:

- Label.
- Value.
- Supporting text.
- Optional severity color.
- Optional click target.

ProgressBar:

- Percent value.
- Optional completed/skipped/remaining labels.

DefinitionList:

- Used on detail pages for key-value records.

Timeline:

- Used for audit history and attachment history.

EmptyState:

- Title, body, optional action.

Alert:

- Info, warning, success, and danger variants.

## Table Components
DataTable:

- Generic table wrapper.
- Horizontal overflow for dense admin tables.
- Accepts columns, rows, loading state, empty state, and row action.
- Should be controlled by page/query state rather than owning backend filters internally.
- Should not perform global client filtering on paginated backend data.

TableToolbar:

- Houses filters, export actions, and secondary actions.
- Should receive controlled filter values and change handlers.

Pagination:

- Uses backend `page` and `page_size`.
- Must not request `page_size > 100`.
- Should update URL search params on list pages.

Column patterns:

- Keep primary identifiers visible.
- Use badges for statuses.
- Use right alignment for numeric grid counts if the table design supports it.
- Keep row actions compact.

## Filter Components
DateFilter:

- Single date picker.

DateRangeFilter:

- From and to date pickers.

RegionFilter:

- Values:
  - `NE_UP`
  - `CENTRAL`
  - `SOUTH_FLORIDA`

Display labels:

- `NE-UP`
- `Central`
- `South/Florida`

ShiftFilter:

- Values:
  - `AM`
  - `PM`

SubmissionStatusFilter:

- Values:
  - `IN_PROGRESS`
  - `CHECKED_OUT`
  - `COMPLETED`

WorkorderStatusFilter:

- Values:
  - `ACTIVE`
  - `COMPLETED`

FilePendingFilter:

- Values:
  - all
  - file pending
  - not file pending

SearchInput:

- Used for workorder code, tester name/email, and ticket number.
- Should support debounced change handling when wired to API queries.

## Form Components
EditDrawer:

- Used for workorder and daily submission edits.
- Slides in from right on desktop.
- Can become full-screen on mobile.
- Closes with escape and close button.

ConfirmationDialog:

- Used for reopen, reject, suspend, and any high-impact mutation.

FormField:

- Label, control, help text, error text.

NumberField:

- Non-negative values for grid counts.
- Do not allow invalid string state to leak into API payloads.

SelectField:

- Use for region, shift, statuses, and roles.

DateField:

- Use for work date filters and editable date fields if backend supports them.

## Page-Specific Components
DashboardSummary:

- Metric cards for dashboard counts.

AdminQueue:

- File pending, pending users, and no submission yet drill-downs.

WorkorderProgressList:

- Compact progress cards for dashboard.

DailySubmissionsTable:

- Main operations table.

DailySubmissionDetailHeader:

- Tester, workorder, date, shift, ticket, status badges.

DailySubmissionEditDrawer:

- Edits supported daily submission fields.

WorkordersTable:

- Parent workorder aggregate table.

WorkorderDetailHeader:

- Workorder code, region, status, edit action.

WorkorderEditDrawer:

- Edits workorder code, region, and total grids.

UsersTable:

- All users list.

PendingUsersList:

- Pending approval cards or table.

NoSubmissionYetTable:

- Approved testers with no daily submission record for selected date.

ReportsExportPanel:

- Report filters and CSV export action.

## Styling Rules
Use the static mockup as the visual baseline:

```text
docs/ui-mockups/adminui
```

General rules:

- Border radius around 8px.
- Light neutral background.
- White panels.
- Blue brand accents.
- Dense spacing for tables.
- Clear visual hierarchy.
- No nested decorative cards.
- No marketing hero sections.
- No one-hue-only design. Use status colors intentionally.

Status colors:

- Green for success/completed/approved/attached.
- Amber for checked-out/file-pending/pending approval.
- Blue for active/in-progress/role badges.
- Red for rejected/suspended/destructive warnings.
- Gray for inactive/unavailable/not required.

## Accessibility Rules
- Icon-only buttons must have `aria-label`.
- Form inputs must have labels.
- Dialogs and drawers must trap focus when using Radix or equivalent primitives.
- Badge color cannot be the only source of meaning.
- Tables should keep readable headers.
- Avoid text overflow in buttons and badges.

## Data And Formatting Helpers
Create shared helpers for:

- Status label formatting.
- Region label formatting.
- Date formatting.
- Date-time formatting.
- Percent formatting.
- Remaining grids calculation when needed for display.
- CSV filename generation.
- Query param serialization for filters.
- Query param parsing for list page initial state.

Backend remains source of truth for persisted values and computed read-model fields.

## Mock Data Rule
Mock data is allowed during early UI development, but it must be isolated:

- Put mock data in `lib/mock`.
- Do not define large mock arrays inside route files.
- Do not import mock data from reusable primitive components.
- Keep mock object shapes close to expected API response shapes.
- Remove or clearly bypass mock usage when the corresponding API integration is complete.

## Do Not Build
Do not add reusable components for out-of-scope V1 concepts:

- Teams/kits management.
- Assignment planning.
- Viewer role.
- Advanced analytics dashboards.
- Client-facing reporting.
