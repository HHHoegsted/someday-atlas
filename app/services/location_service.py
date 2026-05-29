from __future__ import annotations

from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

from app.models import Location, VideoLocationAppearance


def collect_descendant_ids(session: Session, root_location_id: int) -> list[int]:
    descendant_ids = [root_location_id]
    frontier = [root_location_id]

    while frontier:
        child_ids = list(
            session.exec(select(Location.id).where(Location.parent_location_id.in_(frontier)))
        )
        frontier = [child_id for child_id in child_ids if child_id not in descendant_ids]
        descendant_ids.extend(frontier)

    return descendant_ids


def build_location_breadcrumb(session: Session, location: Location) -> list[Location]:
    breadcrumb = [location]
    current_parent_id = location.parent_location_id

    while current_parent_id is not None:
        parent = session.get(Location, current_parent_id)
        if parent is None:
            break
        breadcrumb.append(parent)
        current_parent_id = parent.parent_location_id

    return list(reversed(breadcrumb))


def list_subtree_appearances(session: Session, root_location_id: int) -> list[VideoLocationAppearance]:
    subtree_ids = collect_descendant_ids(session, root_location_id)
    statement = (
        select(VideoLocationAppearance)
        .where(VideoLocationAppearance.location_id.in_(subtree_ids))
        .options(
            selectinload(VideoLocationAppearance.video),
            selectinload(VideoLocationAppearance.location),
        )
    )
    appearances = list(session.exec(statement))
    appearances.sort(
        key=lambda appearance: (
            appearance.location.name.lower() if appearance.location else "",
            appearance.video.title.lower() if appearance.video else "",
            appearance.order_index if appearance.order_index is not None else 1_000_000,
            appearance.timestamp_seconds if appearance.timestamp_seconds is not None else 1_000_000,
        )
    )
    return appearances