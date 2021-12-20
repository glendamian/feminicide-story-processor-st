from sqlalchemy.orm import sessionmaker
import datetime as dt

from processor import engine
from processor.database.models import ProjectHistory

Session = sessionmaker(bind=engine)


def add_history(project_id: int, last_processed_stories_id: int) -> None:
    p = ProjectHistory()
    p.id = project_id
    p.last_processed_id = last_processed_stories_id if last_processed_stories_id is not None else 0
    now = dt.datetime.now()
    p.created_at = now
    p.updated_at = now
    session = Session()
    session.add(p)
    session.commit()


def update_history(project_id: int, last_processed_stories_id: int) -> None:
    session = Session()
    project_history = session.query(ProjectHistory).get(project_id)
    project_history.last_processed_id = last_processed_stories_id
    project_history.updated_at = dt.datetime.now()
    session.commit()


def get_history(project_id: int) -> ProjectHistory:
    session = Session()
    project_history = session.get(ProjectHistory, project_id)
    session.close()
    return project_history
