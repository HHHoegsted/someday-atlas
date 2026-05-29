from collections.abc import Generator
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine


DATA_DIR = Path("/data")
DATABASE_PATH = DATA_DIR / "atlas.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

connect_args = {"check_same_thread": False}
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)


def _ensure_capture_event_location_column() -> None:
    with engine.begin() as connection:
        columns = {
            row[1]
            for row in connection.exec_driver_sql("PRAGMA table_info(captureevent)").fetchall()
        }
        if "location_id" not in columns:
            connection.exec_driver_sql("ALTER TABLE captureevent ADD COLUMN location_id INTEGER")
        if "video_id" not in columns:
            connection.exec_driver_sql("ALTER TABLE captureevent ADD COLUMN video_id INTEGER")
        if "timestamp_seconds" not in columns:
            connection.exec_driver_sql("ALTER TABLE captureevent ADD COLUMN timestamp_seconds INTEGER")


def create_db_and_tables() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SQLModel.metadata.create_all(engine)
    _ensure_capture_event_location_column()


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session