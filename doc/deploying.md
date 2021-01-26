Deploying
=========

This is built to deploy via dokku. This takes a rounds of configuration to set up correctly.

Create the Dokku apps
---------------------

1. [install Dokku](http://dokku.viewdocs.io/dokku/getting-started/installation/)
2. install the [Dokku redis plugin](https://github.com/dokku/dokku-redis) 
3. setup a redis queue: `dokku redis:create story-processor-q`
4. create an app: `dokku apps:cerate story-processor`
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
