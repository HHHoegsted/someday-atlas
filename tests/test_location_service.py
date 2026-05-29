from sqlmodel import Session, SQLModel, create_engine

from app.models import Location, Video, VideoLocationAppearance
from app.services.location_service import build_location_breadcrumb, collect_descendant_ids, list_subtree_appearances


def build_session() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_collect_descendant_ids_returns_entire_subtree() -> None:
    with build_session() as session:
        root = Location(name="Tokyo", kind="city")
        session.add(root)
        session.commit()
        session.refresh(root)

        district = Location(name="Shibuya", kind="district", parent_location_id=root.id)
        station = Location(name="Tokyo Station", kind="station", parent_location_id=root.id)

        session.add(district)
        session.add(station)
        session.commit()
        session.refresh(district)

        attraction = Location(name="Shibuya Scramble Crossing", kind="attraction", parent_location_id=district.id)
        session.add(attraction)
        session.commit()
        session.refresh(attraction)

        assert set(collect_descendant_ids(session, root.id)) == {root.id, district.id, station.id, attraction.id}


def test_build_location_breadcrumb_includes_parents() -> None:
    with build_session() as session:
        root = Location(name="Tokyo", kind="city")
        session.add(root)
        session.commit()
        session.refresh(root)

        district = Location(name="Shibuya", kind="district", parent_location_id=root.id)
        session.add(district)
        session.commit()
        session.refresh(district)

        attraction = Location(name="Shibuya Scramble Crossing", kind="attraction", parent_location_id=district.id)
        session.add(attraction)
        session.commit()
        session.refresh(attraction)

        breadcrumb = build_location_breadcrumb(session, attraction)
        assert [item.name for item in breadcrumb] == ["Tokyo", "Shibuya", "Shibuya Scramble Crossing"]


def test_list_subtree_appearances_collects_child_location_videos() -> None:
    with build_session() as session:
        root = Location(name="Cozumel", kind="place")
        session.add(root)
        session.commit()
        session.refresh(root)

        beach = Location(name="Mr. Sancho's", kind="attraction", parent_location_id=root.id)
        session.add(beach)
        session.commit()
        session.refresh(beach)

        video = Video(youtube_url="https://youtu.be/example", youtube_id="example", title="Cozumel port day")
        session.add(video)
        session.commit()
        session.refresh(video)

        appearance = VideoLocationAppearance(
            video_id=video.id,
            location_id=beach.id,
            timestamp_seconds=305,
            note="Beach club arrival",
        )
        session.add(appearance)
        session.commit()

        subtree_appearances = list_subtree_appearances(session, root.id)
        assert len(subtree_appearances) == 1
        assert subtree_appearances[0].location.name == "Mr. Sancho's"
        assert subtree_appearances[0].video.title == "Cozumel port day"