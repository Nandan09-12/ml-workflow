# Admin Web UI Spec

## Purpose
This file defines the MVP Admin Web pages and their UI behavior.

Reference mockup:

```text
docs/ui-mockups/adminui/index.html
```

## Design Direction
Use an operations-console layout:

- Left sidebar navigation.
- Sticky topbar.
- Dense tables.
- Strong filter rows.
- Clear status badges.
- Detail pages for high-impact edits.
- Drawers or modals for forms.
- Confirmation dialogs for reopen, reject, suspend, and similar actions.

Avoid marketing-page layouts. Admins are replacing spreadsheet-driven review workflows and need fast scanning.

## Global Navigation
Sidebar items:

- Dashboard
- Daily Submissions
- Workorders
- Users
- Pending Users
- No Submission Yet
- Reports

Detail pages do not need permanent sidebar entries in the real app. They can be reached from list rows.

## Global Topbar
Include:

- Page title.
- Optional global search placeholder for workorder code, tester, email, or ticket.
- Notification icon placeholder.
- Current admin identity chip.

Do not build notification behavior in V1 unless backend support exists.

## URL State
List pages should store meaningful state in URL search params:

- Filters.
- Page.
- Page size.
- Search terms.

This applies to:

- Daily Submissions.
- Workorders.
- Users.
- No Submission Yet.
- Reports.

Dashboard drill-down links should open list pages with the relevant search params already set.

Do not store table filter state only in local component state unless it is strictly temporary UI state.

## Table Behavior
Tables should be server-data oriented:

- Backend pagination is the source of truth.
- Do not client-filter across only the current page and present it as global results.
- Do not add sorting controls unless the backend supports sorting or the control is clearly local/mock-only.
- Keep numeric grid fields scannable.
- Keep workorder code, tester, status, and file state visible without horizontal scrolling on common desktop widths where practical.
- Use horizontal scrolling for overflow on smaller screens instead of crushing text.

Table loading states should preserve approximate layout height to avoid jarring shifts.

## Dashboard
Purpose:

- Give admins a fast operational summary for today or a selected date range.

Filters:

- Date or date range.
- Region.

Summary cards:

- Approved drive testers.
- Active workorders.
- Completed workorders.
- `IN_PROGRESS` daily submissions.
- `CHECKED_OUT` daily submissions.
- `COMPLETED` daily submissions.
- File pending count.
- No submission yet count.

Sections:

- Workorder progress list.
- Admin queue.
- Recent daily submissions.

Drill-downs:

- File pending opens Daily Submissions with `file_submission_pending=true`.
- No submission yet opens No Submission Yet page.
- Active workorders opens Workorders filtered to `ACTIVE`.
- Recent daily submission row opens detail.

## Daily Submissions List
Purpose:

- Main admin operations table for daily records.

Filters:

- Work date.
- Date from and date to.
- Region.
- Shift.
- Tester.
- Workorder code.
- Ticket number.
- Daily submission status.
- Workorder status.
- File submission pending.

URL search params should mirror backend query names where possible.

Columns:

- Work date.
- Tester name.
- Tester email.
- Workorder code.
- Region.
- Shift.
- Ticket number.
- Completed grids.
- Skipped grids.
- Force tested grids.
- Daily submission status.
- Workorder status.
- File state.
- Started at.
- Ended at.
- Updated at.
- Row action.

Row actions:

- Open detail.

Do not implement inline edits in V1.

Empty state:

- "No daily submissions match these filters."

## Daily Submission Detail
Purpose:

- Review one daily submission and its context.

Header:

- Tester name.
- Workorder code.
- Work date.
- Shift.
- Ticket number.
- Daily submission status badge.
- File pending badge when applicable.

Primary sections:

- Daily submission values.
- Parent workorder summary.
- Active attachment.
- Attachment history.
- Audit timeline.
- Admin actions.

Daily values:

- Completed grids.
- Skipped grids.
- Force tested grids.
- Started at.
- Ended at.
- Version number if exposed.

Parent workorder summary:

- Workorder code.
- Region.
- Total grids.
- Aggregate completed.
- Aggregate skipped.
- Remaining grids.
- Progress percent.
- Workorder status.

Attachment section:

- Active file name.
- File type.
- File size.
- Uploaded by.
- Uploaded at.
- Download action.

If no active attachment and `file_submission_pending=true`, show a warning:

```text
Closeout file is missing.
This daily submission has been checked out but has no active CSV/XLSX attachment.
```

Attachment history:

- Include inactive and removed file metadata for admins.

Audit timeline:

- Show mutation action, actor, timestamp, and changed fields summary when available.

Actions:

- Edit Submission.
- Reopen Submission when status is `COMPLETED`.
- Download attachment if active file exists.

Edit behavior:

- Open drawer or modal.
- Editable fields should reflect backend support.
- Show warning that changing daily counts can recompute parent workorder progress.

## Daily Submission Edit Drawer
Recommended fields:

- Work date if backend supports admin patch.
- Shift.
- Ticket number.
- Team number as optional or lower-priority field.
- Completed grids.
- Skipped grids.
- Force tested grids.

Do not edit:

- Submitter email snapshot unless backend explicitly supports it.
- Submitter name snapshot unless backend explicitly supports it.
- Audit logs.
- Attachment history metadata.

If an admin note field is not in the backend contract, do not submit it. It may remain as a future UI idea only if clearly marked.

## Workorders List
Purpose:

- Review parent multi-day workorders and aggregate progress.

Filters:

- Workorder code.
- Region.
- Workorder status.
- Date from.
- Date to.

URL search params should mirror backend query names where possible.

Columns:

- Workorder code.
- Region.
- Total grids.
- Aggregate completed grids.
- Aggregate skipped grids.
- Remaining grids.
- Progress percent.
- Workorder status.
- Created at.
- Updated at.
- Row action.

Remaining grids are computed:

```text
total_grids - (completed_grids + skipped_grids)
```

Row actions:

- Open detail.

## Workorder Detail
Purpose:

- Review and edit one parent workorder.

Header:

- Workorder code.
- Region.
- Workorder status.

Summary:

- Total grids.
- Aggregate completed.
- Aggregate skipped.
- Remaining grids.
- Progress percent.

Sections:

- Child daily submissions.
- Audit context.
- Workorder guardrails.

Child submissions table:

- Work date.
- Tester.
- Shift.
- Ticket.
- Completed.
- Skipped.
- Force tested.
- Submission status.
- File state.
- Detail action.

Actions:

- Edit Workorder.

## Workorder Edit Drawer
Editable fields:

- Workorder code.
- Region.
- Total grids.

Warnings:

- Workorder code must remain globally unique after normalization.
- Total grids cannot be reduced below aggregate completed plus skipped.
- Region belongs to the parent workorder and affects date validation by timezone.

## Users
Purpose:

- Review all app users and manage approved accounts.

Filters:

- Role.
- Account status.
- Name or email.

Columns:

- Full name.
- Email.
- Requested role.
- Approved role.
- Account status.
- Created at.
- Last login.
- Approved at.
- Row action.

Actions:

- View user detail when implemented.
- Suspend approved users.

V1 roles:

- `ADMIN`
- `DRIVE_TESTER`

## Pending Users
Purpose:

- Approve or reject users in `PENDING_APPROVAL`.

Filters:

- Requested role.

Fields:

- Full name.
- Email.
- Requested role.
- Created/requested timestamp.

Actions:

- Approve.
- Reject.

Admin role requests should visually feel higher risk than drive tester requests.

## No Submission Yet
Purpose:

- Show approved drive testers with no daily submission record for selected date.

Filters:

- Date.

Required explanatory copy:

```text
No daily submission record exists for the selected date.
This is not assignment-based in V1. It only compares approved drive testers against daily submissions created on the selected date.
```

Columns:

- Tester name.
- Email.
- Approved role.
- Last submission date if available.
- Last workorder if available.

Do not imply that these testers were assigned work.

## Reports
Purpose:

- Export filtered daily submissions as CSV.

Filters:

- Date or date range.
- Region.
- Shift.
- Tester.
- Workorder code.
- Workorder status.
- Daily submission status.
- File submission pending.

Export should include:

- Daily submission fields.
- Tester name and email snapshots.
- Parent workorder fields.
- Aggregate progress fields.
- Computed remaining grids.
- File pending indicator.
- Submission status.
- Workorder status.

PDF export is out of scope for V1 unless product scope changes.

## Common States
Every data page needs:

- Loading state.
- Empty state.
- Error state.
- Permission denied state.
- Success toast for mutations.
- Confirmation dialog for high-impact actions.

## Visual Status Guidance
Suggested badge colors:

- Success green: completed, approved, attached.
- Amber: checked out, pending approval, file pending.
- Blue: active, in progress, role badges.
- Red: rejected, suspended, destructive warnings.
- Gray: not required, inactive, unavailable.

Keep colors restrained and accessible.
