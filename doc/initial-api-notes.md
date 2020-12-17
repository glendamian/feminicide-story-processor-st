Feminicide Media Cloud Story Processor
======================================

Here's a sketch of an API for this work. I've made up a few terms to help us talk about this:
 * "Story Processor" - this is the piece that runs story text against models, living on the Media Cloud server
 * "Feminicide Server" - this is the brains of the operation that lives at D+F somewhere
 * "monitor" - this is the term to describe how a collaboration with a group is captured in the Feminicide Server

API Architecture
----------------

## API on Story Processor

**POST /api/monitors/refresh-now**

The Story Processor will fetch the latest config every night from the Feminicide Server. However, if you want to force it to refresh the config file ASAP then you can hit this endpoint.

Questions:
 * Should this accept an optional JSON object that is an updated config file to use?


## API on Feminicide Server

**GET /api/monitors/config**

The Feminicide Server is the single point of authority for the ongoing monitors. The Story Processor uses this endpoint to ask the Feminicide Server for that configuration file. The Feminicide Server returns JSON content like this:

```json
{
  "version": 0.1,
  "server_url": "http://feminicide-server.url/",
  "monitors": [
    {"monitor_id": 12, "terms": "mc AND query AND media_id:1234", "name": "uruguay1", "start_date": "2020-01-01", "model_url": "http://made.up/url/to/download/model", "model_threshold": 0.5},
    {"monitor_id": 13, "query": "mc AND query AND tags_id_media:(1234 4321)", "name": "usa_partner", "start_date": "2020-06-01", "model_url": "http://made.up/url/to/download/other-model", "model_threshold": 0.5}
  ]
}
```

**POST /api/stories/create**

The Story Processor produces results, basically a list of story_ids and results of the model. Since it has no stateful storage, it posts these results back to the Feminicide Server to store. It posts back JSON data in this form:

```json
{
  "source": "media_cloud",
  "stories": [
    {"stories_id": 1234556, "monitor_id": "12", "model_results": 0.12, "story": { "url": "n", "entities": [], "media_id": 1234, "media_url": "https", "media_name": "newspaper", "title": "my story title", "publish_date": "2020-01-01:09:00:00", "stories_id": 1234556 }},
    {"stories_id": 6543221, "monitor_id": "12", "model_results": 0.87, "story": { "url": "n", "entities": [], "media_id": 1234, "media_url": "https", "media_name": "newspaper", "title": "my story title", "publish_date": "2020-01-01:09:00:00", "stories_id": 6543221 }},
    {...}
  ]
}
```
