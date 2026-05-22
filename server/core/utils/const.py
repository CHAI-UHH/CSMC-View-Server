# CSMC File Server -- FastAPI implementation
# 	(c) 2024 Magnus Bender
# 	Institute of Humanities-Centered Artificial Intelligence (CHAI), Universitaet Hamburg
# 		https://www.philosophie.uni-hamburg.de/chai/personen/bender.html
# 	All rights reserved!

import os, time, logging

DEVMODE = os.environ.get("DEVMODE", "false").lower() == "true"
VERSION = "0.1.10" if not DEVMODE else str(int(time.time()))

SERVER_PATH = os.environ.get("SERVER_PATH", "http://127.0.0.1:8000")
SERVE_STATIC_NGINX = False 

IMPRINT_URL = os.environ.get("IMPRINT_URL", "https://www.fdr.example.com/imprint")
PRIVACY_POLICY_URL = os.environ.get("PRIVACY_POLICY_URL", "https://www.fdr.example.com/privacy-policy")
ALLOWED_HOSTNAMES = os.environ.get("ALLOWED_HOSTNAMES", "rdr.example.com").split(",")

CONTACT_NAME = os.environ.get("CONTACT_NAME", "Contact Name Missing")
CONTACT_MAIL = os.environ.get("CONTACT_MAIL", "mail@example.com")

BASE_PATH = os.path.realpath(os.path.join(
				os.path.dirname(os.path.realpath(__file__)), # the path of this folder congaing const.py
				'..', '..' # go to server's root
			))
DATA_PATH = os.path.join(BASE_PATH, 'data')
VIEWERS_PATH = os.path.join(BASE_PATH, 'data', 'viewers')
CREATE_PATH = os.path.join(BASE_PATH, 'data', 'create')
PREVIEW_PATH = os.path.join(BASE_PATH, 'data', 'preview')

CREATE_ADDITIONAL_PATH = os.path.join(BASE_PATH, 'create_additional_files')

os.makedirs(DATA_PATH, exist_ok=True) # assure data path

FILES_OWN_USER_GROUP = ('user', 'user')

LOG_FILE = os.path.join(DATA_PATH, 'csmc.log')
LOG_LEVEL = logging.INFO

RUNNING_AS_WEB = False
RUNNING_AS_CLI = False