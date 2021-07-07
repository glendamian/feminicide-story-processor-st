import os
import logging
import pickle
from typing import Dict, List
import tensorflow_hub as hub
import requests
import shutil
from urllib.parse import urlparse

from processor import base_dir
import processor.apiclient as apiclient

logger = logging.getLogger(__name__)

test_fixture_dir = os.path.join(base_dir, "processor", "test", "fixtures")

FILES_DIR = os.path.join(base_dir, "files")
MODEL_DIR = os.path.join(base_dir, "files", "models")

# constants that tell us what type of model to load and run (keep in sync with the main server)
MODEL_LINEAR_REGRESSION = 'lr'
MODEL_NAIVE_BAYES = 'nb'
VECTORIZER_TF_IDF = 'tfidf'
VECTORIZER_EMBEDDINGS = 'embeddings'

DEFAULT_MODEL_NAME = 'usa'

TFHUB_MODEL_PATH = '/tmp/models/'

MODELS = {
    # English default
    'usa': dict(language_model_id=1, name='usa',
                model_type=MODEL_NAIVE_BAYES, vectorizer_type=VECTORIZER_TF_IDF,
                vectorizer='usa_vectorizer.p', model='usa_model.p'),
    # Spanish default
    'uruguay': dict(language_model_id=2, name='uruguay',
                    model_type=MODEL_NAIVE_BAYES, vectorizer_type=VECTORIZER_TF_IDF,
                    vectorizer='uruguay_vectorizer.p', model='uruguay_model.p'),
    # black women killed by police
    'aapf': dict(language_model_id=3, name='aapf',
                 model_type=MODEL_LINEAR_REGRESSION, vectorizer_type=VECTORIZER_TF_IDF,
                 vectorizer='aapf_vectorizer.p', model='aapf_model.p'),
    # indigenous feminicides
    'sbi': dict(language_model_id=3, name='sbi',
                model_type=MODEL_LINEAR_REGRESSION, vectorizer_type=VECTORIZER_TF_IDF,
                vectorizer='sbi_vectorizer.p', model='sbi_model.p')

}


class Classifier:

    def __init__(self, model_config: Dict, project: Dict):
        self.config = model_config
        self.project = project
        self._init()

    def model_name(self) -> str:
        return self.config['name']

    def _path_to_file(self, filename: str) -> str:
        return os.path.join(MODEL_DIR, filename)

    def _init(self):
        # load model
        with open(self._path_to_file(self.config['model']), 'rb') as m:
            self._model = pickle.load(m)
        # load vectorizer
        if self.config['vectorizer_type'] == VECTORIZER_TF_IDF:
            with open(self._path_to_file(self.config['vectorizer']), 'rb') as v:
                self.vectorizer = pickle.load(v)
        elif self.config['vectorizer_type'] == VECTORIZER_EMBEDDINGS:
            try:
                self.model = hub.load(self._path_to_file(TFHUB_MODEL_PATH))  # this will cache to a local dir
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
    try:
        matching_models = [m for k, m in MODELS.items()
                           if int(m['language_model_id']) == int(project['language_model_id'])]
        model_config = matching_models[0]
        logger.debug("Project {} - model {}".format(project['id'], model_config['language_model_id']))
    except:
        logger.warning("Can't find model for project {}, language_model_id {} (defaulting to {})".format(
            project['id'], project['language_model_id'], DEFAULT_MODEL_NAME
        ))
        model_config = MODELS[DEFAULT_MODEL_NAME]
    return Classifier(model_config, project)


def download_models():
    """
    Models are stored centrally on the server. We need to retrieve and store them here.
    :return:
    """
    model_list = apiclient.get_language_models_list()
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
