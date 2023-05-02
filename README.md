Feminicide Story Processor
==========================

Grab stories from Media Cloud or Google Alerts, run them against "feminicide story" classifiers, post results to a 
central server.

Install for Development
-----------------------

For development, install via standard Python approaches: `pip install -r requirements.txt`.
You'll need to setup an instance of rabbitmq to connect to (on MacOS do `brew install rabbitmq`).
Then `cp .env.template .env` and fill in the appropriate info for each setting in that file.
Create a database called "mc-story-processor" in Postgres, then run `alembic upgrade head`.

Note that we use tensorflow_text, which is hard to install on MacOS. If you are on MacOS, you'll need to download and 
install the appropriate [`tensorflow_text-2.10.0-cp310-cp310-macosx_11_0_arm64.whl`](https://github.com/sun1638650145/Libraries-and-Extensions-for-TensorFlow-for-Apple-Silicon/releases/download/v2.10/tensorflow_text-2.10.0-cp310-cp310-macosx_11_0_arm64.whl)
from the helpful repo of [prebuilt tensorflow wheels for Apple Silicon](https://github.com/sun1638650145/Libraries-and-Extensions-for-TensorFlow-for-Apple-Silicon/releases/). 

Running
-------

To fill up the queue with new stories based on the monitor config, execute `run-fetch-PROVIDER.sh`.

To start the workers that process queued up jobs to classify and post story results, execute `run-workers.sh`.

To run the small admin web server, execute `run-server.sh`.

### Tips

* To empty out your local queue while developing, visit `http://localhost:15672/` the and click "delete/purge"
on the Queues tab.

Testing
-------

Just run `pytest` on the command line to run all the automated tests.

Deploying
---------

When you make a change, edit `processor.VERSION` and update the `CHANGELOG.md` file with a note about what changed.

This is built to deploy via a SAAS platform, like Heroku. We deploy via [dokku](https://dokku.com). Whatever your deploy
platform, make sure to create environment variables there for each setting in the `.env.template`.

See `doc/deploying.md` for full info on deploying to dokku.
