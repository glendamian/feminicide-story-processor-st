import requests
from typing import List, Dict
import os
import sys
import json
import logging

from processor import base_dir, CONFIG_FILE_URL
import processor.classifiers as classifiers

logger = logging.getLogger(__name__)

config = None  # acts as a singleton
history = None  # acts as a singleton

REALLY_POST = True


def _path_to_config_file() -> str:
    return os.path.join(base_dir, 'config', 'projects.json')


def _path_to_history_file() -> str:
    return os.path.join(base_dir, 'config', 'project-history.json')


def load_config(force_reload=False):
    """
    Treats config like a singleton that is lazy-loaded once the first time this is called.
    :param force_reload: override the default behaviour and load the config from file system again
    :return:
    """
    global config
    if config and not force_reload:
        return config
    try:
        if force_reload:  # grab the latest config file from the main server
            r = requests.get(CONFIG_FILE_URL)
            open(_path_to_config_file(), 'wb').write(r.content)
            logger.info("  updated config file from main server")
        # load and return the (perhaps updated) locally cached file
        with open(_path_to_config_file(), "r") as f:
            config = json.load(f)
        return config
    except Exception as e:
        # bail completely if we can't load the config file
        logger.error("Can't load config file - dying ungracefully")
        logger.exception(e)
        sys.exit(1)


def load_history(force_reload=False):
    """
    Treats history like a singleton that is lazy-loaded once the first time this is called.
    :param force_reload: override the default behaviour and load the config from file system again
    :return:
    """
    global history
    if history and not force_reload:
        return history
    try:
        with open(_path_to_history_file(), "r") as f:
            history = json.load(f)
        return history
    except FileNotFoundError as e:
        logger.warning("No history file yet - returning empty one")
        return {}


def update_processing_history(project_id: int, last_processed_stories_id: int):
    """
    Write back updated history file. This tracks the last story we processed for each project. It is a lookup table,
     from project_id to last_processed_stories_id. This is *not* thread safe, but should work fine for now because
     we will only have one cron-driven job that fetches and queues up stories to be processed by the workers.
    :param project_id: needs to be a string so we can save it in JSON
    :param last_processed_stories_id:
    :return:
    """
    try:
        with open(_path_to_history_file(), "r") as f:
            data = json.load(f)
    except FileNotFoundError as e:
        logger.warning("No history file, creating a new one")
        data = dict()
    logger.debug("  {}: updating from {} to {}".format(project_id, data.get(str(project_id), None),
                                                       last_processed_stories_id))
    data[str(project_id)] = last_processed_stories_id  # JSON dict keys are strings
    try:
        with open(_path_to_history_file(), "w") as f:
            json.dump(data, f)
    except Exception as e:
        # bail completely if we can't load the config file
        logger.error("Couldn't write to history file - dying ungracefully")
        logger.exception(e)
        sys.exit(1)


def post_results(project: Dict, stories: List):
    """
    Send results back to the feminicide server. Raises an exception if this post fails.
    :param project:
    :param stories:
    :return: whether the request worked or not (if not, raises an exception)
    """
    stories_to_send = _remove_low_confidence_stories(project.get('min_confidence', 0), stories)
    data_to_send = dict(project=project,  # send back project data too (even though id is in the URL) for redundancy
                        stories=_prep_stories_for_posting(stories_to_send))
    if REALLY_POST:
        response = requests.post(project['update_post_url'], json=data_to_send)
        return response.ok
    else:
        # helpful for debugging
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(data_to_send, f, ensure_ascii=False, indent=4)
        return True


def _remove_low_confidence_stories(confidence_threshold: float, stories: List) -> List:
    """
    If the config has specified some threshold for which stories to send over, filter out those below the threshold.
    :param confidence_threshold:
    :param stories:
    :return: only those stories whose score was >= to the threshold
    """
    filtered = [s for s in stories if s['confidence'] >= confidence_threshold]
    logger.debug("    kept {}/{} stories above {}".format(len(filtered), len(stories), confidence_threshold))
    return filtered


def _prep_stories_for_posting(stories: List) -> List:
    """
    Pull out just the info to send to the central feminicide server (we don't want to send it data it shouldn't see, or
    cannot use).
    :param stories:
    :return:
    """
    prepped_stories = []
    for s in stories:
        story = dict(
            stories_id=s['stories_id'],
            processed_stories_id=s['processed_stories_id'],
            language=s['language'],
            media_id=s['media_id'],
            media_url=s['media_url'],
            publish_date=s['publish_date'],
            story_tags=s['story_tags'],
            title=s['title'],
            url=s['url'],
            confidence=s['confidence']
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
    story_texts = [s['story_text'] for s in stories]
    vectorized_data = classifier['tfidf_vectorizer'].transform(story_texts)
    predictions = classifier['nb_model'].predict_proba(vectorized_data)
    true_probs = predictions[:, 1]
    return true_probs
