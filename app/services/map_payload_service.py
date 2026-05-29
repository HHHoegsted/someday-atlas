from __future__ import annotations

from app.models import Journey
from app.services.youtube_url_service import build_watch_url


def build_map_payload(journeys: list[Journey]) -> dict[str, list[dict[str, object]]]:
    items: list[dict[str, object]] = []

    for journey in journeys:
        ordered_stops = sorted(journey.stops, key=lambda stop: stop.order_index)
        items.append(
            {
                "id": journey.id,
                "name": journey.name,
                "description": journey.description,
                "video_title": journey.video.title,
                "youtube_url": build_watch_url(journey.video.youtube_url, journey.video.youtube_id),
                "stops": [
                    {
                        "id": stop.id,
                        "place_name": stop.place_name,
                        "country": stop.country,
                        "region": stop.region,
                        "latitude": stop.latitude,
                        "longitude": stop.longitude,
                        "order_index": stop.order_index,
                        "timestamp_seconds": stop.timestamp_seconds,
                        "note": stop.note,
                        "watch_url": build_watch_url(
                            journey.video.youtube_url,
                            journey.video.youtube_id,
                            stop.timestamp_seconds,
                        ),
                    }
                    for stop in ordered_stops
                ],
            }
        )

    return {"journeys": items}