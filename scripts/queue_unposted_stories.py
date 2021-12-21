import logging
from typing import List, Dict
from prefect import Flow, Parameter, task, unmapped
import processor.database.stories_db as stories_db
from processor.classifiers import download_models
from processor import get_mc_client, get_email_config, is_email_configured
import processor.projects as projects
import processor.notifications as notifications

DEFAULT_STORIES_PER_PAGE = 100  # I found this performs poorly if set higher than 100


@task(name='load_projects')
def load_projects_task() -> List[Dict]:
    project_list = projects.load_project_list(force_reload=True, overwrite_last_story=False)
    logger.info("  Checking {} projects".format(len(project_list)))
    return project_list


def chunks(lst, n):
    """
    Yield successive n-sized chunks from lst.
    https://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks
    """
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


@task(name='process_project')
def process_project_task(project: Dict, page_size: int) -> Dict:
    mc = get_mc_client()
    project_email_message = ""
    project_email_message += "Project {} - {}:\n".format(project['id'], project['title'])
    needing_posting_count = stories_db.unposted_above_story_count(project['id'])
    logger.info("Project {} - {} unposted above threshold stories to process".format(
        project['id'], needing_posting_count))
    story_count = 0
    page_count = 0
    if needing_posting_count > 0:
        stories = stories_db.unposted_stories(project['id'])
        for page in chunks(stories, page_size):
            # find the matching media cloud stories
            story_ids = [str(s['stories_id']) for s in page]
            stories = mc.storyList("stories_id:({})".format(" ".join(story_ids)), rows=page_size)
            # add in the scores from the logging db
            story_score_lookup = {r['stories_id']: r for r in page}
            for s in stories:
                s['confidence'] = story_score_lookup[s['stories_id']]['model_score']
                s['model_1_score'] = story_score_lookup[s['stories_id']]['model_1_score']
                s['model_2_score'] = story_score_lookup[s['stories_id']]['model_2_score']
            # strip unneeded fields
            stories_to_send = projects.prep_stories_for_posting(project, stories)
            # send to main server
            projects.post_results(project, stories_to_send)
            # and log that we did it
            stories_db.update_stories_posted_date(stories_to_send, project['id'])
            story_count += len(stories_to_send)
            page_count += 1
    logger.info("  sent {} stories for project {}".format(story_count, project['id']))
    #  add a summary to the email we are generating
    project_email_message += "    posted {} stories from db {}\n\n".format(story_count, page_count)
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
                                 "Feminicide Media Cloud Catchup: {} stories".format(total_new_stories),
                                 email_message)
    else:
        logger.info("Not sending any email updates")


if __name__ == '__main__':

    logger = logging.getLogger(__name__)
    logger.info("Starting story catchup job")

    # important to do because there might new models on the server!
    logger.info("  Checking for any new models we need")
    download_models()

    with Flow("story-processor") as flow:
        #flow.executor = LocalDaskExecutor(scheduler="threads", num_workers=6)  # execute `map` calls in parallel
        # read parameters
        stories_per_page = Parameter("stories_per_page", default=DEFAULT_STORIES_PER_PAGE)
        logger.info("    will request {} stories/page".format(stories_per_page))
        # 1. list all the project we need to work on
        projects_list = load_projects_task()
        # 2. process all the projects (in parallel)
        project_statuses = process_project_task.map(projects_list,
                                                    page_size=unmapped(stories_per_page))
        # 3. send email with results of operations
        send_email_task(project_statuses)

    # run the whole thing
    flow.run(parameters={
        'stories_per_page': DEFAULT_STORIES_PER_PAGE,
    })