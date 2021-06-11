import os
import json
import unittest

import processor.projects as projects
from processor.test import test_fixture_dir

TEST_EN_PROJECT = dict(id=0, language='en', language_model_id=1)


class TestProjects(unittest.TestCase):

    def test_update_list(self):
        project_list = projects.load_project_list(True)
        assert len(project_list) > 0
        for p in project_list:
            assert 'id' in p
            assert 'language_model_id' in p

    def test_update_history_from_config(self):
        # 1. empty - nothing to update
        project_list = [{'id': 1}]
        history = {}
        updates_to_run = projects._update_history_from_config(project_list, history)
        assert len(updates_to_run) == 0
        # 2. empty - no data on server yet
        project_list = [{'id': 1, 'last_processed_stories_id': None}]
        history = {}
        updates_to_run = projects._update_history_from_config(project_list, history)
        assert len(updates_to_run) == 0
        # 3. newly deployed container needs updating
        project_list = [{'id': 1, 'last_processed_stories_id': 1234}]
        history = {}
        updates_to_run = projects._update_history_from_config(project_list, history)
        assert len(updates_to_run) == 1
        assert updates_to_run[1] == 1234
        # 4. some updates we have not run on main server yet? maybe stuck in the queue
        project_list = [{'id': 1, 'last_processed_stories_id': 1}]
        history = {'1': 1000}
        updates_to_run = projects._update_history_from_config(project_list, history)
        assert len(updates_to_run) == 0
        # 5. corrupted local file with old info, overwrite with new server info
        project_list = [{'id': 1, 'last_processed_stories_id': 1000}]
        history = {'1': 2}
        updates_to_run = projects._update_history_from_config(project_list, history)
        assert len(updates_to_run) == 1
        assert updates_to_run[1] == 1000

    def test_classify_stories(self):
        # english
        project = TEST_EN_PROJECT
        # load test inputs
        with open(os.path.join(test_fixture_dir, "usa_sample_stories.json")) as f:
            sample_text = json.load(f)
        sample_stories = [dict(story_text=t) for t in sample_text]
        # check results
        feminicide_probs = projects.classify_stories(project, sample_stories)
        assert round(feminicide_probs[0], 5) == 0.36395
        assert round(feminicide_probs[1], 5) == 0.32298
        assert round(feminicide_probs[2], 5) == 0.33297

    def test_remove_low_confidence_stories(self):
        project = TEST_EN_PROJECT.copy()
        project['min_confidence'] = 0.5
        stories = [
            dict(id=0, confidence=0),
            dict(id=1, confidence=0.1),
            dict(id=2, confidence=0.2),
            dict(id=3, confidence=0.3),
            dict(id=4, confidence=0.4),
            dict(id=5, confidence=0.5),
            dict(id=6, confidence=0.6),
            dict(id=7, confidence=0.7),
            dict(id=8, confidence=0.8),
            dict(id=9, confidence=0.9),
            dict(id=10, confidence=1),
        ]
        trimmed_stories = projects._remove_low_confidence_stories(project['min_confidence'], stories)
        assert len(trimmed_stories) < len(stories)
        assert len(trimmed_stories) == 6
        for s in trimmed_stories:
            assert(s['confidence'] >= project['min_confidence'])


if __name__ == "__main__":
    unittest.main()
