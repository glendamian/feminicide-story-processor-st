import logging
from typing import List, Dict, Optional
import time
import tempfile
import copy
import numpy as np
import os
import json
import mcmetadata.urls as urls
import datetime as dt
from prefect import Flow, task, Parameter
from waybacknews.searchapi import SearchApiClient
from prefect.executors import LocalDaskExecutor
import requests.exceptions
import processor
import processor.database.projects_db as projects_db
from processor.classifiers import download_models
import processor.projects as projects
import scripts.tasks as prefect_tasks

PAGE_SIZE = 100
DEFAULT_DAY_OFFEST = 4
DEFAULT_DAY_WINDOW = 3
WORKER_COUNT = 16
MAX_CALLS_PER_SEC = 5
MAX_STORIES_PER_PROJECT = 10000
DELAY_SECS = 1 / MAX_CALLS_PER_SEC

wm_api = SearchApiClient("mediacloud")
tempdir = tempfile.gettempdir()


@task(name='load_projects')
def load_projects_task() -> List[Dict]:
    project_list = projects.load_project_list(force_reload=True, overwrite_last_story=False)
    projects_with_countries = [p for p in project_list if (p['country'] is not None) and len(p['country']) == 2]
    logger.info("  Found {} projects, checking {} with countries set".format(len(project_list),
                                                                             len(projects_with_countries)))
    return projects_with_countries


def _cached_domains_for_collection(cid: int):
    filepath = os.path.join(tempdir, f'sources-in-{cid}.json')
    # fetch info if it isn't cached
    if not os.path.exists(filepath):
        logger.info(f'Collection {cid}: sources not cached, fetching')
        limit = 1000
        offset = 0
        sources = []
        mc_api = processor.get_mc_client()
        while True:
            response = mc_api.source_list(collection_id=cid, limit=limit, offset=offset)
            sources += response['results']
            if response['next'] is None:
                break
            offset += limit
        with open(filepath, 'w') as f:
            json.dump(sources, f)
        return sources  # just return here to be doubly safe about the tmp dir, which might be weird on prod container
    # otherwise load up cache to reduce server queries and runtime overall
    with open(filepath, 'r') as f:
        sources = json.load(f)
        logger.info(f'Collection {cid}: sources cached {len(sources)}')
        return [s['name'] for s in sources if s['name'] is not None]


@task(name='domains_for_project')
def fetch_domains_for_projects(project: Dict) -> Dict:
    updated_project = copy.copy(project)
    all_domains = []
    for cid in project['media_collections']:  # fetch all the domains in each collection
        all_domains += _cached_domains_for_collection(cid)
    updated_project['domains'] = set(all_domains)
    return updated_project


def _query_builder(terms: str, language: str, domains: list) -> str:
    return "({}) AND (language:{}) AND ({})".format(terms, language, " OR ".join([f"domain:{d}" for d in domains]))


@task(name='fetch_project_stories')
def fetch_project_stories_task(project_list: Dict, data_source: str) -> List[Dict]:
    combined_stories = []
    end_date = dt.datetime.now() - dt.timedelta(days=DEFAULT_DAY_OFFEST)  # stories don't get processed for a few days
    for p in project_list:
        project_stories = []
        valid_stories = 0
        history = projects_db.get_history(p['id'])
        page_number = 1
        # only search stories since the last search (if we've done one before)
        start_date = end_date - dt.timedelta(days=DEFAULT_DAY_OFFEST+DEFAULT_DAY_WINDOW)
        if history.last_publish_date is not None:
            # make sure we don't accidentally cut off a half day we haven't queried against yet
            # this is OK because duplicates will get screened out later in the pipeline
            local_start_date = history.last_publish_date - dt.timedelta(days=1)
            start_date = min(local_start_date, start_date)
        # if query is too big we need to split it up
        full_project_query = _query_builder(p['search_terms'], p['language'], p['domains'])
        project_queries = [full_project_query]
        domain_divisor = 2
        queries_too_big = len(full_project_query) > pow(2, 15)
        if queries_too_big:
            while queries_too_big:
                chunked_domains = np.array_split(list(p['domains']), domain_divisor)
                project_queries = [_query_builder(p['search_terms'], p['language'], d) for d in chunked_domains]
                queries_too_big = any(len(pq) > pow(2, 15) for pq in project_queries)
                domain_divisor *= 2
            logger.info('Project {}/{}: split query into {} parts'.format(p['id'], p['title'], len(project_queries)))
        # now run all queries
        for project_query in project_queries:
            total_hits = wm_api.count(project_query, start_date, end_date)
            logger.info("Project {}/{} - {} total stories (since {})".format(p['id'], p['title'], total_hits, start_date))
            for page in wm_api.all_articles(project_query, start_date, end_date):
                logger.debug("  {} - page {}: {} stories".format(p['id'], page_number, len(page)))
                for item in page:
                    media_url = item['domain'] if len(item['domain']) > 0 else urls.canonical_domain(item['url'])
                    info = dict(
                        url=item['url'],
                        source_publish_date=item['publication_date'],
                        title=item['title'],
                        source=data_source,
                        project_id=p['id'],
                        language=item['language'],
                        authors=None,
                        media_url=media_url,
                        media_name=media_url,
                        article_url=item['article_url']
                    )
                    project_stories.append(info)
                    valid_stories += 1
                logger.info("  project {} - {} valid stories (after {})".format(p['id'], valid_stories,
                                                                                history.last_publish_date))
                combined_stories += project_stories
    return combined_stories


@task(name='fetch_text')
def fetch_archived_text_task(story: Dict) -> Optional[Dict]:
    story_details = requests.get(story['article_url']).json()
    if ('detail' in story_details) and (story_details['detail'] == 'Not Found'):  # handle missing documents
        logger.warning("No details for story {}".format(story['article_url']))
        return None
    updated_story = copy.copy(story)
    updated_story['story_text'] = story_details['snippet']
    return updated_story


if __name__ == '__main__':

    logger = logging.getLogger(__name__)
    logger.info("Starting {} story fetch job".format(processor.SOURCE_WAYBACK_MACHINE))
    logger.info(f"  Using tempdir at {tempdir}")

    # important to do because there might be new models on the server!
    logger.info("  Checking for any new models we need")
    download_models()

    with Flow("story-processor") as flow:
        if WORKER_COUNT > 1:
            flow.executor = LocalDaskExecutor(scheduler="threads", num_workers=WORKER_COUNT)
        data_source_name = Parameter("data_source", default="")
        start_time = Parameter("start_time", default=time.time())
        # 1. list all the project we need to work on
        projects_list = load_projects_task()
        # 2. figure out domains to query for each project
        projects_with_domains = fetch_domains_for_projects.map(projects_list)
        # 3. fetch all the urls from for each project from wayback machine (not mapped, so we can respect rate limiting)
        all_stories = fetch_project_stories_task(projects_with_domains, data_source_name)
        # 4. fetch pre-parsed content (will happen in parallel by story)
        stories_with_text = fetch_archived_text_task.map(all_stories)
        # 5. post batches of stories for classification
        results_data = prefect_tasks.queue_stories_for_classification_task(projects_list, stories_with_text,
                                                                           data_source_name)
        # 5. send email with results of operations
        prefect_tasks.send_email_task(results_data, data_source_name, start_time)

    # run the whole thing
    flow.run(parameters={
        'data_source': processor.SOURCE_WAYBACK_MACHINE,
        'start_time': time.time(),
    })
