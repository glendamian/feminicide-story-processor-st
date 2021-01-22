import logging
import dateparser
from datetime import date
from mediacloud.error import MCException

from processor import get_mc_client
import processor.projects as projects
import processor.tasks as tasks

STORIES_PER_PAGE = 100

logger = logging.getLogger(__name__)

mc = get_mc_client()

all_projects = projects.load_config(force_reload=True)
project_history = projects.load_history()
logger.info("Checking {} projects".format(len(all_projects)))
logger.info("  will request {} stories/page".format(STORIES_PER_PAGE))
total_new_stories = 0
total_pages = 0

for project in all_projects:
    # figure out the query to run based on the history
    last_processed_stories_id = project_history.get(str(project['id']), 0)  # (JSON dict keys have to be strings)
    logger.info("Checking {} - {} (last processed_stories_id={})".format(project['id'], project['title'],
                                                                         last_processed_stories_id))
    # filter by language too so we only get stories the model can process
    q = "({}) AND language:{}".format(project['search_terms'], project['language'])
    start_date = dateparser.parse(project['start_date'])
    now = date.today()
    fq = ["tags_id_media:({})".format(" ".join([str(tid) for tid in project['media_collections']])),
          mc.dates_as_query_clause(start_date, now)]
    # page through any new stories
    new_story_count = 0
    page_count = 0
    more_stories = True
    while more_stories:
        try:
            page_of_stories = mc.storyList(q, fq, last_processed_stories_id=last_processed_stories_id,
                                           text=True, rows=STORIES_PER_PAGE)
        except MCException as mce:
            logger.error("Query failed on project {}. Skipping project.".format(project['id']))
            logger.exception(mce)
            more_stories = False
        logger.debug("  page {}: ({}) stories".format(page_count, len(page_of_stories)))
        if len(page_of_stories) > 0:
            page_count += 1
            new_story_count += len(page_of_stories)
            # TODO: change this to use a celery chain
            tasks.classify_stories_worker.delay(project, page_of_stories)
            last_processed_stories_id = page_of_stories[-1]['processed_stories_id']
            # important to write this update now, because we have queued up the task to process these stories
            # the task queue will manage retrying with the stories if it fails with this batch
            projects.update_processing_history(project['id'], last_processed_stories_id)
        else:
            more_stories = False
    logger.info("  queued {} stories in {} pages".format(new_story_count, page_count))
    total_new_stories += new_story_count
    total_pages += page_count

logger.info("Done with {} projects".format(len(all_projects)))
logger.info("  {} stories over {} pages".format(total_new_stories, total_pages))
