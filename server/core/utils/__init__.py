# CSMC File Server -- FastAPI implementation
# 	(c) 2024 Magnus Bender
# 	Institute of Humanities-Centered Artificial Intelligence (CHAI), Universitaet Hamburg
# 		https://www.philosophie.uni-hamburg.de/chai/personen/bender.html
# 	released under the terms of GNU Public License Version 3
#     https://www.gnu.org/licenses/gpl-3.0.txt

import core.utils.const as const 

import logging
logging.basicConfig(
	handlers=[
		logging.FileHandler(const.LOG_FILE),
		logging.StreamHandler()
	],
	level=const.LOG_LEVEL,
	format='%(asctime)s %(levelname)s %(name)s: %(message)s',
	datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('CSMC Viewer')

from core.utils.functions import *