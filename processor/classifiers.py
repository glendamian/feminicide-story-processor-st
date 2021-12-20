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
        # Classifier 1 is always defined
        with open(self._path_to_file('1_model'), 'rb') as m: # load model
            self._model_1 = pickle.load(m)
        if self.config['vectorizer_type_1'] == VECTORIZER_TF_IDF: # load vectorizer
            with open(self._path_to_file('1_vectorizer'), 'rb') as v:
                self._vectorizer_1 = pickle.load(v)
        elif self.config['vectorizer_type_1'] == VECTORIZER_EMBEDDINGS:
            try:
                self._vectorizer_1 = hub.load(TFHUB_MODEL_PATH)  # this will cache to a local dir
            except OSError:
                # probably the cached SavedModel doesn't exist anymore
                logger.error("Can't load _vectorizer_1 from {} - did you run /scripts/download-models.sh?".format(
                    TFHUB_MODEL_PATH))
        else:
            raise RuntimeError("Unknown vectorizer 1 type '{}' for project {}".format(self.config['vectorizer_type_1'],
                                                                                    self.project['id']))
        # Classifier 2 could also exist
        if self.config['chained_models']:
            with open(self._path_to_file('2_model'), 'rb') as m: # load model
                self._model_2 = pickle.load(m)
            if self.config['vectorizer_type_2'] == VECTORIZER_TF_IDF: # load vectorizer
                with open(self._path_to_file('2_vectorizer'), 'rb') as v:
                    self._vectorizer_2 = pickle.load(v)
            elif self.config['vectorizer_type_2'] == VECTORIZER_EMBEDDINGS:
                try:
                    self._vectorizer_2 = hub.load(TFHUB_MODEL_PATH)  # this will cache to a local dir
                except OSError:
                    # probably the cached SavedModel doesn't exist anymore
                    logger.error("Can't load _vectorizer_2 from {} - did you run /scripts/download-models.sh?".format(
                        TFHUB_MODEL_PATH))
            else:
                raise RuntimeError("Unknown vectorizer 2 type '{}' for project {}".format(
                    self.config['vectorizer_type_2'], self.project['id']))

    def classify(self, stories: List[Dict]) -> Dict[str, List[float]]:
        story_texts = [s['story_text'] for s in stories]
        # Classifier 1 always exists
        # vectorize first (turn words/sentences into vectors)
        if self.config['vectorizer_type_1'] == VECTORIZER_TF_IDF:
            vectorized_data_1 = self._vectorizer_1.transform(story_texts)
        elif self.config['vectorizer_type_1'] == VECTORIZER_EMBEDDINGS:
            vectorized_data_1 = self._vectorizer_1(story_texts)
        # now run model against vectors (turn vectors into probabilities)
        try:
            predictions_1 = self._model_1.predict_proba(vectorized_data_1)
            true_probs_1 = predictions_1[:, 1]  # grab the list of probabilities that these *are* feminicide stories
        except ValueError as ve:
            logger.exception(ve)
            raise RuntimeError("Model {} failed to run ({}/{})".format(self.config['id'],
                                                                       self.config['model_1'],
                                                                       self.config['vectorizer_type_1']))
        if not self.config['chained_models']:
            return dict(
                model_1_scores=None,
                model_2_scores=None,
                model_scores=true_probs_1
            )
        # Classifier 2 could also exist
        if self.config['vectorizer_type_2'] == VECTORIZER_TF_IDF:
            vectorized_data_2 = self._vectorizer_2.transform(story_texts)
        elif self.config['vectorizer_type_2'] == VECTORIZER_EMBEDDINGS:
            vectorized_data_2 = self._vectorizer_2(story_texts)
        # now run model against vectors (turn vectors into probabilities)
        try:
            predictions_2 = self._model_2.predict_proba(vectorized_data_2)
            true_probs_2 = predictions_2[:, 1]  # grab the list of probabilities that these *are* feminicide stories
        except ValueError as ve:
            logger.exception(ve)
            raise RuntimeError("Model {} failed to run ({}/{})".format(self.config['id'],
                                                                       self.config['model_2'],
                                                                       self.config['vectorizer_type_2']))
        # with chained models we just return the multiplied probs (for now)
        combined_probs = true_probs_1 * true_probs_2
        return dict(
            model_1_scores=true_probs_1,
            model_2_scores=true_probs_2,
            model_scores=combined_probs
        )


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
        for u in m['model_1_files']:
            _download_file(u, MODEL_DIR, m['filename_prefix']+"_1")
        for u in m['model_2_files']:
            _download_file(u, MODEL_DIR, m['filename_prefix']+"_2")


def _download_file(url: str, dest_dir: str, prefix: str):
    """
    This expects the files to either end with "_model.p" or "_vectorizer.p". It renames them here so that
    there is less of a convention that needs to be maintained on the central server.
    :param url:
    :param dest_dir:
    :param prefix:
    :return:
    """
    # https://stackoverflow.com/questions/16694907/download-large-file-in-python-with-requests
    url_parts = urlparse(url)
    local_filename = url_parts.path.split('/')[-1]
    filename_parts = local_filename.split("_")
    extra_safe_filename = prefix + "_" + filename_parts[-1]
    logger.info("    to {}".format(extra_safe_filename))
    with requests.get(url, stream=True) as r:
        with open(os.path.join(dest_dir, extra_safe_filename), 'wb') as f:
            shutil.copyfileobj(r.raw, f)
