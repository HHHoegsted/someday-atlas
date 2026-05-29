from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

from app.database import get_session
from app.models import Journey, Location, LocationJourney, LocationJourneyStop, VideoLocationAppearance
from app.services.map_payload_service import build_map_payload


router = APIRouter(prefix="/api")


@router.get("/map/journeys")
def map_journeys(session: Session = Depends(get_session)) -> dict[str, list[dict[str, object]]]:
    statement = select(Journey).options(selectinload(Journey.video), selectinload(Journey.stops))
    journeys = list(session.exec(statement))
    locations = _load_map_locations(session)
    location_journeys = _load_map_location_journeys(session)
    return build_map_payload(session, journeys, locations, location_journeys)


@router.get("/map")
def atlas_map(session: Session = Depends(get_session)) -> dict[str, list[dict[str, object]]]:
    journey_statement = select(Journey).options(selectinload(Journey.video), selectinload(Journey.stops))
    journeys = list(session.exec(journey_statement))
    locations = _load_map_locations(session)
    location_journeys = _load_map_location_journeys(session)
    return build_map_payload(session, journeys, locations, location_journeys)


@router.get("/journeys/{journey_id}/stops")
def journey_stops(journey_id: int, session: Session = Depends(get_session)) -> dict[str, object]:
    statement = (
        select(Journey)
        .where(Journey.id == journey_id)
        .options(selectinload(Journey.video), selectinload(Journey.stops))
    )
    journey = session.exec(statement).one_or_none()
    if journey is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journey not found")

    payload = build_map_payload(session, [journey], [], [])
    return payload["journeys"][0]


def _load_map_locations(session: Session) -> list[Location]:
    statement = (
        select(Location)
        .options(
            selectinload(Location.children),
            selectinload(Location.video_appearances).selectinload(VideoLocationAppearance.video),
        )
        .order_by(Location.created_at.desc())
    )
    return list(session.exec(statement))


def _load_map_location_journeys(session: Session) -> list[LocationJourney]:
    statement = (
        select(LocationJourney)
        .options(
            selectinload(LocationJourney.start_location),
            selectinload(LocationJourney.stops).selectinload(LocationJourneyStop.location),
        )
        .order_by(LocationJourney.created_at.desc())
    )
    return list(session.exec(statement))