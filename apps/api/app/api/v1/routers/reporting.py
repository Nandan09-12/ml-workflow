import math
import uuid
from datetime import UTC, date, datetime
from typing import Any

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import Shift, SubmissionStatus
from app.core.responses import success_envelope
from app.core.security import get_current_auth_payload
from app.db.session import get_db_session
from app.repositories.reporting_repository import ReportingRepository
from app.schemas.reporting import DashboardSummaryResponse, NoSubmissionYetUserResponse
from app.services.reporting_service import ReportingService

router = APIRouter(prefix="/admin", tags=["reporting"])


def get_reporting_service(
    session: AsyncSession = Depends(get_db_session),
) -> ReportingService:
    return ReportingService(repository=ReportingRepository(session))


@router.get("/dashboard/summary")
async def get_dashboard_summary(
    request: Request,
    work_date: date | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    auth_payload: dict[str, Any] = Depends(get_current_auth_payload),
    service: ReportingService = Depends(get_reporting_service),
) -> dict[str, Any]:
    summary = await service.get_dashboard_summary(
        auth_payload,
        work_date=work_date,
        date_from=date_from,
        date_to=date_to,
    )
    return success_envelope(
        data=DashboardSummaryResponse.model_validate(summary).model_dump(mode="json"),
        request_id=request.state.request_id,
    )


@router.get("/dashboard/no-submission-yet")
async def list_no_submission_yet(
    request: Request,
    work_date: date = Query(...),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    auth_payload: dict[str, Any] = Depends(get_current_auth_payload),
    service: ReportingService = Depends(get_reporting_service),
) -> dict[str, Any]:
    users, total = await service.list_no_submission_yet(
        auth_payload,
        work_date=work_date,
        page=page,
        page_size=page_size,
    )
    items = [NoSubmissionYetUserResponse.model_validate(user).model_dump(mode="json") for user in users]
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    return success_envelope(
        data={
            "work_date": work_date.isoformat(),
            "note": "Best-effort view only; this is not assignment-based.",
            "items": items,
            "count": len(items),
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": total_pages,
            },
        },
        request_id=request.state.request_id,
    )


@router.get("/reports/submissions/export")
async def export_submissions_csv(
    work_date: date | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    status: SubmissionStatus | None = Query(default=None),
    shift: Shift | None = Query(default=None),
    owner_user_id: uuid.UUID | None = Query(default=None),
    ticket_number: str | None = Query(default=None),
    file_submission_pending: bool | None = Query(default=None),
    auth_payload: dict[str, Any] = Depends(get_current_auth_payload),
    service: ReportingService = Depends(get_reporting_service),
) -> Response:
    csv_text = await service.export_submissions_csv(
        auth_payload,
        work_date=work_date,
        date_from=date_from,
        date_to=date_to,
        status=status,
        shift=shift,
        owner_user_id=owner_user_id,
        ticket_number=ticket_number,
        file_submission_pending=file_submission_pending,
    )
    filename_date = datetime.now(UTC).strftime("%Y%m%d")
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="submissions_export_{filename_date}.csv"'
        },
    )

