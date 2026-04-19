from __future__ import annotations

from dataclasses import asdict, dataclass, field
import base64
import json
import re
from urllib.parse import urljoin
import urllib.error
import urllib.request

from .live_config import AIGCPanelLauncherConfig


DEFAULT_BASE_URLS = (
    "http://127.0.0.1:8888",
    "http://127.0.0.1:3030",
)
RUN_RESULT_RE = re.compile(r"AigcPanelRunResult\[[^\]]*\]\[([A-Za-z0-9+/=]+)\]")
LAUNCHER_DATA_RE = re.compile(r"(/launcher-data/[^\s\"'\]]+)")
WINDOWS_MEDIA_PATH_RE = re.compile(r"([A-Za-z]:[\\/][^\r\n\"']+\.(?:wav|mp3|m4a|ogg|flac|mp4|mov|mkv|webm|png|jpg|jpeg))", re.IGNORECASE)


@dataclass(slots=True)
class AIGCPanelCallResult:
    ok: bool
    action: str
    message: str
    status: str = ""
    token: str | None = None
    logs: str | None = None
    payload: dict[str, object] = field(default_factory=dict)
    response: dict[str, object] = field(default_factory=dict)
    base_url: str | None = None
    remote_config: dict[str, object] = field(default_factory=dict)
    resolved_launcher: dict[str, object] = field(default_factory=dict)
    result_data: dict[str, object] = field(default_factory=dict)
    artifacts: list[dict[str, str]] = field(default_factory=list)
    media_url: str | None = None
    media_kind: str | None = None
    local_path: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _string_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _string_mapping(value: object) -> dict[str, str]:
    if isinstance(value, dict):
        return {
            str(key).strip(): str(item).strip()
            for key, item in value.items()
            if str(key).strip()
        }
    if isinstance(value, list):
        mapping: dict[str, str] = {}
        for item in value:
            text = str(item).strip()
            if not text or "=" not in text:
                continue
            key, raw_value = text.split("=", 1)
            key = key.strip()
            if key:
                mapping[key] = raw_value.strip()
        return mapping
    return {}


def _dedupe_urls(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        candidate = _text(value).rstrip("/")
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        ordered.append(candidate)
    return ordered


def _candidate_base_urls(config: AIGCPanelLauncherConfig) -> list[str]:
    return _dedupe_urls(
        [
            config.base_url,
            *config.probe_base_urls,
            *DEFAULT_BASE_URLS,
        ]
    )


def _apply_placeholders(text: str | None, placeholders: dict[str, str]) -> str | None:
    if text is None:
        return None
    result = text
    for key, value in placeholders.items():
        result = result.replace("${" + key + "}", value)
    return result


def _decode_logs(value: object) -> str:
    if value in (None, ""):
        return ""
    try:
        raw = base64.b64decode(str(value), validate=False)
    except (ValueError, TypeError):
        return str(value)
    return raw.decode("utf-8", errors="replace")


def _request_json(
    *,
    method: str,
    url: str,
    payload: dict[str, object] | None,
    headers: dict[str, str],
    timeout: float,
) -> tuple[bool, dict[str, object]]:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", **headers},
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw_body = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        raw_body = exc.read().decode("utf-8", errors="replace")
        try:
            payload_obj = json.loads(raw_body)
        except json.JSONDecodeError:
            payload_obj = {"code": -1, "msg": raw_body or f"HTTP {exc.code}", "data": {}}
        return False, payload_obj
    except urllib.error.URLError as exc:
        return False, {"code": -1, "msg": f"{exc.__class__.__name__}: {exc.reason}", "data": {}}

    try:
        parsed = json.loads(raw_body)
    except json.JSONDecodeError:
        parsed = {"code": -1, "msg": raw_body or "Invalid JSON response", "data": {}}
    if not isinstance(parsed, dict):
        parsed = {"code": -1, "msg": "Invalid response payload", "data": {}}
    ok = parsed.get("code") == 0
    return ok, parsed


def _normalize_remote_config(response: dict[str, object]) -> dict[str, object]:
    data = response.get("data", {}) if isinstance(response.get("data"), dict) else {}
    launcher = data.get("launcher", {}) if isinstance(data.get("launcher"), dict) else {}
    resolved = {
        "name": _text(data.get("name")),
        "title": _text(data.get("title")),
        "version": _text(data.get("version")),
        "entry": _text(launcher.get("entry")),
        "entryArgs": _string_list(launcher.get("entryArgs")),
        "envs": _string_mapping(launcher.get("envs")),
        "root": _text(launcher.get("root")),
    }
    return {key: value for key, value in resolved.items() if value not in ("", [], {})}


def _resolve_launcher_contract(
    config: AIGCPanelLauncherConfig,
    remote_config: dict[str, object] | None = None,
) -> dict[str, object]:
    remote = remote_config or {}
    envs = {
        **_string_mapping(remote.get("envs")),
        **config.envs,
    }
    resolved = {
        "entry": config.entry or _text(remote.get("entry")),
        "entryArgs": list(config.entry_args or _string_list(remote.get("entryArgs"))),
        "envs": envs,
        "root": config.root or _text(remote.get("root")) or None,
    }
    return {
        key: value
        for key, value in resolved.items()
        if value not in (None, "", [], {})
    }


def build_aigcpanel_submit_payload(
    config: AIGCPanelLauncherConfig,
    text: str,
    context: dict[str, object] | None = None,
    remote_config: dict[str, object] | None = None,
) -> dict[str, object]:
    launcher = _resolve_launcher_contract(config, remote_config=remote_config)
    entry = _text(launcher.get("entry"))
    if not entry:
        raise ValueError("AIGCPanel launcher entry is not configured.")

    runtime_context = {
        "TEXT": text,
        "MESSAGE": text,
        "HOST_NAME": str((context or {}).get("host_name") or ""),
        "PRODUCT_NAME": str((context or {}).get("product_name") or ""),
        "PRODUCT_ID": str((context or {}).get("product_id") or ""),
        "ROOM_TITLE": str((context or {}).get("room_title") or ""),
        "SESSION_ID": str((context or {}).get("session_id") or ""),
    }
    placeholders = {
        key: value
        for key, value in {**config.entry_placeholders, **runtime_context}.items()
        if value
    }
    payload: dict[str, object] = {
        "entry": entry,
        "entryPlaceholders": placeholders,
    }
    entry_args = _string_list(launcher.get("entryArgs"))
    if entry_args:
        payload["entryArgs"] = entry_args
    envs = _string_mapping(launcher.get("envs"))
    if envs:
        payload["envs"] = {
            key: _apply_placeholders(value, placeholders) or ""
            for key, value in envs.items()
        }
    root = _apply_placeholders(_text(launcher.get("root")) or None, placeholders)
    if root:
        payload["root"] = root
    return payload


def _guess_media_kind(reference: str) -> str | None:
    lowered = reference.lower().split("?", 1)[0]
    if lowered.endswith((".wav", ".mp3", ".m4a", ".ogg", ".flac")):
        return "audio"
    if lowered.endswith((".mp4", ".mov", ".mkv", ".webm")):
        return "video"
    if lowered.endswith((".png", ".jpg", ".jpeg", ".webp")):
        return "image"
    return None


def _normalize_artifact_reference(reference: str, base_url: str) -> dict[str, str] | None:
    text = _text(reference)
    if not text:
        return None
    normalized = text.replace("\\", "/")
    artifact = {
        "source": text,
        "kind": _guess_media_kind(text) or "",
        "url": "",
        "local_path": "",
    }
    if normalized.startswith("http://") or normalized.startswith("https://"):
        artifact["url"] = text
        return artifact
    if normalized.startswith("/launcher-data/"):
        artifact["url"] = urljoin(base_url.rstrip("/") + "/", normalized.lstrip("/"))
        return artifact
    if normalized.startswith("launcher-data/"):
        artifact["url"] = urljoin(base_url.rstrip("/") + "/", normalized.lstrip("/"))
        return artifact
    if re.match(r"^[A-Za-z]:[\\/]", text) or text.startswith("\\\\"):
        artifact["local_path"] = text
        return artifact
    if "/" in normalized and _guess_media_kind(normalized):
        artifact["local_path"] = text
        return artifact
    return None


def _decode_run_result(encoded: str) -> dict[str, object]:
    try:
        raw = base64.b64decode(encoded, validate=False)
    except (ValueError, TypeError):
        return {}
    try:
        parsed = json.loads(raw.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(parsed, dict):
        return {}
    return {str(key): value for key, value in parsed.items()}


def _append_artifact(
    artifacts: list[dict[str, str]],
    artifact: dict[str, str] | None,
    seen: set[tuple[str, str]],
    *,
    field_name: str = "",
) -> None:
    if artifact is None:
        return
    key = (artifact.get("source") or "", artifact.get("local_path") or artifact.get("url") or "")
    if key in seen:
        return
    seen.add(key)
    artifacts.append(
        {
            "field": field_name,
            "source": artifact.get("source") or "",
            "url": artifact.get("url") or "",
            "local_path": artifact.get("local_path") or "",
            "kind": artifact.get("kind") or "",
        }
    )


def parse_aigcpanel_query_logs(logs: str, base_url: str) -> dict[str, object]:
    merged: dict[str, object] = {}
    artifacts: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for match in RUN_RESULT_RE.finditer(logs):
        result_data = _decode_run_result(match.group(1))
        if not result_data:
            continue
        merged.update(result_data)
        for field_name, value in result_data.items():
            if not isinstance(value, str):
                continue
            _append_artifact(
                artifacts,
                _normalize_artifact_reference(value, base_url),
                seen,
                field_name=field_name,
            )

    for match in LAUNCHER_DATA_RE.finditer(logs):
        _append_artifact(
            artifacts,
            _normalize_artifact_reference(match.group(1), base_url),
            seen,
            field_name="launcher-data",
        )
    for match in WINDOWS_MEDIA_PATH_RE.finditer(logs):
        _append_artifact(
            artifacts,
            _normalize_artifact_reference(match.group(1), base_url),
            seen,
            field_name="file",
        )

    preferred_fields = ("video", "audio", "url", "file", "output")
    selected: dict[str, str] | None = None
    for preferred in preferred_fields:
        selected = next((item for item in artifacts if item.get("field") == preferred), None)
        if selected:
            break
    if selected is None and artifacts:
        selected = artifacts[0]

    return {
        "result_data": merged,
        "artifacts": artifacts,
        "media_url": selected.get("url") if selected else None,
        "media_kind": selected.get("kind") if selected else None,
        "local_path": selected.get("local_path") if selected else None,
    }


def probe_aigcpanel_launcher(config: AIGCPanelLauncherConfig) -> AIGCPanelCallResult:
    first_error: AIGCPanelCallResult | None = None
    for base_url in _candidate_base_urls(config):
        ping_ok, ping_response = _request_json(
            method="GET",
            url=urljoin(base_url.rstrip("/") + "/", config.ping_path.lstrip("/")),
            payload=None,
            headers=config.headers,
            timeout=config.timeout_seconds,
        )
        config_ok, config_response = _request_json(
            method="POST",
            url=urljoin(base_url.rstrip("/") + "/", config.config_path.lstrip("/")),
            payload={},
            headers=config.headers,
            timeout=config.timeout_seconds,
        )
        remote_config = _normalize_remote_config(config_response if config_ok else {})
        if ping_ok or config_ok:
            resolved_launcher = _resolve_launcher_contract(config, remote_config=remote_config)
            return AIGCPanelCallResult(
                ok=True,
                action="probe",
                message=_text(config_response.get("msg")) or _text(ping_response.get("msg")) or "ok",
                status="ready" if resolved_launcher.get("entry") else "reachable",
                base_url=base_url,
                response={
                    "ping": ping_response,
                    "config": config_response,
                },
                remote_config=remote_config,
                resolved_launcher=resolved_launcher,
            )
        error_result = AIGCPanelCallResult(
            ok=False,
            action="probe",
            message=_text(config_response.get("msg")) or _text(ping_response.get("msg")) or "Launcher not reachable",
            status="error",
            base_url=base_url,
            response={
                "ping": ping_response,
                "config": config_response,
            },
        )
        if first_error is None:
            first_error = error_result
    return first_error or AIGCPanelCallResult(
        ok=False,
        action="probe",
        message="AIGCPanel launcher base URL is not configured.",
        status="error",
    )


def ping_aigcpanel_launcher(config: AIGCPanelLauncherConfig) -> AIGCPanelCallResult:
    probe = probe_aigcpanel_launcher(config)
    probe.action = "ping"
    return probe


def submit_aigcpanel_launcher_task(
    config: AIGCPanelLauncherConfig,
    text: str,
    context: dict[str, object] | None = None,
) -> AIGCPanelCallResult:
    if not config.enabled:
        raise ValueError("AIGCPanel launcher is disabled in config.")
    probe = probe_aigcpanel_launcher(config)
    remote_config = probe.remote_config if probe.ok else {}
    base_url = probe.base_url or config.base_url
    payload = build_aigcpanel_submit_payload(
        config,
        text,
        context=context,
        remote_config=remote_config,
    )
    ok, response = _request_json(
        method="POST",
        url=urljoin(base_url.rstrip("/") + "/", config.submit_path.lstrip("/")),
        payload=payload,
        headers=config.headers,
        timeout=config.timeout_seconds,
    )
    data = response.get("data", {}) if isinstance(response.get("data"), dict) else {}
    return AIGCPanelCallResult(
        ok=ok,
        action="submit",
        message=_text(response.get("msg")),
        status="submitted" if ok else "error",
        token=_text(data.get("token")) or None,
        payload=payload,
        response=response,
        base_url=base_url,
        remote_config=remote_config,
        resolved_launcher=_resolve_launcher_contract(config, remote_config=remote_config),
    )


def query_aigcpanel_launcher_task(
    config: AIGCPanelLauncherConfig,
    token: str,
) -> AIGCPanelCallResult:
    if not token:
        raise ValueError("AIGCPanel task token is required for query.")
    base_url = _candidate_base_urls(config)[0]
    payload = {"token": token}
    ok, response = _request_json(
        method="POST",
        url=urljoin(base_url.rstrip("/") + "/", config.query_path.lstrip("/")),
        payload=payload,
        headers=config.headers,
        timeout=config.timeout_seconds,
    )
    data = response.get("data", {}) if isinstance(response.get("data"), dict) else {}
    logs = _decode_logs(data.get("logs"))
    parsed = parse_aigcpanel_query_logs(logs, base_url=base_url)
    return AIGCPanelCallResult(
        ok=ok,
        action="query",
        message=_text(response.get("msg")),
        status=_text(data.get("status")) or ("success" if ok else "error"),
        token=token,
        logs=logs,
        payload=payload,
        response=response,
        base_url=base_url,
        result_data=parsed["result_data"],
        artifacts=parsed["artifacts"],
        media_url=parsed["media_url"],
        media_kind=parsed["media_kind"],
        local_path=parsed["local_path"],
    )


def cancel_aigcpanel_launcher_task(config: AIGCPanelLauncherConfig) -> AIGCPanelCallResult:
    base_url = _candidate_base_urls(config)[0]
    ok, response = _request_json(
        method="POST",
        url=urljoin(base_url.rstrip("/") + "/", config.cancel_path.lstrip("/")),
        payload={},
        headers=config.headers,
        timeout=config.timeout_seconds,
    )
    return AIGCPanelCallResult(
        ok=ok,
        action="cancel",
        message=_text(response.get("msg")),
        status="cancelled" if ok else "error",
        response=response,
        base_url=base_url,
    )
