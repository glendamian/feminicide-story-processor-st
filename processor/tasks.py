import os
import json
import requests
from typing import List, Dict
import logging
import time
# from celery.utils.log import get_task_logger

from processor import path_to_log_dir
from processor.celery import app
import processor.projects as projects

logger = logging.getLogger(__name__)  # get_task_logger(__name__)
logFormatter = logging.Formatter("[%(levelname)s %(threadName)s] - %(asctime)s - %(name)s - : %(message)s")
fileHandler = logging.FileHandler(os.path.join(path_to_log_dir, "tasks-{}.log".format(time.strftime("%Y%m%d-%H%M%S"))))
fileHandler.setFormatter(logFormatter)
logger.addHandler(fileHandler)


def _add_confidence_to_stories(project: Dict, stories: List[Dict]) -> List[Dict]:
    probabilities = projects.classify_stories(project, stories)
    for idx, s in enumerate(stories):
        s['confidence'] = probabilities[idx]
    results = projects.prep_stories_for_posting(project, stories)
    if projects.LOG_LAST_POST_TO_FILE:  # helpful for debugging (the last project post will written to a file)
        with open(os.path.join(path_to_log_dir,
                               '{}-all-stories-{}.json'.format(project['id'], time.strftime("%Y%m%d-%H%M%S"))),
                  'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
    return results


@app.task(serializer='json', bind=True)
def classify_stories_worker(self, project: Dict, stories: List[Dict]):
    """
    Take a page of stories matching a project and run them through the classifier for that project.
    :param self:
    :param project:
    :param stories:
    """
    try:
        logger.debug('{}: classify {} stories (model {})'.format(project['id'], len(stories),
                                                                 project['language_model_id']))
        stories_with_confidence = _add_confidence_to_stories(project, stories)
        for s in stories:
            logger.debug("  classify: {} - {} - {}".format(project['id'], s['stories_id'], s['confidence']))
        stories_to_send = projects.remove_low_confidence_stories(project.get('min_confidence', 0),
                                                                 stories_with_confidence)
        logger.debug('{}: {} stories queued to post'.format(project['id'], len(stories_to_send)))
        post_results_worker.delay(project, stories_to_send)
    except Exception as exc:
        # only failure here is the classifier not loading? probably we should try again... feminicide server holds state
        # and can handle any duplicate results based on stories_id+model_id synthetic unique key
        logger.warning("{}: Failed to label {} stories".format(project['id'], len(stories)))
        logger.exception(exc)
        raise self.retry(exc=exc)


@app.task(serializer='json', bind=True)
def post_results_worker(self, project: Dict, stories: List[Dict]):
    """
    Take a set of classified stories and post the results back to the feminicide server
    :param self:
    :param project:
    :param stories:
    """
    try:
        logger.debug('{}: posting {} stories'.format(project['id'], len(stories)))
        # do this again, just in case there is something old in the queues
        stories_to_send = projects.remove_low_confidence_stories(project.get('min_confidence', 0), stories)
        for s in stories_to_send:  # for auditing, keep a log in the container of the results posted to main server
            logger.debug("  post: {} - {} - {}".format(project['id'], s['stories_id'], s['confidence']))
        projects.post_results(project, stories_to_send)
    except requests.exceptions.HTTPError as err:
        # on failure requeue to try again
        logger.warning("{}: Failed to post {} results".format(project['id'], len(stories)))
        logger.exception(err)
        raise self.retry(exc=err)
