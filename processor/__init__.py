import os
import logging
import sys
from dotenv import load_dotenv
import mediacloud.api
from flask import Flask
#from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.logging import ignore_logger
from sentry_sdk import init
from typing import Dict
from sqlalchemy import create_engine

VERSION = "3.0.10"
SOURCE_GOOGLE_ALERTS = "google-alerts"
SOURCE_MEDIA_CLOUD = "media-cloud"
SOURCE_NEWSCATCHER = "newscatcher"
SOURCE_WAYBACK_MACHINE = "wayback-machine"
PLATFORMS = [SOURCE_GOOGLE_ALERTS, SOURCE_MEDIA_CLOUD, SOURCE_NEWSCATCHER, SOURCE_WAYBACK_MACHINE]

load_dotenv()  # load config from .env file (local) or env vars (production)

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path_to_log_dir = os.path.join(base_dir, 'logs')

# set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(name)s | %(message)s')
logger = logging.getLogger(__name__)
logger.info("------------------------------------------------------------------------")
logger.info("Starting up Feminicide Story Processor v{}".format(VERSION))
# supress annoying "not enough comments" and "using custom extraction" notes# logger = logging.getLogger(__name__)
loggers_to_skip = ['trafilatura.core', 'trafilatura.metadata', 'readability.readability']
for item in loggers_to_skip:
    logging.getLogger(item).setLevel(logging.WARNING)

# read in environment variables
MC_API_TOKEN = os.environ.get('MC_API_TOKEN', None)  # sensitive, so don't log it
if MC_API_TOKEN is None:
    logger.error("  No MC_API_TOKEN env var specified. Pathetically refusing to start!")
    sys.exit(1)

BROKER_URL = os.environ.get('BROKER_URL', None)
if BROKER_URL is None:
    logger.error("No BROKER_URL env var specified. Pathetically refusing to start!")
    sys.exit(1)
logger.info("  Queue at {}".format(BROKER_URL))

SENTRY_DSN = os.environ.get('SENTRY_DSN', None)  # optional
if SENTRY_DSN:
    init(dsn=SENTRY_DSN, release=VERSION,
         integrations=[CeleryIntegration()])
    ignore_logger('trafilatura.utils')
    logger.info("  SENTRY_DSN: {}".format(SENTRY_DSN))
else:
    logger.info("  Not logging errors to Sentry")

FEMINICIDE_API_URL = os.environ.get('FEMINICIDE_API_URL', None)
if FEMINICIDE_API_URL is None:
    logger.error("  No FEMINICIDE_API_URL is specified. Bailing because we can't list projects to run!")
    sys.exit(1)
else:
    logger.info("  Config server at at {}".format(FEMINICIDE_API_URL))

FEMINICIDE_API_KEY = os.environ.get('FEMINICIDE_API_KEY', None)
if FEMINICIDE_API_KEY is None:
    logger.error("  No FEMINICIDE_API_KEY is specified. Bailing because we can't send things to the main server without one")
    sys.exit(1)

SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
if SQLALCHEMY_DATABASE_URI is None:
    logger.error("  No SQLALCHEMY_DATABASE_URI is specified. Bailing because we can't save things to a DB for tracking")
    sys.exit(1)
engine = create_engine(SQLALCHEMY_DATABASE_URI, pool_size=20, max_overflow=20) # bumped pool size up for parallel tasks


ENTITY_SERVER_URL = os.environ['ENTITY_SERVER_URL']
if ENTITY_SERVER_URL is None:
    logger.info("  No ENTITY_SERVER_URL is specified. You won't get entities in the stories sent to the  main server.")


NEWSCATCHER_API_KEY = os.environ['NEWSCATCHER_API_KEY']
if NEWSCATCHER_API_KEY is None:
    logger.info("  No NEWSCATCHER_API_KEY is specified. We won't be fetching from Newscatcher.")


def get_mc_client() -> mediacloud.api.DirectoryApi:
    """
    A central place to get the Media Cloud client
    :return: an admin media cloud client with the API key from the environment variable
    """
    return mediacloud.api.DirectoryApi(MC_API_TOKEN)


def create_flask_app() -> Flask:
    """
    Create and configure the Flask app. Standard practice is to do this in a factory method like this.
    :return: a fully configured Flask web app
    """
    return Flask(__name__)


def is_email_configured() -> bool:
    return (os.environ.get('SMTP_USER_NAME', None) is not None) and \
            (os.environ.get('SMTP_PASSWORD', None) is not None) and \
            (os.environ.get('SMTP_ADDRESS', None) is not None) and \
            (os.environ.get('SMTP_PORT', None) is not None) and \
            (os.environ.get('SMTP_FROM', None) is not None) and \
            (os.environ.get('NOTIFY_EMAILS', None) is not None)


def get_email_config() -> Dict:
    return dict(
        user_name=os.environ.get('SMTP_USER_NAME', None),
        password=os.environ.get('SMTP_PASSWORD', None),
        address=os.environ.get('SMTP_ADDRESS', None),
        port=os.environ.get('SMTP_PORT', None),
        from_address=os.environ.get('SMTP_FROM', None),
        notify_emails=os.environ.get('NOTIFY_EMAILS', "").split(",")
    )
