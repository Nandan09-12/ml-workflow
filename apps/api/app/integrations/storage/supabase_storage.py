from urllib.parse import quote

import httpx

from app.integrations.storage.base import StorageIntegrationError


class SupabaseStorageProvider:
    def __init__(
        self,
        *,
        supabase_url: str | None,
        service_role_key: str | None,
        timeout_seconds: float = 20.0,
    ) -> None:
        self._supabase_url = supabase_url.rstrip("/") if supabase_url else None
        self._service_role_key = service_role_key
        self._timeout_seconds = timeout_seconds

    async def upload_bytes(
        self,
        *,
        bucket_name: str,
        object_path: str,
        content_type: str,
        data: bytes,
    ) -> None:
        self._validate_config()
        safe_object_path = quote(object_path, safe="/")
        url = f"{self._supabase_url}/storage/v1/object/{bucket_name}/{safe_object_path}"
        headers = self._auth_headers(content_type=content_type)

        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.post(url, headers=headers, content=data)
        if response.status_code >= 400:
            raise StorageIntegrationError(
                f"Upload failed with status {response.status_code}: {response.text}"
            )

    async def create_signed_download_url(
        self,
        *,
        bucket_name: str,
        object_path: str,
        expires_in_seconds: int,
    ) -> str:
        self._validate_config()
        safe_object_path = quote(object_path, safe="/")
        url = f"{self._supabase_url}/storage/v1/object/sign/{bucket_name}/{safe_object_path}"
        headers = self._auth_headers(content_type="application/json")
        payload = {"expiresIn": expires_in_seconds}

        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.post(url, headers=headers, json=payload)
        if response.status_code >= 400:
            raise StorageIntegrationError(
                f"Signed URL generation failed with status {response.status_code}: {response.text}"
            )

        body = response.json()
        signed_url = body.get("signedURL") or body.get("signedUrl") or body.get("url")
        if not isinstance(signed_url, str) or not signed_url:
            raise StorageIntegrationError("Supabase signed URL response did not include a URL.")

        if signed_url.startswith("http://") or signed_url.startswith("https://"):
            return signed_url
        return f"{self._supabase_url}/storage/v1{signed_url}"

    def _validate_config(self) -> None:
        if not self._supabase_url or not self._service_role_key:
            raise StorageIntegrationError(
                "Supabase storage configuration is incomplete. Check SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY."
            )

    def _auth_headers(self, *, content_type: str) -> dict[str, str]:
        assert self._service_role_key is not None
        return {
            "Authorization": f"Bearer {self._service_role_key}",
            "apikey": self._service_role_key,
            "Content-Type": content_type,
            "x-upsert": "false",
        }
