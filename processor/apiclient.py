import requests
from typing import Dict

from processor import FEMINICIDE_API_URL, FEMINICIDE_API_KEY


def get_projects_list() -> Dict:
    path = FEMINICIDE_API_URL + '/api/story_processor/projects.json'
    return _get_json(path)


def get_language_models_list() -> Dict:
    path = FEMINICIDE_API_URL + '/api/story_processor/language_models.json'
    return _get_json(path)


def _get_json(path: str) -> Dict:
    params = dict(apikey=FEMINICIDE_API_KEY)
    r = requests.get(path, params)
    return r.json()
