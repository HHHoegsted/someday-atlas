from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


GEOCODING_ENDPOINT = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "SomedayAtlas/0.1 (private homelab geocoding helper)"


def _pick_place_name(candidate: dict[str, Any]) -> str:
    address = candidate.get("address") or {}
    for key in ("city", "town", "village", "hamlet", "municipality", "suburb", "name"):
        value = address.get(key)
        if value:
            return str(value)

    if candidate.get("name"):
        return str(candidate["name"])

    display_name = str(candidate.get("display_name", "")).strip()
    return display_name.split(",", 1)[0].strip() if display_name else "Unknown place"


def _pick_region(candidate: dict[str, Any]) -> str | None:
    address = candidate.get("address") or {}
    for key in ("state", "region", "county", "municipality"):
        value = address.get(key)
        if value:
            return str(value)
    return None


def normalize_geocoding_candidates(payload: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []

    for candidate in payload:
        latitude = candidate.get("lat")
        longitude = candidate.get("lon")
        if latitude is None or longitude is None:
            continue

        candidates.append(
            {
                "place_name": _pick_place_name(candidate),
                "country": (candidate.get("address") or {}).get("country"),
                "region": _pick_region(candidate),
                "latitude": float(latitude),
                "longitude": float(longitude),
                "display_name": str(candidate.get("display_name", "")).strip(),
                "type": str(candidate.get("type", "")).strip(),
            }
        )

    return candidates


def search_places(query: str, limit: int = 5) -> list[dict[str, Any]]:
    encoded_query = urlencode(
        {
            "q": query.strip(),
            "format": "jsonv2",
            "addressdetails": 1,
            "limit": limit,
        }
    )
    request = Request(
        url=f"{GEOCODING_ENDPOINT}?{encoded_query}",
        headers={"User-Agent": USER_AGENT},
        method="GET",
    )

    with urlopen(request, timeout=6) as response:
        payload = json.loads(response.read().decode("utf-8"))

    return normalize_geocoding_candidates(payload)