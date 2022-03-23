import logging
from typing import List, Dict, Optional
import copy
import dateutil.parser
import mcmetadata as metadata
import datetime as dt

import processor
from urllib.parse import urlparse, parse_qs
from prefect import Flow, task
from prefect.executors import LocalDaskExecutor
import processor.database.stories_db as stories_db
import processor.database.projects_db as projects_db
from processor.classifiers import download_models
from processor import get_email_config, is_email_configured
import processor.projects as projects
import processor.tasks as tasks
import processor.notifications as notifications
from newscatcherapi import NewsCatcherApiClient

DEFAULT_STORIES_PER_PAGE = 150  # I found this performs poorly if set too high
DEFAULT_MAX_STORIES_PER_PROJECT = 200  # 40 * 1000  # make sure we don't do too many stories each cron run (for testing)


newscatcherapi = NewsCatcherApiClient(x_api_key=processor.NEWSCATCHER_API_KEY)


@task(name='load_projects')
def load_projects_task() -> List[Dict]:
    project_list = projects.load_project_list(force_reload=True, overwrite_last_story=False)
    logger.info("  Checking {} projects".format(len(project_list)))
    return [p for p in project_list if p['rss_url'] and (len(p['rss_url']) > 0)]


@task(name='fetch_project_stories')
def fetch_project_stories_task(project_list: Dict) -> List[Dict]:
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
                url=real_url,
                source_publish_date=item['published'],
                title=item['title'],
                source=processor.SOURCE_NEWSCATCHER,
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


@task(name='fetch_text')
def fetch_text_task(story: Dict) -> Optional[Dict]:
    html = metadata.webpages.fetch(story['url'])
    parsed = metadata.content.from_html(story['url'], html)
    updated_story = copy.copy(story)
    if parsed['status'] == 'ok':
        updated_story['story_text'] = parsed['results']['text']
        updated_story['publish_date'] = parsed['results']['publish_date']
        return updated_story
    return None


@task(name='queue_stories_for_classification')
def queue_stories_for_classification_task(project_list: List[Dict], stories: List[Dict]) -> Dict:
    total_stories = 0
    email_message = ""
    for p in project_list:
        project_stories = [s for s in stories if (s is not None) and (s['project_id'] == p['id'])]
        email_message += "Project {} - {}: {} stories\n".format(p['id'], p['title'], len(project_stories))
        total_stories += len(project_stories)
        if len(project_stories) > 0:
            # and log that we got and queued them all
            inserted_ids = stories_db.add_stories(project_stories, p, processor.SOURCE_NEWSCATCHER)
            for idx in range(0, len(inserted_ids)):
                project_stories[idx]['stories_id'] = inserted_ids[idx]
                # Newscatcher might be better at guessing publication dates than we are?
                project_stories[idx]['publish_date'] = project_stories[idx]['source_publish_date']
            # important to do this *after* we add the stories_id here
            tasks.classify_and_post_worker.delay(p, project_stories)
            # important to write this update now, because we have queued up the task to process these stories
            # the task queue will manage retrying with the stories if it fails with this batch
            publish_dates = [dateutil.parser.parse(s['source_publish_date']) for s in project_stories]
            latest_date = max(publish_dates)
            projects_db.update_history(p['id'], last_publish_date=latest_date, last_url=project_stories[0]['url'])
        logger.info("  queued {} stories for project {}/{}".format(total_stories, p['id'], p['title']))
    return dict(
        email_text=email_message,
        project_count=len(project_list),
        stories=total_stories
    )


@task(name='send_email')
def send_email_task(summary: Dict):
    email_message = ""
    email_message += "Checking {} projects.\n\n".format(summary['project_count'])
    email_message += summary['email_text']
    email_message += "\nDone - pulled {} stories.\n\n" \
                     "(An automated email from your friendly neighborhood Newscatcher story processor)" \
        .format(summary['stories'])
    if is_email_configured():
        email_config = get_email_config()
        notifications.send_email(email_config['notify_emails'],
                                 "Feminicide Newscatcher Alerts Update: {} stories".format(summary['stories']),
                                 email_message)
    else:
        logger.info("Not sending any email updates")


if __name__ == '__main__':

    logger = logging.getLogger(__name__)
    logger.info("Starting story fetch job")

    # important to do because there might be new models on the server!
    logger.info("  Checking for any new models we need")
    download_models()

    with Flow("story-processor") as flow:
        #flow.executor = LocalDaskExecutor(scheduler="threads", num_workers=16)  # execute `map` calls in parallel
        # 1. list all the project we need to work on
        projects_list = load_projects_task()
        # 2. fetch all the urls from for each project from newscatcher
        all_stories = fetch_project_stories_task(projects_list)
        # 3. fetch webpage text and parse all the stories (will happen in parallel by story)
        stories_with_text = fetch_text_task.map(all_stories)
        # 4. post batches of stories for classification
        results_data = queue_stories_for_classification_task(projects_list, stories_with_text)
        # 5. send email with results of operations
        send_email_task(results_data)

    # run the whole thing
    flow.run()
