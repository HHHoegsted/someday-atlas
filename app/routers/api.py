from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

from app.database import get_session
from app.models import Journey
from app.services.map_payload_service import build_map_payload


router = APIRouter(prefix="/api")


@router.get("/map/journeys")
def map_journeys(session: Session = Depends(get_session)) -> dict[str, list[dict[str, object]]]:
    statement = select(Journey).options(selectinload(Journey.video), selectinload(Journey.stops))
    journeys = list(session.exec(statement))
    return build_map_payload(journeys)


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

    payload = build_map_payload([journey])
    return payload["journeys"][0]