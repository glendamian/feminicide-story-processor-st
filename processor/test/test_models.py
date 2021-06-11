import os
import unittest
import tensorflow_hub as hub
import pickle
import json

from processor import base_dir
from processor.test import test_fixture_dir

model_dir = os.path.join(base_dir, "files", "models")


class TestModels(unittest.TestCase):
    """
    Lower level model loading tests for debugging and implementation help
    """

    def test_tf_hub_model(self):
        with open(os.path.join(test_fixture_dir, "more_sample_stories.json")) as f:
            sample_texts = json.load(f)
        model_path = "/tmp/models"
        embed = hub.load(model_path)
        vectorized_data = embed(sample_texts)
        with open(os.path.join(model_dir, 'usa_model_aapf.p'), 'rb') as m:
            lr_model = pickle.load(m)

        predictions = lr_model.predict_proba(vectorized_data)
        feminicide_probs = predictions[:, 1]

        assert round(feminicide_probs[0], 5) == 0.88928
        assert round(feminicide_probs[1], 5) == 0.24030
        assert round(feminicide_probs[2], 5) == 0.23219

    def test_nb_model(self):
        with open(os.path.join(model_dir, 'usa_vectorizer.p'), 'rb') as v:
            tfidf_vectorizer = pickle.load(v)
        with open(os.path.join(model_dir, 'usa_model.p'), 'rb') as m:
            nb_model = pickle.load(m)

        with open(os.path.join(test_fixture_dir, "more_sample_stories.json")) as f:
            sample_texts = json.load(f)
        vectorized_data = tfidf_vectorizer.transform(sample_texts)
        predictions = nb_model.predict_proba(vectorized_data)
        feminicide_probs = predictions[:, 1]
        assert round(feminicide_probs[0], 5) == 0.32256
        assert round(feminicide_probs[1], 5) == 0.13036
        assert round(feminicide_probs[2], 5) == 0.71464

        with open(os.path.join(test_fixture_dir, "usa_sample_stories.json")) as f:
            sample_texts = json.load(f)
        vectorized_data = tfidf_vectorizer.transform(sample_texts)
        predictions = nb_model.predict_proba(vectorized_data)
        feminicide_probs = predictions[:, 1]
        assert round(feminicide_probs[0], 5) == 0.36395
        assert round(feminicide_probs[1], 5) == 0.32298
        assert round(feminicide_probs[2], 5) == 0.33297


if __name__ == "__main__":
    unittest.main()
