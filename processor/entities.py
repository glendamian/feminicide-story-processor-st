import requests
from typing import Dict

from processor import ENTITY_SERVER_URL


def server_address_set() -> bool:
    return ENTITY_SERVER_URL is not None


def from_content(text: str, language: str) -> Dict:
    target_url = ENTITY_SERVER_URL + 'entities/from-content'
    response = requests.post(target_url, data=dict(text=text, language=language))
    return response.json()


def from_url(url: str, language:str) -> Dict:
    target_url = ENTITY_SERVER_URL + 'entities/from-url'
    response = requests.post(target_url, data=dict(url=url, language=language))
    return response.json()
