import logging

from processor import get_mc_client
import processor.monitors as monitors
import processor.tasks as tasks

STORIES_PER_PAGE = 100

logger = logging.getLogger(__name__)

mc = get_mc_client()

all_monitors = monitors.list_all()
logger.info("Checking {} monitors".format(len(all_monitors)))
logger.info("  requesting {} stories/page".format(STORIES_PER_PAGE))
total_new_stories = 0
total_pages = 0

for monitor in all_monitors:
    last_processed_stories_id = monitor.get('last_processed_stories_id', 0)
    logger.info("{} (last processed_stories_id={})".format(monitor['id'], last_processed_stories_id))
    new_story_count = 0
    page_count = 0
    more_stories = True
    while more_stories:
        page_of_stories = mc.storyList(monitor['q'], monitor['fq'], last_processed_stories_id=last_processed_stories_id,
                                       text=True, rows=STORIES_PER_PAGE)
        if len(page_of_stories) > 0:
            page_count += 1
            new_story_count += len(page_of_stories)
            tasks.classify_stories_worker.delay(monitor, page_of_stories)
            monitor['last_processed_stories_id'] = last_processed_stories_id
            monitors.write_config(monitors)
        else:
            more_stories = False
    logger.info("  queued {} stories in {} pages".format(new_story_count, page_count))
    total_new_stories += new_story_count
    total_pages += page_count

logger.info("Done with {} monitors".format(len(all_monitors)))
logger.info("  {} stories over {} pages".format(total_new_stories, total_pages))
