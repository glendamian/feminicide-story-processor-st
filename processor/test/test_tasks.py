import os
import json
import unittest

import processor.tasks as tasks
from processor import get_mc_client
from processor.test import test_fixture_dir
from processor.test.test_projects import TEST_EN_PROJECT


class TestTasks(unittest.TestCase):

    def _classify_story_ids(self, project, story_ids):
        mc = get_mc_client()
        stories_with_text = mc.storyList("stories_id:({})".format(" ".join([str(id) for id in story_ids])),
                                         text=True, rows=100)
        classified_stories = tasks._add_confidence_to_stories(project, stories_with_text)
        assert len(classified_stories) == len(stories_with_text)
        return classified_stories

    def test_add_probability_to_stories(self):
        project = TEST_EN_PROJECT.copy()
        project['language_model_id'] = 3
        # this loads read data from a real request from a log file on the real server
        with open(os.path.join(test_fixture_dir, "aapf_samples.json")) as f:
            sample_stories = json.load(f)
        story_ids = [s['stories_id'] for s in sample_stories]
        classified_stories = self._classify_story_ids(project, story_ids)
        for s in classified_stories:
            assert 'story_text' not in s
        matching_stories = [s for s in classified_stories if s['stories_id'] == 1957814773]
        assert len(matching_stories) == 1
        assert round(matching_stories[0]['confidence'], 5) == 0.37232

    def test_one_story_by_id(self):
        project = TEST_EN_PROJECT.copy()
        project['language_model_id'] = 3
        story_ids = [1962328343]
        classified_stories = self._classify_story_ids(project, story_ids)
        for s in classified_stories:
            assert 'story_text' not in s
        assert round(classified_stories[0]['confidence'], 5) == 0.78392


if __name__ == "__main__":
    unittest.main()
