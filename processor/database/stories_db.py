import datetime as dt
from typing import List, Dict

from sqlalchemy import and_, text
from sqlalchemy.orm import sessionmaker

from processor import engine
from processor.database import Story

Session = sessionmaker(bind=engine)


def add_stories(mc_story_list: List, project: Dict) -> None:
    now = dt.datetime.now()
    db_stories_to_insert = []
    for mc_story in mc_story_list:
        db_story = Story.from_mc_story(mc_story)
        db_story.project_id = project['id']
        db_story.model_id = project['language_model_id']
        db_story.queued_date = now
        db_story.above_threshold = False
        db_stories_to_insert.append(db_story)
    # now insert in batch to the database
    session = Session()
    session.add_all(db_stories_to_insert)
    session.commit()


def update_stories_processed_date_score(stories: List, project_id: int) -> None:
    now = dt.datetime.now()
    session = Session()
    db_stories = session.query(Story).filter(
        and_(
            Story.project_id == project_id,
            Story.stories_id.in_(set([s['stories_id'] for s in stories])),
        )
    ).all()
    for db_story in db_stories:
        matching_mc_story = [s for s in stories if
                             (s['stories_id'] == db_story.stories_id) and (project_id == db_story.project_id)]
        mc_story = matching_mc_story[0]
        db_story.model_score = mc_story['model_score']
        db_story.model_1_score = mc_story['model_1_score']
        db_story.model_2_score = mc_story['model_2_score']
        db_story.processed_date = now
    session.commit()


def update_stories_above_threshold(stories: List, project_id:id) -> None:
    session = Session()
    db_stories = session.query(Story).filter(
        and_(
            Story.project_id == project_id,
            Story.stories_id.in_(set([s['stories_id'] for s in stories])),
        )
    ).all()
    for db_story in db_stories:
        db_story.above_threshold = True
    session.commit()


def update_stories_posted_date(stories: List, project_id: int) -> None:
    now = dt.datetime.now()
    session = Session()
    db_stories = session.query(Story).filter(
        and_(
            Story.project_id == project_id,
            Story.stories_id.in_(set([s['stories_id'] for s in stories])),
        )
    ).all()
    for db_story in db_stories:
        db_story.posted_date = now
    session.commit()


def recent_stories(project_id: int, above_threshold: bool, limit: int = 5) -> List[Story]:
    session = Session()
    q = session.query(Story).\
        filter(Story.project_id == project_id). \
        filter(Story.above_threshold == above_threshold). \
        order_by(Story.processed_date.desc()). \
        limit(limit).all()
    stories = [s for s in q]
    return stories


def stories_by_procesed_day(project_id: int, above_threshold: bool, is_posted: bool, limit: int = 20) -> List:
    query = "select processed_date::date as day, count(*) as stories from stories " \
            "where (project_id={}) and (above_threshold is {}) and (processed_date is not Null) ".\
        format(project_id, 'True' if above_threshold else 'False')
    if is_posted is not None:
        query += "and posted_date {} Null ".format("is not" if is_posted else "is")
    query += "group by 1 order by 1 DESC limit {}".format(limit)
    return _run_query(query)


def stories_by_published_day(project_id: int, above_threshold: bool, limit: int = 20) -> List:
    query = "select published_date::date as day, count(*) as stories from stories " \
            "where (project_id={}) and (above_threshold is {}) and (published_date is not Null) " \
            "group by 1 order by 1 DESC limit {}".format(project_id, 'True' if above_threshold else 'False', limit)
    return _run_query(query)


def _run_query(query: str) -> List:
    data = []
    with engine.begin() as connection:
        result = connection.execute(text(query))
        for row in result:
            data.append(row)
    return data


def _run_count_query(query: str) -> int:
    data = _run_query(query)
    return data[0][0]


def unposted_above_story_count(project_id: int) -> int:
    query = "select count(*) from stories where project_id={} and posted_date is Null and above_threshold is True".\
        format(project_id)
    return _run_count_query(query)


def posted_above_story_count(project_id: int) -> int:
    query = "select count(*) from stories where project_id={} and posted_date is not Null and above_threshold is True". \
        format(project_id)
    return _run_count_query(query)


def below_story_count(project_id: int) -> int:
    query = "select count(*) from stories where project_id={} and above_threshold is False".\
        format(project_id)
    return _run_count_query(query)


def unposted_stories(project_id: int):
    query = "select * from stories where project_id={} and posted_date is Null and above_threshold is True".format(project_id)
    """
    session = Session()
    q = session.query(Story). \
        filter(Story.project_id == project_id). \
        filter(Story.above_threshold is True). \
        filter(Story.posted_date is None)
    return q.all()
    """
    return _run_query(query)

