import logging
from typing import List, Dict
import feedparser
import copy
import dateutil.parser
import langdetect

import processor
import processor.entities as entities
import processor.util.domains as domains
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

DEFAULT_STORIES_PER_PAGE = 150  # I found this performs poorly if set too high
DEFAULT_MAX_STORIES_PER_PROJECT = 200  # 40 * 1000  # make sure we don't do too many stories each cron run (for testing)


def _url_from_google_alert_link(rss_item) -> str:
    url = rss_item.entries[0]['link']
    o = urlparse(url)
    query = parse_qs(o.query)
    return query['url'][0]


@task(name='load_projects')
def load_projects_task() -> List[Dict]:
    project_list = projects.load_project_list(force_reload=True, overwrite_last_story=False)
    logger.info("  Checking {} projects".format(len(project_list)))
    return [p for p in project_list if 'google_alert_rss' in p]


@task(name='fetch_project_stories')
def fetch_project_stories_task(project: Dict) -> List[Dict]:
    feed = feedparser.parse(project['google_alert_rss'])
    results = []
    valid_stories = 0
    logger.info("Project {}/{} - {} stories".format(project['id'], project['title'], len(feed.entries)))
    history = projects_db.get_history(project['id'])
    for item in feed.entries:
        # only process stories published after the last check we ran
        published_date = dateutil.parser.parse(item['published'])
        if history.last_publish_date and (published_date < history.last_publish_date):
            continue
        # story was published more recently than latest one we saw, so process it
        real_url = _url_from_google_alert_link(item['link'])
        info = dict(
            url=real_url,
            google_publish_date=item['published'],
            title=item['title'],
            source=processor.SOURCE_GOOGLE_ALERTS,
            project_id=project['id'],
            media_url=domains.get_canonical_mediacloud_domain(real_url),
            media_name=domains.get_canonical_mediacloud_domain(real_url)
        )
        results.append(info)
        valid_stories += 1
    logger.info("  project {} - {} valid stories (after {})".format(project['id'], valid_stories, history.last_publish_date))
    return results


@task(name='fetch_text')
def fetch_text_task(story: Dict) -> Dict:
    parsed = entities.content_from_url(story['url'])
    updated_story = copy.copy(story)
    if parsed['status'] == 'ok':
        updated_story['text'] = parsed['results']['text']
        updated_story['language'] = langdetect.detect(parsed['results']['text'])
        updated_story['publish_date'] = parsed['results']['publish_date']
    else:
        return None


@task(name='queue_stories_for_classification')
def queue_stories_for_classification_task(projects: List[Dict], stories: List[Dict]) -> Dict:
    total_stories = 0
    email_message = ""
    for p in projects:
        email_message += "Project {} - {}:\n".format(p['id'], p['title'])
        project_stories = [s for s in stories if (s is not None) and (s['project_id'] == p['id'])]
        email_message += "  {} stories:\n".format(p['id'], len(project_stories))
        total_stories += len(project_stories)
        tasks.classify_and_post_worker.delay(p, project_stories)
        # and log that we got and queued them all
        inserted_ids = stories_db.add_stories(project_stories, p, processor.SOURCE_GOOGLE_ALERTS)
        for idx in range(0, len(inserted_ids)):
            project_stories[idx]['stories_id'] = inserted_ids[idx]
        # important to write this update now, because we have queued up the task to process these stories
        # the task queue will manage retrying with the stories if it fails with this batch
        latest_date = max([dateutil.parser.parse(p['publish_date']) for p in project_stories])
        projects_db.update_history(p['id'], last_publish_date=latest_date)
        logger.info("  queued {} stories for project {}/{}".format(total_stories, p['id'], p['title']))
    return dict(
        email_text=email_message,
        project_count=len(projects),
        stories=total_stories
    )


@task(name='send_email')
def send_email_task(summary: Dict):
    email_message = ""
    email_message += "Checking {} projects.\n\n".format(summary['project_count'])
    email_message += summary['email_text']
    email_message += "Done - pulled {} stories.\n\n" \
                     "(An automated email from your friendly neighborhood Google Alert story processor)" \
        .format(summary['stories'])
    if is_email_configured():
        email_config = get_email_config()
        notifications.send_email(email_config['notify_emails'],
                                 "Feminicide Google Alerts Update: {} stories".format(summary['stories']),
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
        flow.executor = LocalDaskExecutor(scheduler="threads", num_workers=6)  # execute `map` calls in parallel
        # 1. list all the project we need to work on
        projects_list = load_projects_task()
        # 2. fetch all the urls from Google Alerts RSS feeds (will happen in parallel by project)
        stories = fetch_project_stories_task.map(projects_list)
        # 3. fetch webpage text and parse all the stories (will happen in parallel by story)
        stories_with_text = fetch_text_task.map(stories)
        # 4. post batches of stories for classification
        results_data = queue_stories_for_classification_task(projects_list, stories_with_text)
        # 5. send email with results of operations
        send_email_task(results_data)

    # run the whole thing
    flow.run()
