from app.services.youtube_url_service import build_watch_url, extract_video_id


def test_extract_video_id_from_watch_url() -> None:
    assert extract_video_id("https://www.youtube.com/watch?v=abc123xyz") == "abc123xyz"


def test_extract_video_id_from_short_url() -> None:
    assert extract_video_id("https://youtu.be/abc123xyz") == "abc123xyz"


def test_build_watch_url_with_timestamp() -> None:
    assert (
        build_watch_url("https://youtu.be/abc123xyz", "abc123xyz", 1930)
        == "https://www.youtube.com/watch?v=abc123xyz&t=1930s"
    )


def test_build_watch_url_without_parsed_video_id() -> None:
    assert (
        build_watch_url("https://example.com/video", None, 45)
        == "https://example.com/video?t=45s"
    )