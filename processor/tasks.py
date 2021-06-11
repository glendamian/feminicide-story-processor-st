import os
import json
import requests
from typing import List, Dict
from celery.utils.log import get_task_logger

from processor import path_to_log_dir
from processor.celery import app
import processor.projects as projects

logger = get_task_logger(__name__)


def _add_probability_to_stories(project: Dict, stories: List[Dict]) -> List[Dict]:
    probabilities = projects.classify_stories(project, stories)
    for idx, s in enumerate(stories):
        s['confidence'] = probabilities[idx]
    results = projects.prep_stories_for_posting(project, stories)
    if projects.LOG_LAST_POST_TO_FILE:  # helpful for debugging (the last project post will written to a file)
        with open(os.path.join(path_to_log_dir, '{}-all-stories.json'.format(project['id'])), 'w', encoding='utf-8') as f:
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
        logger.debug('{}: classify {} stories'.format(project['id'], len(stories)))
        results = _add_probability_to_stories(project, stories)
        post_results_worker.delay(project, results)
    except Exception as exc:
        # only failure here is the classifier not loading? probably we should try again... feminicide server holds state
        # and can handle any duplicate results based on stories_id+model_id synthetic unique key
        logger.warn("{}: Failed to label {} stories".format(project['id'], len(stories)))
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
        logger.debug('{}: post {} stories'.format(['id'], len(stories)))
        for s in stories:  # for auditing, keep a log in the container of the results posted to main server
            logger.debug("{} - {} - {}".format(project['id'], s['stories_id'], s['confidence']))
        projects.post_results(project, stories)
    except requests.exceptions.HTTPError as err:
        # on failure requeue to try again
        logger.warn("{}: Failed to post {} results".format(project['id'], len(stories)))
        logger.exception(err)
        raise self.retry(exc=err)
