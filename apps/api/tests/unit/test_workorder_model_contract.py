from sqlalchemy import Enum

from app.core.enums import Region, WorkorderStatus
from app.models.submission import Submission
from app.models.workorder import Workorder


def test_workorder_model_uses_region_and_workorder_status_enums() -> None:
    region_column = Workorder.__table__.c.region
    status_column = Workorder.__table__.c.status

    assert isinstance(region_column.type, Enum)
    assert region_column.type.enum_class is Region
    assert isinstance(status_column.type, Enum)
    assert status_column.type.enum_class is WorkorderStatus


def test_workorder_model_exposes_required_parent_columns() -> None:
    columns = Workorder.__table__.c

    assert "workorder_code" in columns
    assert "workorder_code_normalized" in columns
    assert "total_grids" in columns
    assert "created_by_user_id" in columns
    assert "updated_by_user_id" in columns
    assert "completed_at" in columns
    assert "completed_by_user_id" in columns


def test_submission_model_includes_workorder_foreign_key() -> None:
    columns = Submission.__table__.c

    assert "workorder_id" in columns
