import unittest

import processor.apiclient as apiclient
from processor.classifiers import MODEL_TYPES, VECTORIZER_TYPES


class TestApiClient(unittest.TestCase):

    def test_get_projects_list(self):
        project_list = apiclient.get_projects_list()
        for p in project_list:
            assert 'search_terms' in p
            assert 'start_date' in p
            assert 'media_collections' in p
            assert 'min_confidence' in p
            assert 'language_model_id' in p
            assert 'last_processed_stories_id' in p
            assert 'update_post_url' in p

    def test_get_language_models_list(self):
        models_list = apiclient.get_language_models_list()
        for p in models_list:
            assert 'id' in p
            if p['model_type_1'] is not None:
                assert p['model_type_1'] in MODEL_TYPES
            if p['model_type_2'] is not None:
                assert p['model_type_2'] in MODEL_TYPES
            if p['vectorizer_type_1'] is not None:
                assert p['vectorizer_type_1'] in VECTORIZER_TYPES
            if p['vectorizer_type_2'] is not None:
                assert p['vectorizer_type_1'] in VECTORIZER_TYPES
            assert p['filename_prefix'] is not None


if __name__ == "__main__":
    unittest.main()
