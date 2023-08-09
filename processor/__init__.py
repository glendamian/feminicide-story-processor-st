import os
import logging
import sys
from dotenv import load_dotenv
from sentry_sdk import init

VERSION = "0.0.1"
#SOURCE_GOOGLE_ALERTS = "google-alerts"
SOURCE_MEDIA_CLOUD = "media-cloud"
SOURCE_NEWSCATCHER = "newscatcher"
SOURCE_WAYBACK_MACHINE = "wayback-machine"
PLATFORMS = [SOURCE_MEDIA_CLOUD, SOURCE_NEWSCATCHER, SOURCE_WAYBACK_MACHINE]

load_dotenv()  # load config from .env file (local) or env vars (production)

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(base_dir, "config")

# set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(name)s | %(message)s')
logger = logging.getLogger(__name__)
logger.info("------------------------------------------------------------------------")
logger.info("Starting up Feminicide Dashboard v{}".format(VERSION))

SENTRY_DSN = os.environ.get('SENTRY_DSN', None)  # optional
if SENTRY_DSN:
    init(dsn=SENTRY_DSN, release=VERSION)
    logger.info("  SENTRY_DSN: {}".format(SENTRY_DSN))
else:
    logger.info("  Not logging errors to Sentry")

FEMINICIDE_API_URL = os.environ.get('FEMINICIDE_API_URL', None)
if FEMINICIDE_API_URL is None:
    logger.error("  ❌ No FEMINICIDE_API_URL is specified. Bailing because we can't list projects to run!")
    sys.exit(1)
else:
    logger.info("  Config server at at {}".format(FEMINICIDE_API_URL))

FEMINICIDE_API_KEY = os.environ.get('FEMINICIDE_API_KEY', None)
if FEMINICIDE_API_KEY is None:
    logger.error("  ❌ No FEMINICIDE_API_KEY is specified. Bailing because we can't send things to the main server without one")
    sys.exit(1)

PROCESSOR_DB_URI = os.environ.get('PROCESSOR_DB_URI', None)
if PROCESSOR_DB_URI is None:
    logger.warning("  ❌ ️No PROCESSOR_DB_URI is specified")
    sys.exit(1)

"""
ALERTS_DB_URI = os.environ.get('ALERTS_DB_URI', None)
if ALERTS_DB_URI is None:
    logger.warning("  ❌ ️No ALERTS_DB_URI is specified")
    sys.exit(1)
"""