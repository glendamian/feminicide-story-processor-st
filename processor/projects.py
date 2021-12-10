import requests
from typing import List, Dict
import os
import sys
import json
import logging
import time

from processor import FEMINICIDE_API_KEY, VERSION, path_to_log_dir
import processor.classifiers as classifiers
import processor.apiclient as apiclient

logger = logging.getLogger(__name__)

_all_projects = None  # acts as a singleton because we only load it once (after we update it from central server)
_all_project_history = None  # acts as a singleton

REALLY_POST = True  # helpful debug flag - set to False and we don't post results to central server TMP
LOG_LAST_POST_TO_FILE = True


def _path_to_config_file() -> str:
    return os.path.join(classifiers.CONFIG_DIR, 'projects.json')


def _path_to_history_file() -> str:
    return os.path.join(classifiers.CONFIG_DIR, 'project-history.json')


def load_project_list(force_reload: bool = False, update_history: bool = True) -> List[Dict]:
    """
    Treats config like a singleton that is lazy-loaded once the first time this is called.
    :param force_reload: Override the default behaviour and load the config from file system again.
    :param update_history: Set to False to override default behaviour, which is to update history of last processed
                           story id to latest from server. Useful for debugging.
    :return: list of configutations for projects to query about
    """
    global _all_projects
    if _all_projects and not force_reload:
        return _all_projects
    try:
        if force_reload:  # grab the latest config file from the main server
            projects_list = apiclient.get_projects_list()
            with open(_path_to_config_file(), 'w') as f:
                json.dump(projects_list, f)
            logger.info("  updated config file from main server")
        # load and return the (perhaps updated) locally cached file
        with open(_path_to_config_file(), "r") as f:
            _all_projects = json.load(f)
        # update the local history file, which tracks the latest processed_stories_id we've run for each project
        if update_history:
            updates = _update_history_from_config(_all_projects, load_history(True))
            for project_id, processed_stories_id in updates.items():
                update_processing_history(project_id, processed_stories_id)
            logger.info("    updated {} processed_stories_ids from server data".format(len(updates)))
        else:
            logger.info("    skipping history update - using whatever is in local history file for last processed id")
        return _all_projects
    except Exception as e:
        # bail completely if we can't load the config file
        logger.error("Can't load config file - dying ungracefully")
        logger.exception(e)
        sys.exit(1)


def _update_history_from_config(project_list: List[Dict], the_history: Dict[str, int]) -> Dict[int, int]:
    """
    In order to avoid holding state within this container, we rely on the central server to relay back
    the latest processed_stories_id for each project. Yes, we track this ourselves in project-history.json,
    but when the container is reset we lose that file. This is a redundancy to avoid reprocessing loads and
    loads of stories
    :param project_list: the list of projects from the main server
    :return: a dict of the
    """
    updates_to_do = {}
    for project in project_list:
        needs_update = False
        previous_value = None
        if ('latest_processed_stories_id' in project) and (project['latest_processed_stories_id'] is not None):
            if str(project['id']) in the_history:
                previous_value = int(the_history[str(project['id'])])
                needs_update = int(project['latest_processed_stories_id']) > int(the_history[str(project['id'])])
            else:
                needs_update = True
        if needs_update:
            logging.debug("Updating processed_stories_id: {} -> {}".format(
                previous_value, project['latest_processed_stories_id']))
            updates_to_do[project['id']] = project['latest_processed_stories_id']
    return updates_to_do


def load_history(force_reload: bool = False) -> Dict[str, int]:
    """
    Treats history like a singleton that is lazy-loaded once the first time this is called.
    :param force_reload: override the default behaviour and load the config from file system again
    :return:
    """
    global _all_project_history
    if _all_project_history and not force_reload:
        return _all_project_history
    try:
        with open(_path_to_history_file(), "r") as f:
            _all_project_history = json.load(f)
        return _all_project_history
    except FileNotFoundError:
        logger.warning("No history file yet - returning empty one")
        return {}


def update_processing_history(project_id: int, processed_stories_id: int):
    """
    Write back updated history file. This tracks the last story we processed for each project. It is a lookup table,
     from project_id to processed_stories_id. This is *not* thread safe, but should work fine for now because
     we will only have one cron-driven job that fetches and queues up stories to be processed by the workers.
    :param project_id: needs to be a string so we can save it in JSON
    :param processed_stories_id:
    :return:
    """
    try:
        with open(_path_to_history_file(), "r") as f:
            data = json.load(f)
    except FileNotFoundError as e:
        logger.warning("No history file, creating a new one")
        data = dict()
    logger.debug("  {}: updating from {} to {}".format(project_id, data.get(str(project_id), None),
                                                       processed_stories_id))
    data[str(project_id)] = processed_stories_id  # JSON dict keys are strings
    try:
        with open(_path_to_history_file(), "w") as f:
            json.dump(data, f)
    except Exception as e:
        # bail completely if we can't load the config file
        logger.error("Couldn't write to history file - dying ungracefully")
        logger.exception(e)
        sys.exit(1)


def post_results(project: Dict, stories: List[Dict]) -> None:
    """
    Send results back to the feminicide server. Raises an exception if this post fails.
    :param project:
    :param stories:
    :return:
    """
    if len(stories) > 0:  # don't bother posting if there are no stories above threshold
        data_to_send = dict(version=VERSION,
                            project=project,  # send back project data too (even though id is in the URL) for redundancy
                            stories=stories,
                            apikey=FEMINICIDE_API_KEY)
        # helpful logging for debugging (the last project post will written to a file)
        if LOG_LAST_POST_TO_FILE:
            with open(os.path.join(path_to_log_dir, '{}-posted-data-{}.json'.format(
                    project['id'], time.strftime("%Y%m%d-%H%M%S"))), 'w', encoding='utf-8') as f:
                json.dump(data_to_send, f, ensure_ascii=False, indent=4)
        # now post to server (if not in debug mode)
        if REALLY_POST:
            response = requests.post(project['update_post_url'], json=data_to_send)
            if not response.ok:
                raise RuntimeError("Tried to post to project {} but got an error code {}".format(
                    project['id'], response.status_code))
    else:
        logger.debug("  no stories to send for project {}".format(project['id']))


def remove_low_confidence_stories(confidence_threshold: float, stories: List[Dict]) -> List[Dict]:
    """
    If the config has specified some threshold for which stories to send over, filter out those below the threshold.
    :param confidence_threshold:
    :param stories:
    :return: only those stories whose score was >= to the threshold
    """
    filtered = [s for s in stories if s['confidence'] >= confidence_threshold]
    logger.debug("    kept {}/{} stories above {}".format(len(filtered), len(stories), confidence_threshold))
    return filtered


def prep_stories_for_posting(project: Dict, stories: List[Dict]) -> List[Dict]:
    """
    Pull out just the info to send to the central feminicide server (we don't want to send it data it shouldn't see, or
    cannot use).
    :param project:
    :param stories:
    :return:
    """
    prepped_stories = []
    for s in stories:
        story = dict(
            # list a bunch of Media Cloud story metadata
            stories_id=s['stories_id'],
            processed_stories_id=s['processed_stories_id'],
            language=s['language'],
            media_id=s['media_id'],
            media_url=s['media_url'],
            media_name=s['media_name'],
            publish_date=s['publish_date'],
            story_tags=s['story_tags'],
            title=s['title'],
            url=s['url'],
            # add in the entities we parsed out via news-entity-server
            entities=s['entities'] if 'entities' in s else None,  # backwards compatible, in case some in queue are old
            # add in the probability from the model
            confidence=s['confidence'],
            # throw in some of the metadata for good measure
            project_id=project['id'],
            language_model_id=project['language_model_id']
        )
        prepped_stories.append(story)
    return prepped_stories


def classify_stories(project: Dict, stories: List[Dict]) -> List[float]:
    """
    Run all the stories passed in through the appropriate classifier, based on the project config
    :param project:
    :param stories:
    :return: an array of confidence probabilities for this being a story about feminicide
    """
    classifier = classifiers.for_project(project)
    return classifier.classify(stories)
