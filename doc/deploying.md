Deploying
=========

This is built to deploy via [dokku](http://dokku.viewdocs.io/dokku/). This takes a few rounds of configuration to set up
correctly. There are three components:
* The worker app - ingest stories from Media Cloud and queues them up for classification and sending to central server
* The queues - one holds batches of stories needing classification, the other batches to be posted to the central server
* The queue monitor - lets us keep an eye on queue servicing speeds

Create the Dokku apps
---------------------

1. [install Dokku](http://dokku.viewdocs.io/dokku/getting-started/installation/)
2. install the [Dokku redis plugin](https://github.com/dokku/dokku-redis) 
3. setup a redis queue: `dokku redis:create story-processor-q`
4. create an app: `dokku apps:create story-processor`
5. link it to the redis queue: `dokku redis:link story-processor-q story-processor`
6. create an app to monitor the queues: `dokku apps:create celery-flower`
7. link it to the redis queue: `dokku redis:link story-processor-q celery-flower`

Release the queue monitoring
----------------------------

1. grab the code: `git clone git@github.com:mitmedialab/celery-flower-heroku.git`
2. add a remote: `git remote add mc dokku@feminicide.friends.mediacloud.org:celery-flower`   
3. push the code to the server: `git push mc master`

Release the worker app
----------------------

1. setup the configuration on the dokku app: `dokku config:set MC_API_KEY=1234 BROKER_URL=http://my.redis.url SENTRY_DSN=https://mydsn@sentry.io/123 CONFIG_FILE_URL=https://my.server/api/projects.json`
2. grab the code: `git clone git@github.mit.edu:data-feminism-lab/feminicide-mc-story-processor.git`
3. add a remote: `git remote add mc dokku@feminicide.friends.mediacloud.org:story-processor`
4. push the code to the server: `git push mc master`
5. scale it to get a worker (dokku doesn't add one by default): `dokku ps:scale story-processor worker=1`

Setup the fetcher
-----------------

1. scale it to get a fetcher (dokku doesn't add one by default): `dokku ps:scale story-processor fetcher=1` (this will run the script once)
2. add a cron job something like this to fetch new stories every night: `0 8 * * * dokku --rm run story-processor fetcher /app/run-fetch.sh >> /var/tmp/story-processor-cron.log 2>&1`
