import os
import logging
from dotenv import load_dotenv
import mediacloud.api
from flask import Flask

load_dotenv()  # load config from .env file (local) or env vars (production)

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(name)s | %(message)s')
logger = logging.getLogger(__name__)
logger.info("------------------------------------------------------------------------")
logger.info("Starting up Feminicide MC Story Processor")

# read in environment variables
MC_API_KEY = os.environ['MC_API_KEY'] # sensitive, so don't log it
BROKER_URL = os.environ['BROKER_URL']
logger.info("BROKER_URL: {}".format(BROKER_URL))


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
