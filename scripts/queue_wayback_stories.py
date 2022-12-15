import logging
from typing import List, Dict, Optional
import time
import copy
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
WORKER_COUNT = 1
MAX_CALLS_PER_SEC = 5
MAX_STORIES_PER_PROJECT = 10000
DELAY_SECS = 1 / MAX_CALLS_PER_SEC

api = SearchApiClient("mediacloud")


@task(name='load_projects')
def load_projects_task() -> List[Dict]:
    project_list = projects.load_project_list(force_reload=True, overwrite_last_story=False)
    projects_with_countries = [p for p in project_list if (p['country'] is not None) and len(p['country']) == 2]
    logger.info("  Found {} projects, checking {} with countries set".format(len(project_list),
                                                                             len(projects_with_countries)))
    return projects_with_countries


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
            # make sure we don't accidently cut off a half day we haven't queried against yet
            # this is OK because duplicates will get screened out later in the pipeline
            local_start_date = history.last_publish_date - dt.timedelta(days=1)
            start_date = min(local_start_date, start_date)
        project_query = "{} AND language:{}".format(p['search_terms'], p['language'])
        total_hits = api.count(project_query, start_date, end_date)
        logger.info("Project {}/{} - {} total stories (since {})".format(p['id'], p['title'], total_hits, start_date))
        for page in api.all_articles(project_query, start_date, end_date):
            logger.debug("  {} - page {}: {} stories".format(p['id'], page_number, len(page)))
            for item in page:
                media_url = item['domain'] if len(item['domain'] > 0) else urls.canonical_domain(item['url'])
                info = dict(
                    url=item['url'],
                    publish_date=item['publication_date'],
                    title=item['title'],
                    source=data_source,
                    project_id=p['id'],
                    language=item['language'],
                    authors=None,
                    media_url=media_url,
                    media_name=media_url
                )
                project_stories.append(info)
                valid_stories += 1
            logger.info("  project {} - {} valid stories (after {})".format(p['id'], valid_stories,
                                                                            history.last_publish_date))
            combined_stories += project_stories
    return combined_stories


@task(name='fetch_text')
def fetch_achived_text_task(story: Dict) -> Optional[Dict]:
    story_details = requests.get(story['article_url']).json()
    if story_details['detail'] == 'Not Found':
        logger.warning("No details for story {}".format(story['article_url']))
        return None
    updated_story = copy.copy(story)
    updated_story['story_text'] = story_details['snippet']
    return updated_story


if __name__ == '__main__':

    logger = logging.getLogger(__name__)
    logger.info("Starting {} story fetch job".format(processor.SOURCE_WAYBACK_MACHINE))

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
        # 2. fetch all the urls from for each project from wayback machine (not mapped, so we can respect rate limiting)
        all_stories = fetch_project_stories_task(projects_list, data_source_name)
        # 3. fetch pre-parsed content (will happen in parallel by story)
        stories_with_text = fetch_achived_text_task.map(all_stories)
        # 4. post batches of stories for classification
        results_data = prefect_tasks.queue_stories_for_classification_task(projects_list, stories_with_text,
                                                                           data_source_name)
        # 5. send email with results of operations
        prefect_tasks.send_email_task(results_data, data_source_name, start_time)

    # run the whole thing
    flow.run(parameters={
        'data_source': processor.SOURCE_WAYBACK_MACHINE,
        'start_time': time.time(),
    })
