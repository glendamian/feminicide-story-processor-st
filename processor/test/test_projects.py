import os
import json
import unittest

import processor.projects as projects
from processor import base_dir

test_fixture_dir = os.path.join(base_dir, "processor", "test", "fixtures")

TEST_EN_PROJECT = dict(id=0, language='en', language_model_id=1)


class TestProjects(unittest.TestCase):

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


if __name__ == "__main__":
    unittest.main()
