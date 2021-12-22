Change Log
==========

Here is a history of what was changed in each version. 

### 1.8.2

* Run web server with multiple workers and gevent

### 1.8.1

* Work on making UI faster, and including more tracking info for debugging

### 1.8.0

* Full UI for monitoring story ingest and orocessing

### 1.7.4

* Fix web ui bugs related to first run of new deployment

### 1.7.3

* Add web-based UI for monitoring story volume

### 1.7.2

* Add logging of two separated chained model scores

### 1.7.1

* Upgrade python to latest
* Store last_processed_stories_id in new `projects` table to try and reduce reprocessing for projects with broad queries
  and few positive, above threshold, stories
* Disabled-for-now support for fetching and adding entities on this side

### 1.7.0

* Switch to parallel processing model (via Prefect + Dask)
* Parse and send entities to main server
* Hack to work with temporary Media Cloud database change

### 1.6.0

Supports chained language models.

### 1.5.3

Add warning emoji to email update for projects that are near max stories per day.

### 1.5.2

Update the support model chaining format, but not implementation yet.

### 1.5.1

Fix Sentry-related bug.

### 1.5.0

Switch to RabbitMQ, also log a LOT more to our local DB.

### 1.4.0

Add database for logging story state over to to make debugging across workers easier.

### 1.3.1

Fully integrate Sentry-based centralized logging. Integrate an embeddings model.

### 1.3.0

Load full model configuration from server.

### 1.2.3

More logging and removing queues.

### 1.2.2

More work on testing and logging to chase down bugs.

### 1.2.1

Cleaned up queries and added more debug logging.

### 1.2.0

Dynamically fetch models from server.

### 1.1.0

Add in new aapf models.

### 1.0.0

Add version number, update classifier models.

### (unnumbered)

Add API key-based authentication.

### (unnumbered)

Initial release.
