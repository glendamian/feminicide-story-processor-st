Change Log
==========

Here is a history of what was changed in each version. 

### v2.3.13

* Work on better error reporting 

### v2.3.12

* Remove debugging statements 

### v2.3.11

* Tweaking NewsCatcher ingest to work on odd behavior we're seeing

### v2.3.10

* More work on web dashboard errors

### v2.3.9

* Update dependencies to try and fix dashboard website timeout error on query to Media Cloud. 

### v2.3.8

* Add charts to show discovery/ingest by platform on homepage and project pages.
* Show list of recent URLs discovered by project.

### v2.3.7

* Change Media Cloud processor to err on the side of recentness over completeness, specifically by only querying
  for stories published within the last few days. This should ensure we don't fall too many days behind on projects
  that have lots of results. The downside is that for those projects it could miss stories each day.

### v2.3.6

* Work on dependency problems.

### v2.3.5

* Fix Media Cloud quert start date to avoid getting older stories by accident (because we need to reprocess older
  feeds to backfill some gaps in our main databse, and those would have new high processed_stories_id values).

### v2.3.4

* Fix logging for stories with no unique ID from their source

### v2.3.3

* Respect last check date in newscatcher fetching

### v2.3.2

* Small bug fixes to make it more robust

### v2.3.1

* Time how long a fetch takes, and include in email report
* Fixes for newscatcher integration

### v2.3.0

* Initial integration with newscatcher (triggered by having a filling in "country" property)

### v2.2.0

* Add entities to each story posted (via news-entity-server)

### 2.1.3

* Logging tweaks.

### 2.1.2

* Various small bug fixes for prod deployment.

### 2.1.1

* First work on support for 64 bit story ids.

### 2.1.0

* Check last processed URL within an RSS to make sure we don't re-process stories.

### 2.0.0

* Add initial support for fetching via Google Alerts RSS feeds.

### 1.8.4

* Update handling of Media Cloud crashes

### 1.8.3

* Fix a small no-data bug

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
