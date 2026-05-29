from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Video(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    youtube_url: str
    youtube_id: Optional[str] = None
    title: str
    channel_name: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=utcnow, nullable=False)

    journey: Optional["Journey"] = Relationship(back_populates="video")
    location_appearances: list["VideoLocationAppearance"] = Relationship(back_populates="video")
    capture_events: list["CaptureEvent"] = Relationship(back_populates="video")


class Journey(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    video_id: int = Field(foreign_key="video.id", unique=True, nullable=False)
    name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=utcnow, nullable=False)

    video: Video = Relationship(back_populates="journey")
    stops: list["Stop"] = Relationship(back_populates="journey")


class Stop(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    journey_id: int = Field(foreign_key="journey.id", nullable=False)
    place_name: str
    country: Optional[str] = None
    region: Optional[str] = None
    latitude: float
    longitude: float
    order_index: int
    timestamp_seconds: Optional[int] = None
    note: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=utcnow, nullable=False)

    journey: Journey = Relationship(back_populates="stops")


class CaptureEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_by: Optional[str] = None
    kind: str = Field(default="note", nullable=False)
    location_id: Optional[int] = Field(default=None, foreign_key="location.id")
    video_id: Optional[int] = Field(default=None, foreign_key="video.id")
    timestamp_seconds: Optional[int] = None
    raw_text: str
    processed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utcnow, nullable=False)

    location: Optional["Location"] = Relationship(back_populates="capture_events")
    video: Optional["Video"] = Relationship(back_populates="capture_events")


class Location(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    kind: str = Field(default="place", nullable=False)
    parent_location_id: Optional[int] = Field(default=None, foreign_key="location.id")
    country: Optional[str] = None
    region: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=utcnow, nullable=False)

    parent: Optional["Location"] = Relationship(
        back_populates="children",
        sa_relationship_kwargs={"remote_side": "Location.id"},
    )
    children: list["Location"] = Relationship(back_populates="parent")
    video_appearances: list["VideoLocationAppearance"] = Relationship(back_populates="location")
    capture_events: list["CaptureEvent"] = Relationship(back_populates="location")
    root_journeys: list["LocationJourney"] = Relationship(back_populates="root_location")
    journey_stops: list["LocationJourneyStop"] = Relationship(back_populates="location")


class VideoLocationAppearance(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    video_id: int = Field(foreign_key="video.id", nullable=False)
    location_id: int = Field(foreign_key="location.id", nullable=False)
    timestamp_seconds: Optional[int] = None
    order_index: Optional[int] = None
    note: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=utcnow, nullable=False)

    video: Video = Relationship(back_populates="location_appearances")
    location: Location = Relationship(back_populates="video_appearances")


class LocationJourney(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    root_location_id: int = Field(foreign_key="location.id", nullable=False)
    name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=utcnow, nullable=False)

    root_location: Location = Relationship(back_populates="root_journeys")
    stops: list["LocationJourneyStop"] = Relationship(back_populates="journey")


class LocationJourneyStop(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    journey_id: int = Field(foreign_key="locationjourney.id", nullable=False)
    location_id: int = Field(foreign_key="location.id", nullable=False)
    order_index: int
    note: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=utcnow, nullable=False)

    journey: LocationJourney = Relationship(back_populates="stops")
    location: Location = Relationship(back_populates="journey_stops")