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
        s = Story()
        if source == processor.SOURCE_MEDIA_CLOUD:
            s.stories_id = story['stories_id']
        if not isinstance(story['publish_date'], dt.datetime):
            s.published_date = parse(story['publish_date'])
        elif story['publish_date'] is not None:
            s.published_date = story['publish_date']
        else:  # if it is None then default to now, so we get some date
            s.published_date = dt.datetime.now()
            logger.warning("Used today as publish date for story that didn't have date on it: {}".format(s['url']))
        s.url = story['url']
        s.source = source
        return s


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
