import logging
from flask import render_template, jsonify

from processor import create_flask_app
from processor.projects import load_config

logger = logging.getLogger(__name__)

app = create_flask_app()


@app.route("/", methods=['GET'])
def home():
    config = load_config()
    return render_template('home.html', config=config)


@app.route("/update-config", methods=['POST'])
def update_config():
    config = load_config(force_reload=True)
    return jsonify(config)


if __name__ == "__main__":
    app.debug = True
    app.run()
