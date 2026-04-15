from typing import Any


def success_envelope(
    *,
    data: Any,
    request_id: str,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload_meta: dict[str, Any] = {"request_id": request_id}
    if meta:
        payload_meta.update(meta)
    return {
        "success": True,
        "data": data,
        "meta": payload_meta,
    }


def error_envelope(
    *,
    code: str,
    message: str,
    request_id: str,
    details: Any = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload_meta: dict[str, Any] = {"request_id": request_id}
    if meta:
        payload_meta.update(meta)
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details,
        },
        "meta": payload_meta,
    }
