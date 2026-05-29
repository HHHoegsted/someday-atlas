from collections.abc import Generator
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine


DATA_DIR = Path("/data")
DATABASE_PATH = DATA_DIR / "atlas.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

connect_args = {"check_same_thread": False}
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)


def create_db_and_tables() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session