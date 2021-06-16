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

    def test_stories_by_id(self):
        project = TEST_EN_PROJECT.copy()
        project['language_model_id'] = 3
        story_ids = [1962347883, 1962349234, 1962351727, 1962353022, 1962393331, 1962423253, 1962441612, 1962448739, 1962524394, 1962530545, 1962591842, 1962643550, 1962649426, 1962649367, 1962649356, 1962657504, 1962649348, 1962659502, 1962660224, 1962659986, 1962680816, 1962683773, 1962688213, 1962760327, 1962804171, 1962820258, 1962822699, 1962840640, 1962840636, 1962840604, 1962840583, 1962840585, 1962840557, 1962840492, 1962841187, 1962841162, 1962841266, 1962841145, 1962841139, 1962841142, 1962841122, 1962841138, 1962840943, 1962840939, 1962840953, 1962840948, 1962840520, 1962840933, 1962840945, 1962840931, 1962840506, 1962840393, 1962840442, 1962842250, 1962848158, 1962984566, 1962985830, 1963015259, 1963016009, 1963015590, 1963043123]
        classified_stories = self._classify_story_ids(project, story_ids)
        for s in classified_stories:
            assert 'story_text' not in s
            assert s['confidence'] > 0.75
        # assert round(classified_stories[0]['confidence'], 5) == 0.78392


if __name__ == "__main__":
    unittest.main()
