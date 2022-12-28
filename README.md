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
