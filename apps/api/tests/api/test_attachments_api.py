import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import pytest

from app.api.v1.routers.attachments import get_attachment_service
from app.core.security import get_current_auth_payload


@dataclass(frozen=True)
class FakeAttachmentView:
    id: uuid.UUID
    submission_id: uuid.UUID
    file_name: str
    bucket_name: str
    object_path: str
    mime_type: str
    file_extension: str
    file_size_bytes: int
    uploaded_by_user_id: uuid.UUID
    uploaded_at: datetime
    is_active: bool


@dataclass(frozen=True)
class FakeDownloadUrlView:
    url: str
    expires_in_seconds: int


class FakeAttachmentService:
    def __init__(self) -> None:
        now = datetime.now(UTC)
        self.attachment = FakeAttachmentView(
            id=uuid.uuid4(),
            submission_id=uuid.uuid4(),
            file_name="report.csv",
            bucket_name="attachments",
            object_path="submission/report.csv",
            mime_type="text/csv",
            file_extension=".csv",
            file_size_bytes=120,
            uploaded_by_user_id=uuid.uuid4(),
            uploaded_at=now,
            is_active=True,
        )

    async def upload_attachment(self, _: dict[str, Any], __: uuid.UUID, ___: Any) -> FakeAttachmentView:
        return self.attachment

    async def list_attachments(self, _: dict[str, Any], __: uuid.UUID) -> list[FakeAttachmentView]:
        return [self.attachment]

    async def get_attachment(self, _: dict[str, Any], __: uuid.UUID) -> FakeAttachmentView:
        return self.attachment

    async def create_download_url(self, _: dict[str, Any], __: uuid.UUID) -> FakeDownloadUrlView:
        return FakeDownloadUrlView(
            url="https://example.supabase.co/storage/v1/object/sign/attachments/path?token=abc",
            expires_in_seconds=3600,
        )

    async def delete_attachment(self, _: dict[str, Any], __: uuid.UUID) -> None:
        return None


@pytest.fixture
def attachment_service() -> FakeAttachmentService:
    return FakeAttachmentService()


def test_upload_attachment_requires_auth(client: Any) -> None:
    submission_id = uuid.uuid4()
    response = client.post(
        f"/api/v1/submissions/{submission_id}/attachments",
        files={"file": ("report.csv", b"a,b\n1,2", "text/csv")},
    )
    body = response.json()

    assert response.status_code == 401
    assert body["success"] is False
    assert body["error"]["code"] == "UNAUTHORIZED"
    assert "request_id" in body["meta"]


def test_upload_attachment_success_response_envelope(
    client: Any,
    auth_payload_drive_tester: dict[str, Any],
    attachment_service: FakeAttachmentService,
) -> None:
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_drive_tester
    app.dependency_overrides[get_attachment_service] = lambda: attachment_service

    submission_id = uuid.uuid4()
    response = client.post(
        f"/api/v1/submissions/{submission_id}/attachments",
        files={"file": ("report.csv", b"a,b\n1,2", "text/csv")},
    )
    body = response.json()

    assert response.status_code == 201
    assert body["success"] is True
    assert body["data"]["file_name"] == "report.csv"
    assert body["data"]["file_extension"] == ".csv"
    assert "request_id" in body["meta"]


def test_list_attachments_success(
    client: Any,
    auth_payload_drive_tester: dict[str, Any],
    attachment_service: FakeAttachmentService,
) -> None:
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_drive_tester
    app.dependency_overrides[get_attachment_service] = lambda: attachment_service

    response = client.get(f"/api/v1/submissions/{attachment_service.attachment.submission_id}/attachments")
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["count"] == 1
    assert body["data"]["items"][0]["id"] == str(attachment_service.attachment.id)


def test_get_attachment_metadata_invalid_uuid_returns_enveloped_422(
    client: Any,
    auth_payload_drive_tester: dict[str, Any],
    attachment_service: FakeAttachmentService,
) -> None:
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_drive_tester
    app.dependency_overrides[get_attachment_service] = lambda: attachment_service

    response = client.get("/api/v1/attachments/not-a-uuid")
    body = response.json()

    assert response.status_code == 422
    assert body["success"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "request_id" in body["meta"]


def test_create_download_url_success(
    client: Any,
    auth_payload_drive_tester: dict[str, Any],
    attachment_service: FakeAttachmentService,
) -> None:
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_drive_tester
    app.dependency_overrides[get_attachment_service] = lambda: attachment_service

    response = client.post(f"/api/v1/attachments/{attachment_service.attachment.id}/download-url")
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["data"]["expires_in_seconds"] == 3600
    assert body["data"]["url"].startswith("https://")


def test_delete_attachment_returns_204_without_envelope(
    client: Any,
    auth_payload_drive_tester: dict[str, Any],
    attachment_service: FakeAttachmentService,
) -> None:
    app = client.app
    app.dependency_overrides[get_current_auth_payload] = lambda: auth_payload_drive_tester
    app.dependency_overrides[get_attachment_service] = lambda: attachment_service

    response = client.delete(f"/api/v1/attachments/{attachment_service.attachment.id}")

    assert response.status_code == 204
    assert response.text == ""
