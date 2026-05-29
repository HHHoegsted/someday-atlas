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
    raw_text: str
    processed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utcnow, nullable=False)