Deploying
=========

This is built to deploy via [dokku](http://dokku.viewdocs.io/dokku/). This takes a few rounds of configuration to set up
correctly. There are a few components:
* The fetcher app - ingest stories from Media Cloud and queues them up processing
* The loggin DB - to help us interrogate and debug, we keep track of stories as they move through the pipeline in a DB
* The worker queue - this holds batches of stories needing classification & posting to the central server
* The queue monitor - lets us keep an eye on queue servicing speeds

Create the Dokku apps
---------------------

1. [install Dokku](http://dokku.viewdocs.io/dokku/getting-started/installation/)
2. install the [Dokku rabbitmq plugin](https://github.com/dokku/dokku-rabbitmq) 
3. setup a rabbitmq queue: `dokku rabbitmq:create story-processor-q`
4. create an app: `dokku apps:create story-processor`
5. link the app to the rabbit queue: `dokku rabbitmq:link story-processor-q story-processor`
6. create a postgres database: `dokku postgres:create story-processor-db`
7. link the app to the postgres database: `dokku postgres:link story-processor-db story-processor`

Release the worker app
----------------------

1. setup the configuration on the dokku app: `dokku config:set MC_API_KEY=1234 BROKER_URL=http://my.rabbitmq.url SENTRY_DSN=https://mydsn@sentry.io/123 CONFIG_FILE_URL=https://my.server/api/projects.json`
2. grab the code: `git clone git@github.mit.edu:data-feminism-lab/feminicide-mc-story-processor.git`
3. add a remote: `git remote add mc dokku@feminicide.friends.mediacloud.org:story-processor`
4. push the code to the server: `git push mc master`
5. scale it to get a worker (dokku doesn't add one by default): `dokku ps:scale story-processor worker=1`

Setup the fetcher
-----------------

1. scale it to get a fetcher (dokku doesn't add one by default): `dokku ps:scale story-processor fetcher=1` (this will run the script once)
2. add a cron job something like this to fetch new stories every night: `0 8 * * * dokku --rm run story-processor fetcher /app/run-fetch.sh >> /var/tmp/story-processor-cron.log 2>&1`

Setup Database Backups
----------------------

The local logging database is useful for future interrogation, so we back it up.

1. `dokku postgres:backup-auth mc-story-processor-db AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY`
2. `dokku postgres:backup-schedule mc-story-processor-db "0 9 * * *" df-server-backup`