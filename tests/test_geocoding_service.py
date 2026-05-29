from app.services.geocoding_service import normalize_geocoding_candidates


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