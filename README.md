Feminicide Media Cloud Story Processor
======================================

Grab stories from Media Cloud, run them against "feminicide story" classifiers, post results to feminicide server.

Install for Development
-----------------------

For development, install via standard Python approaches: `pip install -r requirements.txt`.
You'll need to setup an instance of redis to connect to (on MacOS do `brew install redis`).
Then `cp .env.template .env` and fill in the appropriate info for each setting in that file.

Running
-------

To fill up the queue with new stories based on the monitor config, execute `run-fetch.sh`.

To start the workers that process queued up jobs to classify and post story results, execute `run-workers.sh`.

To run the small admin web server, execute `run-server.sh`.

### Tips

* To empty out your local queue while developing, `redis-cli FLUSHALL`.

Testing
-------

Just run `pytest` on the command line to run all the automated tests.

Deploying
---------

This is built to depoy via a SAAS platform, like Heroku. We deploy via dokku. Make sure to create an environment
variable there for each setting in the `.env`.

It is also super useful to deploy an instance of [celery-flower](https://flower.readthedocs.io/en/latest/) so you can
monitor the production queues.

See `doc/deploying.md` for more info.
