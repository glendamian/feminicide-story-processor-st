Feminicide Story Dashboard
==========================

Investigate how stories have moved through the feminucides story detection pipeline. Part of the [Data Against 
Feminicide project](http://datoscontrafeminicidio.net/).

Install for Development
-----------------------

1. Install Python v3.10.0 or higher (we typically use conda or pyenv for this)
2. Install Python requirements: `pip install -r requirements.txt`
3. cp .env.template .env` and fill in the appropriate info for each setting in that file

Running
-------

From the command line run `run-dashboard.sh` to start up the web server. Then visit localhost:8000 to see it.

Deploying
---------

To build a release:

1. Edit `processor.VERSION` based on semantic versioning norms
2. Update the `CHANGELOG.md` file with a note about what changed
3. Commit those changes and tag the repo with the version number from step 1

This is built to deploy via a SAAS platform, like Heroku. We deploy via [dokku](https://dokku.com). Whatever your deploy
platform, make sure to create environment variables there for each setting in the `.env.template`.
