from typing import cast

from sqlmodel import Session, SQLModel, create_engine

from app.models import Journey, Location, LocationJourney, LocationJourneyStop, Stop, Video, VideoLocationAppearance
from app.services.map_payload_service import build_map_payload


def build_session() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_build_map_payload_includes_legacy_journeys_and_locations() -> None:
    with build_session() as session:
        video = Video(
            youtube_url="https://www.youtube.com/watch?v=tokyo123",
            youtube_id="tokyo123",
            title="Tokyo walk",
        )
        session.add(video)
        session.commit()
        session.refresh(video)

        journey = Journey(video_id=video.id, name="Tokyo route")
        session.add(journey)
        session.commit()
        session.refresh(journey)

        stop = Stop(
            journey_id=journey.id,
            place_name="Asakusa",
            latitude=35.7148,
            longitude=139.7967,
            order_index=1,
            timestamp_seconds=42,
        )
        session.add(stop)

        location = Location(
            name="Tokyo",
            kind="city",
            country="Japan",
            region="Kanto",
            latitude=35.6762,
            longitude=139.6503,
        )
        session.add(location)
        session.commit()
        session.refresh(location)

        appearance = VideoLocationAppearance(
            video_id=video.id,
            location_id=location.id,
            timestamp_seconds=84,
            note="Skyline overview",
        )
        session.add(appearance)

        location_journey = LocationJourney(root_location_id=location.id, name="Tokyo district circuit")
        session.add(location_journey)
        session.commit()
        session.refresh(journey)
        session.refresh(location)
        session.refresh(location_journey)

        location_journey_stop = LocationJourneyStop(
            journey_id=location_journey.id,
            location_id=location.id,
            order_index=1,
            note="Start in central Tokyo",
        )
        session.add(location_journey_stop)
        session.commit()

        payload = build_map_payload(session, [journey], [location], [location_journey])
        journey_payload = cast(dict[str, object], payload["journeys"][0])
        stop_payload = cast(list[dict[str, object]], journey_payload["stops"])[0]
        location_payload = cast(dict[str, object], payload["locations"][0])
        video_payload = cast(list[dict[str, object]], location_payload["videos"])[0]
        place_journey_payload = cast(dict[str, object], payload["journeys"][1])
        place_journey_stop_payload = cast(list[dict[str, object]], place_journey_payload["stops"])[0]

        assert journey_payload["name"] == "Tokyo route"
        assert cast(str, stop_payload["watch_url"]).endswith("&t=42s")

        assert location_payload["name"] == "Tokyo"
        assert location_payload["subtree_appearance_count"] == 1
        assert cast(str, video_payload["watch_url"]).endswith("&t=84s")
        assert place_journey_payload["journey_type"] == "location"
        assert place_journey_payload["source_label"] == "Tokyo"
        assert place_journey_stop_payload["location_detail_url"] == f"/locations/{location.id}"


def test_build_map_payload_skips_locations_without_coordinates() -> None:
    with build_session() as session:
        location = Location(name="Unmapped", kind="district")
        session.add(location)
        session.commit()

        payload = build_map_payload(session, [], [location], [])

        assert payload == {"journeys": [], "locations": []}