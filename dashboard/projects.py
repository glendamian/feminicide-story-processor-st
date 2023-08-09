from typing import List, Dict
import os
import sys
import json
import logging

from dashboard import CONFIG_DIR
import dashboard.apiclient as apiclient

logger = logging.getLogger(__name__)

_all_projects = None  # acts as a singleton because we only load it once (after we update it from central server)


def _path_to_config_file() -> str:
    return os.path.join(CONFIG_DIR, 'projects.json')


def load_project_list(force_reload: bool = False, download_if_missing: bool = False) -> List[Dict]:
    """
    Treats config like a singleton that is lazy-loaded once the first time this is called.
    :param force_reload: Override the default behaviour and load the config from file system again.
    :param download_if_missing: If the file is missing try to download it as a backup plan
    :return: list of configurations for projects to query about
    """
    global _all_projects
    if _all_projects and not force_reload:
        return _all_projects
    try:
        file_exists = os.path.exists(_path_to_config_file())
        if force_reload or (download_if_missing and not file_exists):  # grab the latest config file from main server
            projects_list = apiclient.get_projects_list()
            with open(_path_to_config_file(), 'w') as f:
                json.dump(projects_list, f)
                file_exists = True # we might have just created it for the first time
            logger.info("  updated config file from main server - {} projects".format(len(projects_list)))
            if len(projects_list) == 0:
                raise RuntimeError("Fetched empty project list was empty - bailing unhappily")
        # load and return the (perhaps updated) locally cached file
        if file_exists:
            with open(_path_to_config_file(), "r") as f:
                _all_projects = json.load(f)
        else:
            _all_projects = []
        return _all_projects
    except Exception as e:
        # bail completely if we can't load the config file
        logger.error("Can't load config file - dying ungracefully")
        logger.exception(e)
        sys.exit(1)
