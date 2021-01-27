from celery.utils.log import get_task_logger
import logging
from typing import List, Dict
import requests

from processor.celery import app
import processor.projects as projects

logger = get_task_logger(__name__)

# create another logger to track all the story results posted to a file for auditing internally
story_logger = get_task_logger('story_classification_results')
fh = logging.FileHandler('posted-story-data.log')
fh.setLevel(logging.DEBUG)
story_logger.addHandler(fh)


@app.task(serializer='json', bind=True)
def classify_stories_worker(self, project: Dict, stories: List):
    """
    Take a page of stories matching a project and run them through the classifier for that project.
    :param self:
    :param project:
    :param stories:
    """
    try:
        logger.debug('{}: classify {} stories'.format(['id'], len(stories)))
        probabilities = projects.classify_stories(project, stories)
        # TODO
        for idx, s in enumerate(stories):
            s['confidence'] = probabilities[idx]
            del s['story_text']  # don't keep the story text around for longer than we need to
        post_results_worker.delay(project, stories)
    except Exception as exc:
        # only failure here is the classifier not loading? probably we should try again... feminicide server holds state
        # and can handle any duplicate results based on stories_id+model_id synthetic unique key
        logger.warn("{}: Failed to label {} stories".format(project['id'], len(stories)))
        logger.exception(exc)
        raise self.retry(exc=exc)


@app.task(serializer='json', bind=True)
def post_results_worker(self, project: Dict, stories: List):
    """
    Take a set of classified stories and post the results back to the feminicide server
    :param self:
    :param project:
    :param stories:
    """
    try:
        logger.debug('{}: post {} stories'.format(['id'], len(stories)))
        for s in stories:  # for auditing, keep a log in the container of the results posted to main server
            story_logger.debug("{} - {} - {}".format(project['id'], s['stories_id'], s['confidence']))
        projects.post_results(project, stories)
    except requests.exceptions.HTTPError as err:
        # on failure requeue to try again
        logger.warn("{}: Failed to post {} results".format(project['id'], len(stories)))
        logger.exception(err)
        raise self.retry(exc=err)
