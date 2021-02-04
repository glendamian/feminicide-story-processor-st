import json
import os

from processor import base_dir
import processor.classifiers as classifiers

test_fixture_dir = os.path.join(base_dir, "processor", "test", "fixtures")


def test_classify_en():
    project = dict(language='en')
    classifier = classifiers.for_project(project)
    assert 'tfidf_vectorizer' in classifier
    assert 'nb_model' in classifier
    # load test inputs
    sample_texts = json.load(open(os.path.join(test_fixture_dir, "usa_sample_stories.json")))
    # classify them
    vectorized_data = classifier['tfidf_vectorizer'].transform(sample_texts)
    predictions = classifier['nb_model'].predict_proba(vectorized_data)
    # `predictions` is now an array (one per story) of arrays (false confidence, true confidence)
    feminicide_probs = predictions[:, 1]  # grab just the "true" confidence for each story
    assert round(feminicide_probs[0], 8) == 0.42901072
    assert round(feminicide_probs[1], 8) == 0.39132685
    assert round(feminicide_probs[2], 8) == 0.39625011


if __name__ == "__main__":
    test_classify_en()
