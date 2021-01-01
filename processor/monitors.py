import requests
from typing import List, Dict
import os
import sys
import json
import logging

from processor import base_dir
from processor.exceptions import UnknownMonitorException

logger = logging.getLogger(__name__)

config = None  # acts as a singleton


def _path_to_config_file() -> str:
    return os.path.join(base_dir, 'config', 'monitors.json')


def load_config(force_reload=False):
    """
    Treats config like a singleton that is lazy-loaded once the first time this is called.
    :param force_reload: override the default behaviour and load the config from file system again
    :return:
    """
    if config and not force_reload:
        return config
    try:
        with open(_path_to_config_file()) as f:
            data = json.load(f)
            return data
    except Exception as e:
        # bail completely if we can't load the config file
        logger.error("Can't load config file - dying ungracefully")
        logger.exception(e)
        sys.exit(1)


def write_config(monitors: list):
    try:
        with open(_path_to_config_file()) as f:
            json.dump(monitors, f)
    except Exception as e:
        # bail completely if we can't load the config file
        logger.error("Couldn't write to config file - dying ungracefully")
        logger.exception(e)
        sys.exit(1)


def classifier(monitor: Dict):
    # return the classifier for the monitor specified
    return None


def post_results(monitor_url: str, stories: List):
    """
    Send results back to the feminicide server. Raises an exception if this post fails.
    :param monitor:
    :param stories:
    :return: whether the request worked or not (if not, raises an exception)
    """
    response = requests.post(monitor_url, data=dict(stories=stories))
    response.raise_for_status()
    return response.ok
