import os
import unittest
import json

from processor import base_dir
import processor.classifiers as classifiers
from processor.test import test_fixture_dir
from processor.test.test_projects import TEST_EN_PROJECT


class TestModelDownload(unittest.TestCase):

    def test_model_download(self):
        classifiers.download_models()


class TestClassifierHelpers(unittest.TestCase):

    def test_classifier_for_project(self):
        p = TEST_EN_PROJECT.copy()
        c = classifiers.for_project(p)
        assert c.model_name() == 'en_usa'
        p['language_model_id'] = 2
        c = classifiers.for_project(p)
        assert c.model_name() == 'es_uruguay'
        p['language_model_id'] = 3
        c = classifiers.for_project(p)
        assert c.model_name() == 'en_aapf'


class TestClassifierResults(unittest.TestCase):

    def test_classify_en(self):
        project = TEST_EN_PROJECT
        classifier = classifiers.for_project(project)
        with open(os.path.join(test_fixture_dir, "usa_sample_stories.json")) as f:
            sample_texts = json.load(f)
        sample_texts = [dict(story_text=t) for t in sample_texts]
        results = classifier.classify(sample_texts)
        assert round(results[0], 5) == 0.36395
        assert round(results[1], 5) == 0.32298
        assert round(results[2], 5) == 0.33297

    def test_classify_en_aapf(self):
        project = TEST_EN_PROJECT.copy()  # important to copy before editing, otherwise subsequent tests get messed up
        project['language_model_id'] = 3
        classifier = classifiers.for_project(project)
        with open(os.path.join(test_fixture_dir, "more_sample_stories.json")) as f:
            sample_texts = json.load(f)
        sample_texts = [dict(story_text=t) for t in sample_texts]
        results = classifier.classify(sample_texts)
        assert round(results[0], 5) == 0.88928
        assert round(results[1], 5) == 0.24030
        assert round(results[2], 5) == 0.23219
        assert round(results[3], 5) == 0.23250
        assert round(results[4], 5) == 0.37232

    def test_classify_es(self):
        project = TEST_EN_PROJECT.copy()  # important to copy before editing, otherwise subsequent tests get messed up
        project['language_model_id'] = 2
        classifier = classifiers.for_project(project)
        with open(os.path.join(test_fixture_dir, "es_sample_stories.json")) as f:
            sample_texts = json.load(f)
        sample_texts = [dict(story_text=t) for t in sample_texts]
        results = classifier.classify(sample_texts)
        assert round(results[0], 5) == 0.83309

    def _classify_one_from(self, index, file):
        with open(os.path.join(test_fixture_dir, file)) as f:
            sample_texts = json.load(f)
        one_story = [sample_texts[index]]
        sample_texts = [dict(story_text=t) for t in one_story]
        results_by_model_id = []
        for model_id in [1, 2, 3]:
            project = TEST_EN_PROJECT.copy()
            project['language_model_id'] = model_id
            classifier = classifiers.for_project(project)
            model_result = classifier.classify(sample_texts)[0]
            results_by_model_id.append(model_result)
        return results_by_model_id

    def test_stories_against_all_classifiers(self):
        results_by_model_id = self._classify_one_from(6, "more_sample_stories.json")
        assert round(results_by_model_id[0], 5) == 0.30392
        assert round(results_by_model_id[1], 5) == 0.44384
        assert round(results_by_model_id[2], 5) == 0.77732

        results_by_model_id = self._classify_one_from(3, "more_sample_stories.json")
        assert round(results_by_model_id[0], 5) == 0.78411
        assert round(results_by_model_id[1], 5) == 0.57012
        assert round(results_by_model_id[2], 5) == 0.23250

        results_by_model_id = self._classify_one_from(4, "more_sample_stories.json")
        assert round(results_by_model_id[0], 5) == 0.70025
        assert round(results_by_model_id[1], 5) == 0.50000
        assert round(results_by_model_id[2], 5) == 0.37232

        results_by_model_id = self._classify_one_from(5, "more_sample_stories.json")
        assert round(results_by_model_id[0], 5) == 0.24967
        assert round(results_by_model_id[1], 5) == 0.34135
        assert round(results_by_model_id[2], 5) == 0.54318


if __name__ == "__main__":
    unittest.main()
