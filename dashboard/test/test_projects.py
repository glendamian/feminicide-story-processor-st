import unittest

import processor.projects as projects


class TestProjects(unittest.TestCase):

    def test_update_list(self):
        project_list = projects.load_project_list(True)
        assert len(project_list) > 0
        for p in project_list:
            assert 'id' in p
            assert 'language_model_id' in p
            assert 'rss_url' in p


if __name__ == "__main__":
    unittest.main()
