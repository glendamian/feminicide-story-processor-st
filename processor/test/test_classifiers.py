import pickle
import json
import os

from processor import base_dir

test_fixture_dir = os.path.join(base_dir, "processor", "test", "fixtures")


def test_classify():
    # load usa model
    tfidf_vectorizer = pickle.load(open(os.path.join(test_fixture_dir, 'usa_vectorizer.p'), 'rb'))
    nb_model = pickle.load(open(os.path.join(test_fixture_dir, 'usa_model.p'), 'rb'))
    # load test inputs
    sample_stories = json.load(open(os.path.join(test_fixture_dir, "usa_sample_stories.json")))
    # classify them
    vectorized_data = tfidf_vectorizer.transform(sample_stories)
    predictions = nb_model.predict_proba(vectorized_data)  # an array (one per story) of arrays (false confidence, true confidence)
    feminicide_probs = predictions[:, 1]  # grab just the true confidence for each story
    assert round(feminicide_probs[0], 8) == 0.42901072
    assert round(feminicide_probs[1], 8) == 0.39132685
    assert round(feminicide_probs[2], 8) == 0.39625011


if __name__ == "__main__":
    test_classify()
