import logging

from flask import render_template, jsonify
import json
from typing import Dict, List
from itertools import chain

from processor import create_flask_app, VERSION, PLATFORMS
from processor.projects import load_project_list
import processor.database.stories_db as stories_db

logger = logging.getLogger(__name__)

app = create_flask_app()


# render helper, see https://stackoverflow.com/questions/34646055/encoding-json-inside-flask-template
def as_pretty_json(value: Dict) -> str:
    return json.dumps(value, indent=4, separators=(',', ': '))
app.jinja_env.filters['as_pretty_json'] = as_pretty_json


@app.route("/", methods=['GET'])
def home():
    projects = load_project_list()
    return render_template('home.html', projects=projects, version=VERSION)


@app.route("/posted-platform-history", methods=['GET'])
def posted_platform_history():
    # show overall ingest over last month
    data_for_graph = _prep_for_stacked_graph(
        [stories_db.stories_by_posted_day(platform=p) for p in PLATFORMS],
        PLATFORMS)
    return jsonify(data_for_graph)


@app.route("/processed-platform-history", methods=['GET'])
def processed_platform_history():
    # show overall ingest over last month
    data_for_graph = _prep_for_stacked_graph(
        [stories_db.stories_by_processed_day(platform=p) for p in PLATFORMS],
        PLATFORMS)
    return jsonify(data_for_graph)


@app.route("/processed-result-history", methods=['GET'])
def processed_result_history():
    # show stories above threshold over last month
    data = _prep_for_stacked_graph(
        [stories_db.stories_by_processed_day(above_threshold=True),
         stories_db.stories_by_processed_day(above_threshold=False)],
        ['above threshold', 'below threshold']
    )
    return jsonify(data)


@app.route("/update-config", methods=['POST'])
def update_config():
    config = load_project_list(force_reload=True)
    return jsonify(config)


def _prep_for_stacked_graph(counts: List[List], names: List[str]) -> List[Dict]:
    cleaned_data = [{r['day'].strftime("%Y-%m-%dT00:00:00"): r['stories'] for r in series} for series in counts]
    dates = set(chain(*[series.keys() for series in cleaned_data]))
    stories_by_day_data = []
    for d in dates:  # need to make sure there is a pair of entries for each date
        for idx, series in enumerate(cleaned_data):
            stories_by_day_data.append(dict(
                date=d,
                type=names[idx],
                count=series[d] if d in series else 0
            ))
    return stories_by_day_data


@app.route("/projects/<project_id_str>/processed-by-day", methods=['GET'])
def project_processed_by_day(project_id_str):
    project_id = int(project_id_str)
    data = _prep_for_stacked_graph(
        [stories_db.stories_by_processed_day(project_id, above_threshold=True),
         stories_db.stories_by_processed_day(project_id, above_threshold=False)],
        ['above threshold', 'below threshold']
    )
    return jsonify(data)


@app.route("/projects/<project_id_str>/published-by-day", methods=['GET'])
def project_published_by_day(project_id_str):
    project_id = int(project_id_str)
    data = _prep_for_stacked_graph(
        [stories_db.stories_by_published_day(project_id=project_id, above_threshold=True),
         stories_db.stories_by_published_day(project_id=project_id, above_threshold=False)],
        ['above threshold', 'below threshold']
    )
    return jsonify(data)


@app.route("/projects/<project_id_str>/posted-by-day", methods=['GET'])
def project_posted_by_day(project_id_str):
    project_id = int(project_id_str)
    data = _prep_for_stacked_graph(
        [stories_db.stories_by_processed_day(project_id, above_threshold=True, is_posted=True),
         stories_db.stories_by_processed_day(project_id, above_threshold=True, is_posted=False)],
        ['sent to main server', 'not sent to main server']
    )
    return jsonify(data)


@app.route("/projects/<project_id_str>/binned-model-scores", methods=['GET'])
def project_model_scores(project_id_str):
    project_id = int(project_id_str)
    data = stories_db.project_binned_model_scores(project_id)
    return jsonify(data)


@app.route("/projects/<project_id_str>", methods=['GET'])
def a_project(project_id_str):
    project_id = int(project_id_str)
    # pull out the project info
    project = [p for p in load_project_list(download_if_missing=True) if p['id'] == project_id][0]

    # show overall ingest over last two weeks
    data_for_graph = _prep_for_stacked_graph([stories_db.stories_by_published_day(platform=p, project_id=project_id, limit=30)
                                              for p in PLATFORMS], PLATFORMS)

    # show some recent story results
    stories_above = stories_db.recent_stories(project_id, True)
    stories_below = stories_db.recent_stories(project_id, False)
    story_lookup = {}

    # some other stats
    unposted_above_story_count = stories_db.unposted_above_story_count(project_id)
    posted_above_story_count = stories_db.posted_above_story_count(project_id)
    below_story_count = stories_db.below_story_count(project_id)
    try:
        above_threshold_pct = 100 * (unposted_above_story_count + posted_above_story_count) / below_story_count
    except ZeroDivisionError:
        above_threshold_pct = 100

    # render it all
    return render_template('project.html',
                           ingest_data=data_for_graph,
                           unposted_above_story_count=unposted_above_story_count,
                           above_threshold_pct=above_threshold_pct,
                           posted_above_story_count=posted_above_story_count,
                           below_story_count=below_story_count,
                           project=project,
                           stories_above=stories_above,
                           stories_below=stories_below,
                           story_lookup=story_lookup
                           )


if __name__ == "__main__":
    app.debug = True
    app.run()
