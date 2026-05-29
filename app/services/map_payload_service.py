from __future__ import annotations

from sqlmodel import Session

from app.models import Journey, Location, LocationJourney
from app.services.location_service import build_location_breadcrumb, list_subtree_appearances
from app.services.youtube_url_service import build_watch_url


def _serialize_journeys(journeys: list[Journey]) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []

    for journey in journeys:
        ordered_stops = sorted(journey.stops, key=lambda stop: stop.order_index)
        items.append(
            {
                "id": journey.id,
                "name": journey.name,
                "description": journey.description,
                "journey_type": "video",
                "source_label": journey.video.title,
                "video_title": journey.video.title,
                "detail_url": f"/journeys/{journey.id}",
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
                        "location_detail_url": None,
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

    return items


def _serialize_location_journeys(location_journeys: list[LocationJourney]) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []

    for journey in location_journeys:
        ordered_stops = sorted(journey.stops, key=lambda stop: stop.order_index)
        serialized_stops = []
        for stop in ordered_stops:
            location = stop.location
            if location.latitude is None or location.longitude is None:
                continue

            serialized_stops.append(
                {
                    "id": stop.id,
                    "place_name": location.name,
                    "country": location.country,
                    "region": location.region,
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                    "order_index": stop.order_index,
                    "timestamp_seconds": None,
                    "note": stop.note,
                    "location_detail_url": f"/locations/{location.id}",
                    "watch_url": None,
                }
            )

        if not serialized_stops:
            continue

        items.append(
            {
                "id": journey.id,
                "name": journey.name,
                "description": journey.description,
                "journey_type": "location",
                "source_label": journey.root_location.name,
                "video_title": None,
                "detail_url": f"/location-journeys/{journey.id}",
                "youtube_url": None,
                "stops": serialized_stops,
            }
        )

    return items


def _serialize_locations(session: Session, locations: list[Location]) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []

    for location in locations:
        if location.latitude is None or location.longitude is None:
            continue

        breadcrumb = build_location_breadcrumb(session, location)
        subtree_appearances = list_subtree_appearances(session, location.id)
        direct_appearances = sorted(
            location.video_appearances,
            key=lambda appearance: (
                appearance.order_index if appearance.order_index is not None else 1_000_000,
                appearance.timestamp_seconds if appearance.timestamp_seconds is not None else 1_000_000,
                appearance.video.title.lower() if appearance.video else "",
            ),
        )

        items.append(
            {
                "id": location.id,
                "name": location.name,
                "kind": location.kind,
                "country": location.country,
                "region": location.region,
                "latitude": location.latitude,
                "longitude": location.longitude,
                "notes": location.notes,
                "detail_url": f"/locations/{location.id}",
                "breadcrumb": [crumb.name for crumb in breadcrumb],
                "child_count": len(location.children),
                "direct_appearance_count": len(direct_appearances),
                "subtree_appearance_count": len(subtree_appearances),
                "videos": [
                    {
                        "id": appearance.video.id,
                        "title": appearance.video.title,
                        "timestamp_seconds": appearance.timestamp_seconds,
                        "note": appearance.note,
                        "watch_url": build_watch_url(
                            appearance.video.youtube_url,
                            appearance.video.youtube_id,
                            appearance.timestamp_seconds,
                        ),
                    }
                    for appearance in direct_appearances
                    if appearance.video is not None and appearance.video.id is not None
                ],
            }
        )

    return items


def build_map_payload(
    session: Session,
    journeys: list[Journey],
    locations: list[Location],
    location_journeys: list[LocationJourney],
) -> dict[str, list[dict[str, object]]]:
    return {
        "journeys": _serialize_journeys(journeys) + _serialize_location_journeys(location_journeys),
        "locations": _serialize_locations(session, locations),
    }