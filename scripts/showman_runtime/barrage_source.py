from __future__ import annotations

import json
import urllib.error
import urllib.request


def normalize_barrage_event(
    payload: dict[str, object],
    format_name: str = "barragegrab_type3",
) -> dict[str, str]:
    if format_name == "generic":
        user = str(payload.get("user") or payload.get("nickname") or "匿名用户")
        message = str(payload.get("message") or payload.get("content") or "").strip()
        if not message:
            raise ValueError("Generic barrage payload is missing message/content.")
        return {"user": user, "message": message}

    if format_name != "barragegrab_type3":
        raise ValueError(f"Unsupported barrage source format: {format_name}")

    message_type = payload.get("Type")
    if str(message_type) != "3":
        raise ValueError("BarrageGrab payload is not a comment event (Type=3).")
    data = payload.get("Data")
    if not isinstance(data, dict):
        raise ValueError("BarrageGrab payload is missing Data.")
    user_payload = data.get("User")
    user_name = "匿名用户"
    if isinstance(user_payload, dict) and user_payload.get("NickName"):
        user_name = str(user_payload.get("NickName"))
    elif data.get("NickName"):
        user_name = str(data.get("NickName"))
    message = str(data.get("Content") or data.get("Text") or "").strip()
    if not message:
        raise ValueError("BarrageGrab payload is missing Content.")
    return {"user": user_name, "message": message}


def post_barrage_to_bridge(
    bridge_url: str,
    payload: dict[str, object],
    timeout_seconds: float = 5.0,
) -> tuple[bool, str]:
    request = urllib.request.Request(
        bridge_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            status = getattr(response, "status", 200)
            if 200 <= status < 300:
                return True, f"http_{status}"
            return False, f"http_{status}"
    except urllib.error.URLError as exc:
        return False, f"{exc.__class__.__name__}: {exc.reason}"
