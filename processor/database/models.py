from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, BigInteger, Integer, DateTime, Float, Boolean, String
from dateutil.parser import parse
import datetime as dt
import logging

import processor

Base = declarative_base()

logger = logging.getLogger(__name__)


class Story(Base):
    __tablename__ = 'stories'

    id = Column(Integer, primary_key=True)
    stories_id = Column(BigInteger)
    project_id = Column(Integer)
    model_id = Column(Integer)
    model_score = Column(Float)
    model_1_score = Column(Float)
    model_2_score = Column(Float)
    published_date = Column(DateTime)
    queued_date = Column(DateTime)
    processed_date = Column(DateTime)
    posted_date = Column(DateTime)
    above_threshold = Column(Boolean)
    source = Column(String)
    url = Column(String)

    def __repr__(self):
        return '<Story id={}>'.format(self.id)

    @staticmethod
    def from_source(story, source):
        db_story = Story()
        if source == processor.SOURCE_MEDIA_CLOUD:  # backwards compatability
            db_story.stories_id = story['stories_id']
        db_story.url = story['url']
        db_story.source = source
        # carefully parse date, with fallback to today so we at least get something close to right
        use_fallback_date = False
        try:
            if not isinstance(story['publish_date'], dt.datetime):
                db_story.published_date = parse(story['publish_date'])
            elif story['publish_date'] is not None:
                db_story.published_date = story['publish_date']
            else:
                use_fallback_date = True
        except Exception as e:
            use_fallback_date = True
        if use_fallback_date:
            db_story.published_date = dt.datetime.now()
            logger.warning("Used today as publish date for story that didn't have date ({}) on it: {}".format(
                story['publish_date'], db_story['url']))
        return db_story


class ProjectHistory(Base):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    last_processed_id = Column(BigInteger)
    last_publish_date = Column(DateTime)
    last_url = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    def __repr__(self):
        return '<ProjectHistory id={}>'.format(self.id)
