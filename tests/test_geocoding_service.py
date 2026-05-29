import json

from app.services import geocoding_service
from app.services.geocoding_service import normalize_geocoding_candidates, search_places


def test_normalize_geocoding_candidates_picks_place_country_region_and_coordinates() -> None:
    payload = [
        {
            "display_name": "Melby, Halsnaes Municipality, Capital Region of Denmark, Denmark",
            "lat": "56.0685",
            "lon": "12.1066",
            "address": {
                "village": "Melby",
                "municipality": "Halsnaes Municipality",
                "state": "Capital Region of Denmark",
                "country": "Denmark",
            },
            "type": "village",
        }
    ]

    result = normalize_geocoding_candidates(payload)

    assert result == [
        {
            "place_name": "Melby",
            "country": "Denmark",
            "region": "Capital Region of Denmark",
            "latitude": 56.0685,
            "longitude": 12.1066,
            "display_name": "Melby, Halsnaes Municipality, Capital Region of Denmark, Denmark",
            "type": "village",
        }
    ]


def test_normalize_geocoding_candidates_falls_back_to_display_name_when_needed() -> None:
    payload = [
        {
            "display_name": "Melby, Denmark",
            "lat": "56.0000",
            "lon": "12.0000",
            "address": {"country": "Denmark"},
        }
    ]

    result = normalize_geocoding_candidates(payload)

    assert result[0]["place_name"] == "Melby"


def test_search_places_requests_english_results(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self) -> bytes:
            return json.dumps([]).encode("utf-8")

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["headers"] = dict(request.header_items())
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(geocoding_service, "urlopen", fake_urlopen)

    search_places("Melby, Denmark")

    assert "accept-language=en" in str(captured["url"])
    assert captured["headers"]["Accept-language"] == "en"
    assert captured["timeout"] == 6