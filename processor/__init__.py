import os
import logging
import sys
from dotenv import load_dotenv
import mediacloud.api
from flask import Flask
from sentry_sdk import init, capture_message

load_dotenv()  # load config from .env file (local) or env vars (production)

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s | %(levelname)s | %(name)s | %(message)s')
logger = logging.getLogger(__name__)
logger.info("------------------------------------------------------------------------")
logger.info("Starting up Feminicide MC Story Processor")

# read in environment variables
MC_API_KEY = os.environ.get('MC_API_KEY', None)  # sensitive, so don't log it
if MC_API_KEY is None:
    logger.error("No MC_API_KEY env var specified. Pathetically refusing to start!")
    sys.exit(1)

BROKER_URL = os.environ.get('BROKER_URL', None)
if BROKER_URL is None:
    logger.error("No BROKER_URL env var specified. Pathetically refusing to start!")
    sys.exit(1)
logger.info("BROKER_URL: {}".format(BROKER_URL))

SENTRY_DSN = os.environ.get('SENTRY_DSN', None)  # optional
if SENTRY_DSN:
    init(dsn=SENTRY_DSN)
    capture_message("Initializing")
    logger.info("SENTRY_DSN: {}".format(SENTRY_DSN))
else:
    logger.info("Not logging errors to Sentry")


def get_mc_client():
    """
    A central place to get the Media Cloud client
    :return: an admin media cloud client with the API key from the environment variable
    """
    mc = mediacloud.api.AdminMediaCloud(MC_API_KEY)
    return mc


def create_flask_app():
    """
    Create and configure the Flask app. Standard practice is to do this in a factory method like this.
    :return: a fully configured Flask web app
    """
    # Factory method to create the app
    my_app = Flask(__name__)
    return my_app
