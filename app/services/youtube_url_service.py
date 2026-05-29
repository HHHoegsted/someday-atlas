from __future__ import annotations

from urllib.parse import parse_qs, urlparse


def extract_video_id(youtube_url: str) -> str | None:
    parsed = urlparse(youtube_url.strip())
    host = parsed.netloc.lower()

    if host in {"youtu.be", "www.youtu.be"}:
        candidate = parsed.path.strip("/")
        return candidate or None

    if host in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
        if parsed.path == "/watch":
            return parse_qs(parsed.query).get("v", [None])[0]
        if parsed.path.startswith("/shorts/"):
            candidate = parsed.path.split("/", 2)[2]
            return candidate or None
        if parsed.path.startswith("/embed/"):
            candidate = parsed.path.split("/", 2)[2]
            return candidate or None

    return None


def build_watch_url(youtube_url: str, youtube_id: str | None, timestamp_seconds: int | None = None) -> str:
    if youtube_id:
        base_url = f"https://www.youtube.com/watch?v={youtube_id}"
    else:
        base_url = youtube_url

    if timestamp_seconds is None:
        return base_url

    return f"{base_url}&t={timestamp_seconds}s" if "?" in base_url else f"{base_url}?t={timestamp_seconds}s"