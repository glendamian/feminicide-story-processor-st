from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, BigInteger, Integer, DateTime, Float, Boolean, String
from dateutil.parser import parse

import processor

Base = declarative_base()


class Story(Base):
    __tablename__ = 'stories'

    id = Column(Integer, primary_key=True)
    stories_id = Column(Integer)
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
        s.published_date = parse(story['publish_date'])
        s.url = story['url']
        s.source = source
        return s


class ProjectHistory(Base):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    last_processed_id = Column(BigInteger)
    last_publish_date = Column(DateTime)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    def __repr__(self):
        return '<ProjectHistory id={}>'.format(self.id)
