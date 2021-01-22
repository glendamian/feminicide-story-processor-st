import os
import logging
import pickle
from typing import Dict

from processor import base_dir

logger = logging.getLogger(__name__)

test_fixture_dir = os.path.join(base_dir, "processor", "test", "fixtures")

files_dir = os.path.join(base_dir, "files")
model_dir = os.path.join(base_dir, "files", "models")

MODELS = {
    'en': dict(tfidf_vectorizer='usa_vectorizer.p', nb_model='usa_model.p'),
    'es': dict(tfidf_vectorizer='uruguay_vectorizer.p', nb_model='uruguay_model.p')
}


def for_project(project: Dict):
    """
    This is where we would download a classifier, as needed, from the main server based on the URL info
    in the project config passed in. For now, just return the static
    """
    if 'language' not in project:
        logger.error('No language specified on {}'.format(project['id']))
    if project['language'] not in MODELS.keys():
        logger.error('Invalid language specified on {}'.format(project['id']))

    return dict(
        tfidf_vectorizer=pickle.load(open(os.path.join(model_dir,
                                                       MODELS[project['language']]['tfidf_vectorizer']), 'rb')),
        nb_model=pickle.load(open(os.path.join(model_dir,MODELS[project['language']]['nb_model']), 'rb'))
    )
