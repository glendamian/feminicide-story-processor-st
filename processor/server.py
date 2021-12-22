import logging
from flask import render_template, jsonify
import json
from typing import Dict, List

from processor import create_flask_app, VERSION, get_mc_client
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


@app.route("/update-config", methods=['POST'])
def update_config():
    config = load_project_list(force_reload=True)
    return jsonify(config)


def _prep_for_graph(counts_1: Dict[str, int], count_2: Dict[str, int], type1: str, type2: str) -> List[Dict]:
    data1 = {r['day'].strftime("%Y-%m-%d"): r['stories'] for r in counts_1}
    data2 = {r['day'].strftime("%Y-%m-%d"): r['stories'] for r in count_2}
    dates = set(data1.keys() | data2.keys())
    stories_by_day_data = []
    for d in dates:  # need to make sure there is a pair of entries for each date
        stories_by_day_data.append(dict(
            date=d,
            type=type1,
            count=data1[d] if d in data1 else 0
        ))
        stories_by_day_data.append(dict(
            date=d,
            type=type2,
            count=data2[d] if d in data2 else 0
        ))
    return stories_by_day_data


@app.route("/projects/<project_id_str>", methods=['GET'])
def a_project(project_id_str):
    project_id = int(project_id_str)
    # pull out the project info
    project = [p for p in load_project_list() if p['id'] == project_id][0]

    # get some stats
    processed_by_day_data = _prep_for_graph(
        stories_db.stories_by_procesed_day(project_id, True, None),
        stories_db.stories_by_procesed_day(project_id, False, None),
        'above threshold', 'below threshold'
    )
    published_by_day_data = _prep_for_graph(
        stories_db.stories_by_published_day(project_id, True),
        stories_db.stories_by_published_day(project_id, False),
        'above threshold', 'below threshold'
    )
    posted_by_day_data = _prep_for_graph(
        stories_db.stories_by_procesed_day(project_id, True, True),
        stories_db.stories_by_procesed_day(project_id, True, False),
        'sent to main server', 'not sent to main server'
    )

    # show some recent story results
    stories_above = stories_db.recent_stories(project_id, True)
    stories_below = stories_db.recent_stories(project_id, False)
    story_ids = list(set([s.stories_id for s in stories_above]) | set([s.stories_id for s in stories_below]))
    mc = get_mc_client()
    stories = mc.storyList("stories_id:({})".format(" ".join([str(s) for s in story_ids])))
    story_lookup = {s['stories_id']: s for s in stories}

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
                           unposted_above_story_count=unposted_above_story_count,
                           above_threshold_pct=above_threshold_pct,
                           posted_above_story_count=posted_above_story_count,
                           below_story_count=below_story_count,
                           project=project,
                           stories_above=stories_above,
                           stories_below=stories_below,
                           story_lookup=story_lookup,
                           processed_by_day_data=processed_by_day_data,
                           published_by_day_data=published_by_day_data,
                           posted_by_day_data=posted_by_day_data)


if __name__ == "__main__":
    app.debug = True
    app.run()
