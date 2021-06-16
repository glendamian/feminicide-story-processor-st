import logging
import dateparser
from datetime import date
from mediacloud.error import MCException

from processor import get_mc_client, get_email_config, is_email_configured
import processor.projects as projects
import processor.tasks as tasks
import processor.notifications as notifications

STORIES_PER_PAGE = 100  # I found this performs poorly if set higher than 100
MAX_STORIES_PER_PROJECT = 20 * 1000  # make sure we don't do too many stories each cron run (for testing)

logger = logging.getLogger(__name__)
logger.info("Starting story fetch job")

mc = get_mc_client()

email_message = ""

project_list = projects.load_project_list(force_reload=True)
project_history = projects.load_history()
logger.info("  Checking {} projects".format(len(project_list)))
logger.info("    will request {} stories/page".format(STORIES_PER_PAGE))
email_message += "Checked {} projects.\n\n".format(len(project_list))
total_new_stories = 0
total_pages = 0

# iterate over all the projects, fetching new stories and q-ing them up for analysis (upto MAX_STORIES_PER_PROJECT)
#project_list = [p for p in project_list if p['id'] == 84]  # TMP
for project in project_list:
    # figure out the query to run based on the history
    last_processed_stories_id = project_history.get(str(project['id']), 0)  # (JSON dict keys have to be strings)
    logger.info("Checking project {}/{} (last processed_stories_id={})".format(project['id'], project['title'],
                                                                               last_processed_stories_id))
    email_message += "Project {} - {}:\n".format(project['id'], project['title'])
    # setup queries to filter by language too so we only get stories the model can process
    q = "({}) AND language:{} AND tags_id_media:({})".format(
        project['search_terms'],
        project['language'],
        " ".join([str(tid) for tid in project['media_collections']]))
    start_date = dateparser.parse(project['start_date'])
    now = date.today()
    fq = mc.dates_as_query_clause(start_date, now)
    # page through any new stories
    new_story_count = 0
    page_count = 0
    more_stories = True
    while more_stories and new_story_count < MAX_STORIES_PER_PROJECT:
        try:
            page_of_stories = mc.storyList(q, fq, last_processed_stories_id=last_processed_stories_id,
                                           text=True, rows=STORIES_PER_PAGE)
            logger.info("    page {}: ({}) stories".format(page_count, len(page_of_stories)))
        except MCException as mce:
            logger.error("  Query failed on project {}. Skipping project.".format(project['id']))
            logger.exception(mce)
            more_stories = False
            continue  # fail gracefully by going to the next project; maybe next cron run it'll work?
        if len(page_of_stories) > 0:
            page_count += 1
            new_story_count += len(page_of_stories)
            # TODO: change this to use a celery chain
            tasks.classify_and_post_worker.delay(project, page_of_stories)
            last_processed_stories_id = page_of_stories[-1]['processed_stories_id']
            # important to write this update now, because we have queued up the task to process these stories
            # the task queue will manage retrying with the stories if it fails with this batch
            projects.update_processing_history(project['id'], last_processed_stories_id)
        else:
            more_stories = False
    logger.info("  queued {} stories for project {}/{} (in {} pages)".format(new_story_count, project['id'],
                                                                             project['title'], page_count))
    email_message += "    found {} new stories (over {} pages)\n\n".format(new_story_count, page_count)
    total_new_stories += new_story_count
    total_pages += page_count

logger.info("Done with {} projects".format(len(project_list)))
logger.info("  {} stories over {} pages".format(total_new_stories, total_pages))
email_message += "Done - pulled {} stories over {} pages total.\n\n" \
                 "(An automated email from yout friendly neighborhood Media Cloud story processor)"\
    .format(total_new_stories, total_pages)

# send email!
if is_email_configured():
    email_config = get_email_config()
    notifications.send_email(email_config['notify_emails'],
                             "Feminicide Media Cloud Update: {} stories".format(total_new_stories),
                             email_message)
else:
    logger.info("Not sending any email updates")
