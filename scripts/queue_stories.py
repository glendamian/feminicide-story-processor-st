import logging
import dateparser
from datetime import date
from mediacloud.error import MCException
from requests.exceptions import ConnectionError
from typing import List, Dict
from prefect import Flow, Parameter, task, unmapped
from prefect.executors import LocalDaskExecutor
import processor.database.stories_db as stories_db
import processor.database.projects_db as projects_db
from processor.classifiers import download_models
from processor import get_mc_client, get_email_config, is_email_configured
import processor.projects as projects
import processor.tasks as tasks
import processor.notifications as notifications

DEFAULT_STORIES_PER_PAGE = 100  # I found this performs poorly if set higher than 100
DEFAULT_MAX_STORIES_PER_PROJECT = 40 * 1000  # make sure we don't do too many stories each cron run (for testing)


@task(name='load_projects')
def load_projects_task() -> List[Dict]:
    project_list = projects.load_project_list(force_reload=True, overwrite_last_story=False)
    logger.info("  Checking {} projects".format(len(project_list)))
    return project_list


@task(name='process_project')
def process_project_task(project: Dict, page_size: int, max_stories: int) -> Dict:
    mc = get_mc_client()
    project_last_processed_stories_id = project['local_processed_stories_id']
    project_email_message = ""
    logger.info("Checking project {}/{} (last processed_stories_id={})".format(project['id'], project['title'],
                                                                               project_last_processed_stories_id))
    logger.info("  {} stories/page up to {}".format(page_size, max_stories))
    project_email_message += "Project {} - {}:\n".format(project['id'], project['title'])
    # setup queries to filter by language too so we only get stories the model can process
    q = "({}) AND language:{} AND tags_id_media:({})".format(
        project['search_terms'],
        project['language'],
        " ".join([str(tid) for tid in project['media_collections']]))
# HACK - we need to query from *after* the Nov Media Cloud crash (for now), otherwise paging doesn't work
    # start_date = dateparser.parse(project['start_date'])
    start_date = dateparser.parse("2021-12-01")
    now = date.today()
    fq = mc.dates_as_query_clause(start_date, now)
    # page through any new stories
    story_count = 0
    page_count = 0
    more_stories = True
    while more_stories and (story_count < max_stories):
        try:
            page_of_stories = mc.storyList(q, fq, last_processed_stories_id=project_last_processed_stories_id,
                                           text=True, rows=page_size)
            logger.info("    {} - page {}: ({}) stories".format(project['id'], page_count, len(page_of_stories)))
        except ConnectionError as ce:
            logger.error("  Connection failed on project {}. Skipping project.".format(project['id']))
            logger.exception(ce)
            more_stories = False
            continue  # fail gracefully by going to the next project; maybe next cron run it'll work?
        except MCException as mce:
            logger.error("  Query failed on project {}. Skipping project.".format(project['id']))
            logger.exception(mce)
            more_stories = False
            continue  # fail gracefully by going to the next project; maybe next cron run it'll work?
        if len(page_of_stories) > 0:
            page_count += 1
            story_count += len(page_of_stories)
            tasks.classify_and_post_worker.delay(project, page_of_stories)
            project_last_processed_stories_id = page_of_stories[-1]['processed_stories_id']
            # and log that we got and queued them all
            stories_db.add_stories(page_of_stories, project)
            # important to write this update now, because we have queued up the task to process these stories
            # the task queue will manage retrying with the stories if it fails with this batch
            projects_db.update_history(project['id'], project_last_processed_stories_id)
        else:
            more_stories = False
    logger.info("  queued {} stories for project {}/{} (in {} pages)".format(story_count, project['id'],
                                                                             project['title'], page_count))
    #  add a summary to the email we are generating
    warnings = ""
    if story_count > (max_stories * 0.8):  # try to get our attention in the email
        warnings += "(⚠️️️ query might be too broad)"
    project_email_message += "    found {} new stories (over {} pages) {}\n\n".format(story_count, page_count, warnings)
    return dict(
        email_text=project_email_message,
        stories=story_count,
        pages=page_count,
    )


@task(name='send_email')
def send_email_task(project_details: List[Dict]):
    total_new_stories = sum([s['stories'] for s in project_details])
    total_pages = sum([s['pages'] for s in project_details])
    email_message = ""
    email_message += "Checking {} projects.\n\n".format(len(project_details))
    for p in project_details:
        email_message += p['email_text']
    logger.info("Done with {} projects".format(len(project_details)))
    logger.info("  {} stories over {} pages".format(total_new_stories, total_pages))
    email_message += "Done - pulled {} stories over {} pages total.\n\n" \
                     "(An automated email from your friendly neighborhood Media Cloud story processor)" \
        .format(total_new_stories, total_pages)
    if is_email_configured():
        email_config = get_email_config()
        notifications.send_email(email_config['notify_emails'],
                                 "Feminicide Media Cloud Update: {} stories".format(total_new_stories),
                                 email_message)
    else:
        logger.info("Not sending any email updates")


if __name__ == '__main__':

    logger = logging.getLogger(__name__)
    logger.info("Starting story fetch job")

    # important to do because there might new models on the server!
    logger.info("  Checking for any new models we need")
    download_models()

    with Flow("story-processor") as flow:
        flow.executor = LocalDaskExecutor(scheduler="threads", num_workers=6)  # execute `map` calls in parallel
        # read parameters
        stories_per_page = Parameter("stories_per_page", default=DEFAULT_STORIES_PER_PAGE)
        max_stories_per_project = Parameter("max_stories_per_project", default=DEFAULT_MAX_STORIES_PER_PROJECT)
        logger.info("    will request {} stories/page (up to {})".format(stories_per_page, max_stories_per_project))
        # 1. list all the project we need to work on
        projects_list = load_projects_task()
        # 2. process all the projects (in parallel)
        project_statuses = process_project_task.map(projects_list,
                                                    page_size=unmapped(stories_per_page),
                                                    max_stories=unmapped(max_stories_per_project))
        # 3. send email with results of operations
        send_email_task(project_statuses)

    # run the whole thing
    flow.run(parameters={
        'stories_per_page': DEFAULT_STORIES_PER_PAGE,
        'max_stories_per_project': DEFAULT_MAX_STORIES_PER_PROJECT,
    })