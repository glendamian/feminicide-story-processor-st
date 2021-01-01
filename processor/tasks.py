from celery.utils.log import get_task_logger
import requests

from processor.celery import app
import processor.monitors as monitors

logger = get_task_logger(__name__)


@app.task(serializer='json', bind=True)
def classify_stories_worker(job):
    """
    Take a page of stories matching a monitor and run them through the classifier for that monitor.
    :param job: dict with 'stories' array and 'monitor' dict
    """
    try:
        logger.debug('{}: Received {} stories'.format(job['monitor']['id'], len(job['stories'])))
        model = monitors.classifier(job['monitor'])
        for s in job['stories']:
            results = model.check(s)
            s['model_results'] = results
        post_results_worker.delay(dict(
          stories=job['stories'],
          monitor=job['monitor']
        ))
    except Exception as exc:
        # only failure here is the classifer not loading? either way we should try again
        logger.warn("{}: Failed to label {} stories".format(job['monitor']['id'], len(job['stories'])))
        logger.exception(exc)
        raise self.retry(exc=exc)


@app.task(serializer='json', bind=True)
def post_results_worker(job):
    """
    Take a set of classified stories and post the results back to the feminicide server
    :param job:
    """
    try:
        monitors.post_results(job['monitor']['url'], job['stories'])
    except requests.exceptions.HTTPError as err:
        # on failure requeue to try again
        logger.warn("{}: Failed to post {} results".format(job['monitor']['id'], len(job['stories'])))
        logger.exception(err)
        raise self.retry(exc=err)
