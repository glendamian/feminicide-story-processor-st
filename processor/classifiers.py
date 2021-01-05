import os
import logging
import pickle
from typing import Dict
import zipfile

from processor import base_dir

logger = logging.getLogger(__name__)

test_fixture_dir = os.path.join(base_dir, "processor", "test", "fixtures")

files_dir = os.path.join(base_dir, "files")
model_dir = os.path.join(base_dir, "files", "models")


def _already_downloaded(monitor: Dict):
    """
    Check to see if we have the classifer files already downloaded
    :param monitor:
    :return:
    """
    return False  # for now just assume we don't have them


def _download(monitor: Dict) -> bool:
    """

    :param monitor:
    :return: success or failure
    """
    test_model_zip = os.path.join(test_fixture_dir, "models.zip")
    with zipfile.ZipFile(test_model_zip, 'r') as zip_ref:
        zip_ref.extractall(files_dir)
    return True


def for_monitor(monitor: Dict):
    """
    This is where we would download a classifier, as needed, from the main server based on the URL info
    in the monitor config passed in. For now, just return the static
    """
    if not _already_downloaded(monitor):
        _download(monitor)
    return dict(
        tfidf_vectorizer=pickle.load(open(os.path.join(model_dir, 'usa_vectorizer.p'), 'rb')),
        nb_model=pickle.load(open(os.path.join(model_dir, 'usa_model.p'), 'rb'))
    )
