from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from sqlmodel.orm.session import Session as SQLAlchemySession
from sqlalchemy.orm import selectinload

from app.database import get_session
from app.models import CaptureEvent, Journey, Stop, Video, utcnow
from app.services.geocoding_service import search_places
from app.services.map_payload_service import build_map_payload
from app.services.youtube_url_service import build_watch_url, extract_video_id


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _load_video_or_404(session: Session, video_id: int) -> Video:
    statement = select(Video).where(Video.id == video_id).options(selectinload(Video.journey))
    video = session.exec(statement).one_or_none()
    if video is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    return video


def _load_journey_or_404(session: Session, journey_id: int) -> Journey:
    statement = (
        select(Journey)
        .where(Journey.id == journey_id)
        .options(selectinload(Journey.video), selectinload(Journey.stops))
    )
    journey = session.exec(statement).one_or_none()
    if journey is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journey not found")
    return journey


@router.get("/")
def home(request: Request, session: Session = Depends(get_session)):
    statement = (
        select(Video)
        .options(selectinload(Video.journey).selectinload(Journey.stops))
        .order_by(Video.created_at.desc())
    )
    videos = list(session.exec(statement))
    total_stops = sum(len(video.journey.stops) for video in videos if video.journey)
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "videos": videos,
            "total_stops": total_stops,
            "page_title": "Someday Atlas",
        },
    )


@router.get("/capture")
def capture_page(request: Request, session: Session = Depends(get_session), saved: int = 0):
    statement = select(CaptureEvent).order_by(CaptureEvent.created_at.desc()).limit(12)
    capture_events = list(session.exec(statement))
    remembered_creator = request.cookies.get("atlas_capture_identity", "")
    return templates.TemplateResponse(
        request,
        "capture.html",
        {
            "page_title": "Capture",
            "capture_events": capture_events,
            "remembered_creator": remembered_creator,
            "saved": bool(saved),
        },
    )


@router.post("/capture")
def create_capture_event(
    raw_text: str = Form(...),
    created_by: str = Form(default=""),
    created_by_custom: str = Form(default=""),
    kind: str = Form(default="note"),
    session: Session = Depends(get_session),
):
    creator_name = created_by.strip() or created_by_custom.strip() or None
    capture_event = CaptureEvent(
        created_by=creator_name,
        kind=kind.strip() or "note",
        raw_text=raw_text.strip(),
    )
    session.add(capture_event)
    session.commit()
    response = RedirectResponse(url="/capture?saved=1", status_code=status.HTTP_303_SEE_OTHER)
    if capture_event.created_by:
        response.set_cookie(
            key="atlas_capture_identity",
            value=capture_event.created_by,
            max_age=60 * 60 * 24 * 180,
            samesite="lax",
        )
    return response


@router.get("/videos/new")
def new_video(request: Request):
    return templates.TemplateResponse(
        request,
        "videos_new.html",
        {"page_title": "Add Video"},
    )


@router.post("/videos")
def create_video(
    youtube_url: str = Form(...),
    title: str = Form(...),
    channel_name: str = Form(default=""),
    notes: str = Form(default=""),
    session: Session = Depends(get_session),
):
    video = Video(
        youtube_url=youtube_url.strip(),
        youtube_id=extract_video_id(youtube_url),
        title=title.strip(),
        channel_name=channel_name.strip() or None,
        notes=notes.strip() or None,
    )
    session.add(video)
    session.commit()
    session.refresh(video)
    return RedirectResponse(url=f"/videos/{video.id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/videos/{video_id}")
def video_detail(request: Request, video_id: int, session: Session = Depends(get_session)):
    video = _load_video_or_404(session, video_id)
    return templates.TemplateResponse(
        request,
        "video_detail.html",
        {
            "page_title": video.title,
            "video": video,
            "watch_url": build_watch_url(video.youtube_url, video.youtube_id),
        },
    )


@router.post("/journeys")
def create_journey(
    video_id: int = Form(...),
    name: str = Form(...),
    description: str = Form(default=""),
    session: Session = Depends(get_session),
):
    video = _load_video_or_404(session, video_id)
    if video.journey is not None:
        return RedirectResponse(url=f"/journeys/{video.journey.id}", status_code=status.HTTP_303_SEE_OTHER)

    journey = Journey(
        video_id=video.id,
        name=name.strip(),
        description=description.strip() or None,
    )
    session.add(journey)
    video.updated_at = utcnow()
    session.add(video)
    session.commit()
    session.refresh(journey)
    return RedirectResponse(url=f"/journeys/{journey.id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/journeys/{journey_id}")
def journey_detail(request: Request, journey_id: int, session: Session = Depends(get_session)):
    journey = _load_journey_or_404(session, journey_id)
    ordered_stops = sorted(journey.stops, key=lambda stop: stop.order_index)
    stop_watch_urls = {
        stop.id: build_watch_url(journey.video.youtube_url, journey.video.youtube_id, stop.timestamp_seconds)
        for stop in ordered_stops
        if stop.id is not None
    }
    return templates.TemplateResponse(
        request,
        "journey_detail.html",
        {
            "page_title": journey.name,
            "journey": journey,
            "ordered_stops": ordered_stops,
            "stop_watch_urls": stop_watch_urls,
            "video_watch_url": build_watch_url(journey.video.youtube_url, journey.video.youtube_id),
        },
    )


@router.post("/journeys/{journey_id}/geocode")
def geocode_stop(request: Request, journey_id: int, query: str = Form(default=""), session: Session = Depends(get_session)):
    journey = _load_journey_or_404(session, journey_id)
    normalized_query = query.strip()
    candidates: list[dict[str, object]] = []
    error_message: str | None = None

    if normalized_query:
        try:
            candidates = search_places(normalized_query)
        except Exception:
            error_message = "Geocoding lookup failed. You can still enter the coordinates manually."

    return templates.TemplateResponse(
        request,
        "partials/geocode_results.html",
        {
            "journey": journey,
            "query": normalized_query,
            "candidates": candidates,
            "error_message": error_message,
        },
    )


@router.post("/journeys/{journey_id}/stops")
def create_stop(
    journey_id: int,
    place_name: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    order_index: int = Form(...),
    country: str = Form(default=""),
    region: str = Form(default=""),
    timestamp_seconds: str = Form(default=""),
    note: str = Form(default=""),
    session: Session = Depends(get_session),
):
    journey = _load_journey_or_404(session, journey_id)

    parsed_timestamp = int(timestamp_seconds) if timestamp_seconds.strip() else None
    stop = Stop(
        journey_id=journey.id,
        place_name=place_name.strip(),
        latitude=latitude,
        longitude=longitude,
        order_index=order_index,
        country=country.strip() or None,
        region=region.strip() or None,
        timestamp_seconds=parsed_timestamp,
        note=note.strip() or None,
    )
    session.add(stop)
    journey.updated_at = utcnow()
    session.add(journey)
    session.commit()

    return RedirectResponse(url=f"/journeys/{journey.id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/map")
def map_view(request: Request, session: Session = Depends(get_session)):
    statement = (
        select(Journey)
        .options(selectinload(Journey.video), selectinload(Journey.stops))
        .order_by(Journey.created_at.desc())
    )
    payload = build_map_payload(list(session.exec(statement)))
    return templates.TemplateResponse(
        request,
        "map.html",
        {
            "page_title": "Atlas Map",
            "map_payload": payload,
        },
    )