from __future__ import absolute_import
from celery import Celery
import logging

from processor import BROKER_URL

logger = logging.getLogger(__name__)

app = Celery('feminicide-story-processor', broker=BROKER_URL, include=['processor.tasks'])
