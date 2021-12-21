import logging
from flask import render_template, jsonify
import json
from typing import Dict

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


@app.route("/projects/<project_id_str>", methods=['GET'])
def a_project(project_id_str):
    project_id = int(project_id_str)
    # pull out the project info
    project = [p for p in load_project_list() if p['id'] == project_id][0]

    # get some stats
    above_over_time = {r['day'].strftime("%Y-%m-%d"): r['stories'] for r in stories_db.stories_by_day(project_id, True)}
    below_over_time = {r['day'].strftime("%Y-%m-%d"): r['stories'] for r in stories_db.stories_by_day(project_id, False)}
    dates = set(above_over_time.keys() | below_over_time.keys())
    stories_by_day_data = []
    for d in dates:  # need to make sure there is a pair of entries for each date
        stories_by_day_data.append(dict(
            date=d,
            type='above',
            count=above_over_time[d] if d in above_over_time else 0
        ))
        stories_by_day_data.append(dict(
            date=d,
            type='below',
            count=below_over_time[d] if d in below_over_time else 0
        ))

    # show some recent story results
    stories_above = stories_db.recent_stories(project_id, True)
    stories_below = stories_db.recent_stories(project_id, False)
    story_ids = list(set([s.stories_id for s in stories_above]) | set([s.stories_id for s in stories_below]))
    mc = get_mc_client()
    stories = mc.storyList("stories_id:({})".format(" ".join([str(s) for s in story_ids])))
    story_lookup = {s['stories_id']: s for s in stories}

    # render it all
    return render_template('project.html',
                           posted_story_count=stories_db.posted_story_count(project_id),
                           unposted_story_count=stories_db.unposted_story_count(project_id),
                           project=project,
                           stories_above=stories_above,
                           stories_below=stories_below,
                           story_lookup=story_lookup,
                           stories_by_day_data=stories_by_day_data)


if __name__ == "__main__":
    app.debug = True
    app.run()
