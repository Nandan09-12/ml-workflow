from enum import StrEnum


class RequestedRole(StrEnum):
    DRIVE_TESTER = "DRIVE_TESTER"
    ADMIN = "ADMIN"


class AccountStatus(StrEnum):
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SUSPENDED = "SUSPENDED"


class Zone(StrEnum):
    NORTHEAST = "NORTHEAST"
    CENTRAL = "CENTRAL"
    SOUTH_FLORIDA = "SOUTH_FLORIDA"


class Region(StrEnum):
    NE_UP = "NE_UP"
    CENTRAL = "CENTRAL"
    SOUTH_FLORIDA = "SOUTH_FLORIDA"


class Shift(StrEnum):
    AM = "AM"
    PM = "PM"


class SubmissionStatus(StrEnum):
    IN_PROGRESS = "IN_PROGRESS"
    CHECKED_OUT = "CHECKED_OUT"
    COMPLETED = "COMPLETED"


class WorkorderStatus(StrEnum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"


class ApprovalDecision(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class AuditActionType(StrEnum):
    CREATED = "CREATED"
    UPDATED = "UPDATED"
    STATUS_CHANGED = "STATUS_CHANGED"
    COMPLETED = "COMPLETED"
    REOPENED = "REOPENED"
    FILE_UPLOADED = "FILE_UPLOADED"
    FILE_REMOVED = "FILE_REMOVED"


class AuditSource(StrEnum):
    MOBILE = "MOBILE"
    WEB = "WEB"
    ADMIN_CONSOLE = "ADMIN_CONSOLE"
    SYNC = "SYNC"
