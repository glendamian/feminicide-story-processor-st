import os
import logging
import pickle
from typing import Dict, List
import tensorflow_hub as hub
import requests
import json
import shutil
from urllib.parse import urlparse

from processor import base_dir
import processor.apiclient as apiclient

logger = logging.getLogger(__name__)

test_fixture_dir = os.path.join(base_dir, "processor", "test", "fixtures")

FILES_DIR = os.path.join(base_dir, "files")
MODEL_DIR = os.path.join(base_dir, "files", "models")
CONFIG_DIR = os.path.join(base_dir, "config")

# constants that tell us what type of model to load and run (keep in sync with the main server)
MODEL_LINEAR_REGRESSION = 'lr'
MODEL_NAIVE_BAYES = 'nb'
MODEL_TYPES = [MODEL_LINEAR_REGRESSION, MODEL_NAIVE_BAYES]
VECTORIZER_TF_IDF = 'tfidf'
VECTORIZER_EMBEDDINGS = 'embeddings'
VECTORIZER_TYPES = [VECTORIZER_TF_IDF, VECTORIZER_EMBEDDINGS]

DEFAULT_MODEL_NAME = 'usa'

TFHUB_MODEL_PATH = '/tmp/models/'


class Classifier:

    def __init__(self, model_config: Dict, project: Dict):
        self.config = model_config
        self.project = project
        self._init()

    def model_name(self) -> str:
        return self.config['filename_prefix']

    def _path_to_file(self, filename: str) -> str:
        return os.path.join(MODEL_DIR, self.config['filename_prefix'] + '_' + filename + '.p')

    def _init(self):
        # load model
        with open(self._path_to_file('model'), 'rb') as m:
            self._model = pickle.load(m)
        # load vectorizer
        if self.config['vectorizer_type'] == VECTORIZER_TF_IDF:
            with open(self._path_to_file('vectorizer'), 'rb') as v:
                self.vectorizer = pickle.load(v)
        elif self.config['vectorizer_type'] == VECTORIZER_EMBEDDINGS:
            try:
                self.model = hub.load(TFHUB_MODEL_PATH)  # this will cache to a local dir
            except OSError:
                # probably the cached SavedModel doesn't exist anymore
                logger.error("Can't load model from {}".format(self.config['tfhub_model_path']))
        else:
            raise RuntimeError("Unknown vectorizer type '{}' for project {}".format(self.config['vectorizer_type'],
                                                                                    self.project['id']))

    def classify(self, stories: List[Dict]) -> List[float]:
        story_texts = [s['story_text'] for s in stories]
        # vectorize first (turn words/sentences into vectors)
        if self.config['vectorizer_type'] == VECTORIZER_TF_IDF:
            vectorized_data = self.vectorizer.transform(story_texts)
        elif self.config['vectorizer_type'] == VECTORIZER_EMBEDDINGS:
            embed = hub.load(TFHUB_MODEL_PATH)
            vectorized_data = embed(story_texts)
        # now run model against vectors (turn vectors into probabilities)
        predictions = self._model.predict_proba(vectorized_data)
        true_probs = predictions[:, 1]  # grab the list of probabilities that these *are* feminicide stories
        return true_probs


def for_project(project: Dict) -> Classifier:
    """
    This is a factory method to return a model for the project based on the `language_model_id`
    """
    model_list = get_model_list()
    try:
        matching_models = [m for m in model_list if int(m['id']) == int(project['language_model_id'])]
        model_config = matching_models[0]
        logger.debug("Project {} - model {}".format(project['id'], model_config['id']))
    except:
        logger.warning("Can't find model for project {}, language_model_id {}".format(
            project['id'], project['language_model_id']
        ))
        raise RuntimeError()
    return Classifier(model_config, project)


def get_model_list() -> List[Dict]:
    with open(os.path.join(CONFIG_DIR, 'language-models.json'), 'r') as f:
        return json.load(f)


def update_model_list():
    """
    The list of models is on the central server.
    """
    model_list = apiclient.get_language_models_list()
    with open(os.path.join(CONFIG_DIR, 'language-models.json'), 'w') as f:
        json.dump(model_list, f)
    return model_list


def download_models():
    """
    Models are stored centrally on the server. We need to retrieve and store them here.
    """
    model_list = update_model_list()
    logger.info("Downloading models:")
    for m in model_list:
        logger.info("  {} - {}".format(m['id'], m['name']))
        for u in m['model_files']:
            _download_file(u, MODEL_DIR)


def _download_file(url: str, dest_dir: str):
    # https://stackoverflow.com/questions/16694907/download-large-file-in-python-with-requests
    url_parts = urlparse(url)
    local_filename = url_parts.path.split('/')[-1]
    with requests.get(url, stream=True) as r:
        with open(os.path.join(dest_dir, local_filename), 'wb') as f:
            shutil.copyfileobj(r.raw, f)
