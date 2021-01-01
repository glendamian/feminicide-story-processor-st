Architecture Notes
==================

Tasks:
* create a new admin `web-feminicide-user@mediacloud.org` for the project
* start work on code

Code outline
------------

* Runs via cron (fetch_and_run.py)
* containers:
  * redis store
  * app
    * web: gunicorn processor.server.app
    * worker: celery worker --app=processor.tasks.app
    * env vars
      * MC_API_KEY
      * REDIS_URL
      * CELERY_TASK_SERIALIZER=json
  * celery flower
    * env vars
      * REDIS_URL

## processor/server.py

def index:
 * button to fire off monitors.get_latest_config() immediately
 * list monitors and show last run and last_processed_id

## fetch_and_run.py

monitors.get_latest_config()
  on failure, raise error and exit
monitors.queue_stories_by_page()
   for monitor in monitors:
      while more_stories:
          fetch page of results (based on last_processed_id)
          push page + monitor details into classify_stories_queue
          update last_processed_id

## processor/monitors.py

* get_latest_config()
* queue_stories_by_page()

## processor/tasks.py

**classify_stories_worker**
  pop off from the classify_stories_queue
  load appropriate model
  run all story text through model
  push results, story metadata, and monitor details in post_results_queue

**post_results_worker**
  pop off from post_results queue
  post to the URL specified
   -> on failure requeue to try again
