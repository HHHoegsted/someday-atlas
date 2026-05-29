from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

from app.database import get_session
from app.models import (
    CaptureEvent,
    Journey,
    Location,
    LocationJourney,
    LocationJourneyStop,
    Stop,
    Video,
    VideoLocationAppearance,
    utcnow,
)
from app.services.geocoding_service import search_places
from app.services.location_service import build_location_breadcrumb, collect_descendant_ids, list_subtree_appearances
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


def _load_location_or_404(session: Session, location_id: int) -> Location:
    statement = (
        select(Location)
        .where(Location.id == location_id)
        .options(
            selectinload(Location.children),
            selectinload(Location.video_appearances).selectinload(VideoLocationAppearance.video),
        )
    )
    location = session.exec(statement).one_or_none()
    if location is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
    return location


def _load_location_journey_or_404(session: Session, journey_id: int) -> LocationJourney:
    statement = (
        select(LocationJourney)
        .where(LocationJourney.id == journey_id)
        .options(
            selectinload(LocationJourney.root_location),
            selectinload(LocationJourney.stops).selectinload(LocationJourneyStop.location),
        )
    )
    journey = session.exec(statement).one_or_none()
    if journey is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location journey not found")
    return journey


def _parse_optional_float(value: str) -> float | None:
    normalized = value.strip()
    return float(normalized) if normalized else None


def _parse_optional_int(value: str) -> int | None:
    normalized = value.strip()
    return int(normalized) if normalized else None


@router.get("/")
def home(request: Request, session: Session = Depends(get_session)):
    root_locations_statement = (
        select(Location)
        .where(Location.parent_location_id.is_(None))
        .options(
            selectinload(Location.children),
            selectinload(Location.video_appearances),
            selectinload(Location.root_journeys),
        )
        .order_by(Location.name.asc())
    )
    root_locations = list(session.exec(root_locations_statement))

    recent_location_journeys_statement = (
        select(LocationJourney)
        .options(
            selectinload(LocationJourney.root_location),
            selectinload(LocationJourney.stops).selectinload(LocationJourneyStop.location),
        )
        .order_by(LocationJourney.created_at.desc())
        .limit(6)
    )
    recent_location_journeys = list(session.exec(recent_location_journeys_statement))

    recent_videos_statement = (
        select(Video)
        .options(selectinload(Video.journey).selectinload(Journey.stops))
        .order_by(Video.created_at.desc())
        .limit(6)
    )
    recent_videos = list(session.exec(recent_videos_statement))

    total_appearances = sum(len(location.video_appearances) for location in root_locations)
    total_root_journeys = sum(len(location.root_journeys) for location in root_locations)
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "root_locations": root_locations,
            "recent_location_journeys": recent_location_journeys,
            "recent_videos": recent_videos,
            "total_appearances": total_appearances,
            "total_root_journeys": total_root_journeys,
            "hide_global_header": True,
            "page_title": "Someday Atlas",
        },
    )


@router.get("/locations")
def locations_index(request: Request, session: Session = Depends(get_session)):
    statement = (
        select(Location)
        .where(Location.parent_location_id.is_(None))
        .options(selectinload(Location.children), selectinload(Location.video_appearances))
        .order_by(Location.name.asc())
    )
    locations = list(session.exec(statement))
    total_appearances = sum(len(location.video_appearances) for location in locations)
    return templates.TemplateResponse(
        request,
        "locations_index.html",
        {
            "page_title": "Locations",
            "locations": locations,
            "total_appearances": total_appearances,
        },
    )


@router.post("/locations")
def create_location(
    name: str = Form(...),
    kind: str = Form(default="place"),
    country: str = Form(default=""),
    region: str = Form(default=""),
    latitude: str = Form(default=""),
    longitude: str = Form(default=""),
    notes: str = Form(default=""),
    session: Session = Depends(get_session),
):
    location = Location(
        name=name.strip(),
        kind=kind.strip() or "place",
        country=country.strip() or None,
        region=region.strip() or None,
        latitude=_parse_optional_float(latitude),
        longitude=_parse_optional_float(longitude),
        notes=notes.strip() or None,
    )
    session.add(location)
    session.commit()
    session.refresh(location)
    return RedirectResponse(url=f"/locations/{location.id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/locations/geocode")
def geocode_location(request: Request, query: str = Form(default="")):
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
            "query": normalized_query,
            "candidates": candidates,
            "error_message": error_message,
            "apply_context": "location",
            "success_copy": "Choose the best hit for \"{query}\". You can still edit the location before saving it.",
        },
    )


@router.post("/locations/{location_id}")
def update_location(
    location_id: int,
    name: str = Form(...),
    kind: str = Form(default="place"),
    country: str = Form(default=""),
    region: str = Form(default=""),
    latitude: str = Form(default=""),
    longitude: str = Form(default=""),
    notes: str = Form(default=""),
    redirect_to: str = Form(default=""),
    session: Session = Depends(get_session),
):
    location = _load_location_or_404(session, location_id)
    location.name = name.strip()
    location.kind = kind.strip() or "place"
    location.country = country.strip() or None
    location.region = region.strip() or None
    location.latitude = _parse_optional_float(latitude)
    location.longitude = _parse_optional_float(longitude)
    location.notes = notes.strip() or None
    location.updated_at = utcnow()
    session.add(location)
    session.commit()
    return RedirectResponse(
        url=redirect_to.strip() or f"/locations/{location.id}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/locations/{location_id}")
def location_detail(request: Request, location_id: int, session: Session = Depends(get_session)):
    location = _load_location_or_404(session, location_id)
    breadcrumb = build_location_breadcrumb(session, location)
    child_locations = sorted(location.children, key=lambda child: (child.kind, child.name.lower()))
    direct_appearances = sorted(
        location.video_appearances,
        key=lambda appearance: (
            appearance.order_index if appearance.order_index is not None else 1_000_000,
            appearance.timestamp_seconds if appearance.timestamp_seconds is not None else 1_000_000,
            appearance.video.title.lower() if appearance.video else "",
        ),
    )
    root_journey_statement = (
        select(LocationJourney)
        .where(LocationJourney.root_location_id == location.id)
        .options(selectinload(LocationJourney.stops).selectinload(LocationJourneyStop.location))
        .order_by(LocationJourney.created_at.desc())
    )
    root_journeys = list(session.exec(root_journey_statement))
    return templates.TemplateResponse(
        request,
        "location_detail.html",
        {
            "page_title": location.name,
            "location": location,
            "breadcrumb": breadcrumb,
            "child_locations": child_locations,
            "direct_appearances": direct_appearances,
            "root_journeys": root_journeys,
        },
    )


@router.get("/locations/{location_id}/edit")
def edit_location_page(request: Request, location_id: int, session: Session = Depends(get_session)):
    location = _load_location_or_404(session, location_id)
    breadcrumb = build_location_breadcrumb(session, location)
    return templates.TemplateResponse(
        request,
        "location_edit.html",
        {
            "page_title": f"Edit {location.name}",
            "location": location,
            "breadcrumb": breadcrumb,
        },
    )


@router.get("/locations/{location_id}/children/new")
def new_child_location_page(request: Request, location_id: int, session: Session = Depends(get_session)):
    location = _load_location_or_404(session, location_id)
    breadcrumb = build_location_breadcrumb(session, location)
    return templates.TemplateResponse(
        request,
        "location_child_new.html",
        {
            "page_title": f"Add sub-location for {location.name}",
            "location": location,
            "breadcrumb": breadcrumb,
        },
    )


@router.get("/locations/{location_id}/appearances/new")
def new_location_appearance_page(request: Request, location_id: int, session: Session = Depends(get_session)):
    location = _load_location_or_404(session, location_id)
    breadcrumb = build_location_breadcrumb(session, location)
    videos = list(session.exec(select(Video).order_by(Video.title.asc())))
    return templates.TemplateResponse(
        request,
        "location_appearance_new.html",
        {
            "page_title": f"Attach video to {location.name}",
            "location": location,
            "breadcrumb": breadcrumb,
            "videos": videos,
        },
    )


@router.get("/locations/{location_id}/journeys/new")
def new_location_journey_page(request: Request, location_id: int, session: Session = Depends(get_session)):
    location = _load_location_or_404(session, location_id)
    breadcrumb = build_location_breadcrumb(session, location)
    return templates.TemplateResponse(
        request,
        "location_journey_new.html",
        {
            "page_title": f"Create journey for {location.name}",
            "location": location,
            "breadcrumb": breadcrumb,
        },
    )


@router.post("/locations/{location_id}/children")
def create_child_location(
    location_id: int,
    name: str = Form(...),
    kind: str = Form(default="place"),
    country: str = Form(default=""),
    region: str = Form(default=""),
    latitude: str = Form(default=""),
    longitude: str = Form(default=""),
    notes: str = Form(default=""),
    session: Session = Depends(get_session),
):
    parent = _load_location_or_404(session, location_id)
    child_location = Location(
        name=name.strip(),
        kind=kind.strip() or "place",
        parent_location_id=parent.id,
        country=country.strip() or None,
        region=region.strip() or None,
        latitude=_parse_optional_float(latitude),
        longitude=_parse_optional_float(longitude),
        notes=notes.strip() or None,
    )
    session.add(child_location)
    parent.updated_at = utcnow()
    session.add(parent)
    session.commit()
    return RedirectResponse(url=f"/locations/{parent.id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/locations/{location_id}/appearances")
def create_location_appearance(
    location_id: int,
    video_id: int = Form(...),
    timestamp_seconds: str = Form(default=""),
    order_index: str = Form(default=""),
    note: str = Form(default=""),
    session: Session = Depends(get_session),
):
    location = _load_location_or_404(session, location_id)
    _load_video_or_404(session, video_id)
    appearance = VideoLocationAppearance(
        video_id=video_id,
        location_id=location.id,
        timestamp_seconds=_parse_optional_int(timestamp_seconds),
        order_index=_parse_optional_int(order_index),
        note=note.strip() or None,
    )
    session.add(appearance)
    location.updated_at = utcnow()
    session.add(location)
    session.commit()
    return RedirectResponse(url=f"/locations/{location.id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/locations/{location_id}/journeys")
def create_location_journey(
    location_id: int,
    name: str = Form(...),
    description: str = Form(default=""),
    session: Session = Depends(get_session),
):
    location = _load_location_or_404(session, location_id)
    journey = LocationJourney(
        root_location_id=location.id,
        name=name.strip(),
        description=description.strip() or None,
    )
    session.add(journey)
    session.commit()
    session.refresh(journey)

    first_stop = LocationJourneyStop(
        journey_id=journey.id,
        location_id=location.id,
        order_index=1,
        note="Journey anchor",
    )
    session.add(first_stop)
    location.updated_at = utcnow()
    session.add(location)
    session.commit()

    return RedirectResponse(url=f"/location-journeys/{journey.id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/location-journeys/{journey_id}")
def location_journey_detail(request: Request, journey_id: int, session: Session = Depends(get_session)):
    journey = _load_location_journey_or_404(session, journey_id)
    ordered_stops = sorted(journey.stops, key=lambda stop: stop.order_index)
    selectable_locations = list(
        session.exec(
            select(Location)
            .where(Location.latitude.is_not(None), Location.longitude.is_not(None))
            .order_by(Location.name.asc())
        )
    )
    return templates.TemplateResponse(
        request,
        "location_journey_detail.html",
        {
            "page_title": journey.name,
            "journey": journey,
            "ordered_stops": ordered_stops,
            "selectable_locations": selectable_locations,
        },
    )


@router.post("/location-journeys/{journey_id}/stops")
def create_location_journey_stop(
    journey_id: int,
    location_id: int = Form(...),
    order_index: str = Form(default=""),
    note: str = Form(default=""),
    session: Session = Depends(get_session),
):
    journey = _load_location_journey_or_404(session, journey_id)
    location = _load_location_or_404(session, location_id)
    existing_stops = sorted(journey.stops, key=lambda stop: stop.order_index)
    next_order = (existing_stops[-1].order_index + 1) if existing_stops else 1
    stop = LocationJourneyStop(
        journey_id=journey.id,
        location_id=location.id,
        order_index=_parse_optional_int(order_index) or next_order,
        note=note.strip() or None,
    )
    session.add(stop)
    journey.updated_at = utcnow()
    location.updated_at = utcnow()
    session.add(journey)
    session.add(location)
    session.commit()
    return RedirectResponse(url=f"/location-journeys/{journey.id}", status_code=status.HTTP_303_SEE_OTHER)


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
    journey_statement = (
        select(Journey)
        .options(selectinload(Journey.video), selectinload(Journey.stops))
        .order_by(Journey.created_at.desc())
    )
    location_statement = (
        select(Location)
        .options(
            selectinload(Location.children),
            selectinload(Location.video_appearances).selectinload(VideoLocationAppearance.video),
        )
        .order_by(Location.created_at.desc())
    )
    location_journey_statement = (
        select(LocationJourney)
        .options(
            selectinload(LocationJourney.root_location),
            selectinload(LocationJourney.stops).selectinload(LocationJourneyStop.location),
        )
        .order_by(LocationJourney.created_at.desc())
    )
    payload = build_map_payload(
        session,
        list(session.exec(journey_statement)),
        list(session.exec(location_statement)),
        list(session.exec(location_journey_statement)),
    )
    return templates.TemplateResponse(
        request,
        "map.html",
        {
            "page_title": "Atlas Map",
            "map_payload": payload,
        },
    )