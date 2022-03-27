import logging
import math
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

PAGE_SIZE = 100
DAY_WINDOW = 3

newscatcherapi = NewsCatcherApiClient(x_api_key=processor.NEWSCATCHER_API_KEY)


@task(name='load_projects')
def load_projects_task() -> List[Dict]:
    project_list = projects.load_project_list(force_reload=True, overwrite_last_story=False)
    projects_with_countries = [p for p in project_list if (p['country'] is not None) and len(p['country']) == 2]
    logger.info("  Found {} projects, checking {} with countries set".format(len(project_list),
                                                                             len(projects_with_countries)))
    return projects_with_countries


def _fetch_results(project: Dict, start_date, end_date, page: int = 1) -> Dict:
    return newscatcherapi.get_search(
        q=project['search_terms'],
        lang=project['language'],
        countries=project['country'],
        page_size=PAGE_SIZE,
        from_=start_date.strftime("%Y-%m-%d"),
        to_=end_date.strftime("%Y-%m-%d"),
    )


@task(name='fetch_project_stories')
def fetch_project_stories_task(project_list: Dict, data_source: str) -> List[Dict]:
    combined_stories = []
    for p in project_list:
        project_stories = []
        valid_stories = 0
        history = projects_db.get_history(p['id'])
        end_date = dt.date.today()
        start_date = end_date - dt.timedelta(days=DAY_WINDOW)
        page_number = 1
        current_page = _fetch_results(p, start_date, end_date, page_number)
        total_hits = current_page['total_hits']
        logger.info("Project {}/{} - {} total stories".format(p['id'], p['title'], total_hits))
        if total_hits > 0:
            page_count = math.ceil(total_hits / current_page)
            keep_going = True;
            while keep_going:
                for item in current_page['articles']:
                    logger.info("  {} - page {}: {} stories".format(p['id'], page_number, len(current_page['articles'])))
                    # maybe stop when we hit a url we've processed already
                    real_url = item['link']
                    if history.last_url == real_url:
                        logger.info("  Found last_url on {}, skipping the rest".format(p['id']))
                        keep_going = False
                        break # out of the for loop of all articles on page, back to while "more pages"
                    # story was published more recently than latest one we saw, so process it
                    info = dict(
                        url=real_url,
                        source_publish_date=item['published'],
                        title=item['title'],
                        source=data_source,
                        project_id=p['id'],
                        language=p['language'],
                        authors=item['authors'],
                        media_url=metadata.domains.from_url(real_url),
                        media_name=metadata.domains.from_url(real_url)
                        # too bad there isn't somewher we can store the `id` (string)
                    )
                    project_stories.append(info)
                    valid_stories += 1
                if keep_going:  # check after page is processed
                    keep_going = page_number <= page_count
                    _fetch_results(p, start_date, end_date, page_number)
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
