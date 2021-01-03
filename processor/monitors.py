import requests
from typing import List, Dict
import os
import sys
import json
import logging

from processor import base_dir

logger = logging.getLogger(__name__)

config = None  # acts as a singleton
history = None  # acts as a singleton

def _path_to_config_file() -> str:
    return os.path.join(base_dir, 'config', 'monitors.json')


def _path_to_history_file() -> str:
    return os.path.join(base_dir, 'config', 'monitor-history.json')


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
    except Exception as e:
        # bail completely if we can't load the history file
        logger.error("Can't load history file - dying ungracefully")
        logger.exception(e)
        sys.exit(1)


def update_processing_history(monitor_id: str, last_processed_stories_id: str):
    """
    Weite back updated history file. This tracks the last story we processed for each monitor. It is a lookup table,
     from monitor_id to last_processed_stories_id. This is *not* thread safe, but should work fine for now because
     we will only have one cron-driven job that fetches and queues up stories to be processed by the workers.
    :param monitor_id:
    :param last_processed_stories_id:
    :return:
    """
    try:
        with open(_path_to_history_file(), "r") as f:
            data = json.load(f)
    except FileNotFoundError as e:
        logger.warning("No history file, creating a new one")
        data = dict()
    logger.debug("  {}: updating from {} to {}".format(monitor_id, data.get(monitor_id, None),
                                                       last_processed_stories_id))
    data[monitor_id] = last_processed_stories_id
    try:
        with open(_path_to_history_file(), "w") as f:
            json.dump(data, f)
    except Exception as e:
        # bail completely if we can't load the config file
        logger.error("Couldn't write to history file - dying ungracefully")
        logger.exception(e)
        sys.exit(1)


def classify_text(monitor: Dict, story_text: str) -> float:
    """
    Run a story agains the classifier for a monitor.
    :param monitor: config object specifying the monitor
    :param story_text:
    :return: the score returned by the classifier
    """
    # TODO: implement this with the real model
    return 0.5


def post_results(monitor: Dict, stories: List):
    """
    Send results back to the feminicide server. Raises an exception if this post fails.
    :param monitor:
    :param stories:
    :return: whether the request worked or not (if not, raises an exception)
    """
    stories_to_send = _remove_low_confidence_stories(monitor.get('min_confidence', 0), stories)
    response = requests.post(monitor['url'], data=dict(stories=_prep_stories_for_posting(stories_to_send)))
    return response.ok


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
            language=s['language'],
            media_id=s['media_id'],
            media_url=s['media_url'],
            publish_date=s['publish_date'],
            story_tags=s['story_tags'],
            title=s['title'],
            url=s['url'],
            confidence=s['confidence']
        )
        prepped_stories.append(s)
    return prepped_stories
