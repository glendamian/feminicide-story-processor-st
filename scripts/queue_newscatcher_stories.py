import logging
from typing import List, Dict
import mcmetadata as metadata
import datetime as dt
from prefect import Flow, task, Parameter
from newscatcherapi import NewsCatcherApiClient

import processor
import processor.database.projects_db as projects_db
from processor.classifiers import download_models
import processor.projects as projects
import scripts.tasks as prefect_tasks

DEFAULT_STORIES_PER_PAGE = 150  # I found this performs poorly if set too high
DEFAULT_MAX_STORIES_PER_PROJECT = 200  # 40 * 1000  # make sure we don't do too many stories each cron run (for testing)

newscatcherapi = NewsCatcherApiClient(x_api_key=processor.NEWSCATCHER_API_KEY)


@task(name='load_projects')
def load_projects_task() -> List[Dict]:
    project_list = projects.load_project_list(force_reload=True, overwrite_last_story=False)
    logger.info("  Checking {} projects".format(len(project_list)))
    return project_list


@task(name='fetch_project_stories')
def fetch_project_stories_task(project_list: Dict, data_source: str) -> List[Dict]:
    combined_stories = []
    for p in project_list:
        project_stories = []
        valid_stories = 0
        history = projects_db.get_history(p['id'])
        today = dt.date.today()
        yesterday = today - dt.timedelta(days=1)
        results = newscatcherapi.get_search(
            q=p['search_terms'],
            lang=p['language'],
            countries='UY',  # TBD - this needs to be set on each project
            page_size=100,
            to_=today.strftime("%Y-%m-%d"),
            from_=yesterday.strftime("%Y-%m-%d"),
        )
        logger.info("Project {}/{} - {} stories".format(p['id'], p['title'], len(results)))
        for item in results['articles']:
            # only process stories published after the last check we ran?
            # or maybe stop when we hit a url we've processed already?
            real_url = item['link']
            if history.last_url == real_url:
                logger.info("  Found last_url on {}, skipping the rest".format(p['id']))
                break
            # story was published more recently than latest one we saw, so process it
            info = dict(
                stories_id=item['id'], # TODO: double check this
                url=real_url,
                source_publish_date=item['published'],
                title=item['title'],
                source=data_source,
                project_id=p['id'],
                language=p['language'],
                authors=item['authors'],
                media_url=metadata.domains.from_url(real_url),
                media_name=metadata.domains.from_url(real_url)
            )
            project_stories.append(info)
            valid_stories += 1
        logger.info("  project {} - {} valid stories (after {})".format(p['id'], valid_stories,
                                                                        history.last_publish_date))
        combined_stories += project_stories
    return combined_stories


if __name__ == '__main__':

    logger = logging.getLogger(__name__)
    logger.info("Starting story fetch job")

    # important to do because there might be new models on the server!
    logger.info("  Checking for any new models we need")
    download_models()

    with Flow("story-processor") as flow:
        #flow.executor = LocalDaskExecutor(scheduler="threads", num_workers=16)  # execute `map` calls in parallel
        data_source_name = Parameter("data_source", default="")
        # 1. list all the project we need to work on
        projects_list = load_projects_task()
        # 2. fetch all the urls from for each project from newscatcher
        all_stories = fetch_project_stories_task(projects_list, data_source_name)
        # 3. fetch webpage text and parse all the stories (will happen in parallel by story)
        stories_with_text = prefect_tasks.fetch_text_task.map(all_stories)
        # 4. post batches of stories for classification
        results_data = prefect_tasks.queue_stories_for_classification_task(projects_list, stories_with_text,
                                                                           data_source_name)
        # 5. send email with results of operations
        prefect_tasks.send_email_task(results_data, data_source_name)

    # run the whole thing
    flow.run(parameters={
        'data_source': processor.SOURCE_NEWSCATCHER
    })
