from fastapi import APIRouter

from app.api.v1.routers import (
    admin_submissions,
    admin_users,
    admin_workorders,
    attachments,
    expenses,
    health,
    mileage,
    me,
    mobile,
    reporting,
    submissions,
    workorders,
)

api_v1_router = APIRouter()
api_v1_router.include_router(health.router)
api_v1_router.include_router(me.router)
api_v1_router.include_router(expenses.router)
api_v1_router.include_router(mileage.router)
api_v1_router.include_router(admin_users.router)
api_v1_router.include_router(submissions.router)
api_v1_router.include_router(admin_submissions.router)
api_v1_router.include_router(admin_workorders.router)
api_v1_router.include_router(attachments.router)
api_v1_router.include_router(reporting.router)
api_v1_router.include_router(mobile.router)
api_v1_router.include_router(workorders.router)
