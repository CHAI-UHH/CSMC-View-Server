# CSMC File Server -- FastAPI implementation
# 	(c) 2024 Magnus Bender
# 	Institute of Humanities-Centered Artificial Intelligence (CHAI), Universitaet Hamburg
# 		https://www.philosophie.uni-hamburg.de/chai/personen/bender.html
# 	All rights reserved!

import re, os, time, shutil, sys

from typing import Callable

from core.utils import const, logger

class CleanUp():

	DAY_SECONDS = 24 * 60 * 60
	LAX_AGE_DAYS = 14 # max age days, if enough disk space
	STRICT_AGE_DAYS = 1 # max age days, if not much disk space

	STRICT_PERCENTAGE_USED = 90 # strict mode if more than this % used
	STRICT_SPACE_FREE = 2 # strict mode if less than this GB free

	CLEANUP_PATHS = [
		const.VIEWERS_PATH,
		const.CREATE_PATH,
		const.PREVIEW_PATH
	]
	CLEANUP_PATHS_CONDITION = [
		lambda name: re.match('^[0-9a-f]{40}$', name),
		lambda _: True,
		lambda _: True
	]

	def __init__(self):
		if not os.path.exists(const.DATA_PATH):
			os.makedirs(const.DATA_PATH)
		
		for p in self.CLEANUP_PATHS:
			if not os.path.isdir(p):
				os.makedirs(p)

	def run(self, remove_all:bool=False):
		for i, p in enumerate(self.CLEANUP_PATHS):
			self._run_path(p, self.CLEANUP_PATHS_CONDITION[i], remove_all)

		logger.info(f"Finished cleanup task (remove all={remove_all})")

	def _run_path(self, path:str, condition:Callable, remove_all:bool):
		total, used, free = shutil.disk_usage(path)
		current_time = int(time.time())
		delete_before = current_time - (
			(
				self.STRICT_AGE_DAYS if 
					# percentage of used disk more than STRICT_PERCENTAGE_USED
					int((used/total)*100) >= self.STRICT_PERCENTAGE_USED or
					# free (bytes) less than STRICT_SPACE_FREE GB
					free < self.STRICT_SPACE_FREE * 1_000_000_000
				else self.LAX_AGE_DAYS
			) * self.DAY_SECONDS
		)

		for f in os.scandir(path):
			# only folders with sha1 hashes as names
			if f.is_dir() and condition(f.name):
				last_modified = int(f.stat().st_mtime)

				if remove_all or last_modified <= delete_before:
					print("\tRemove the stale item:", path[-20:], f.name)
					self._remove(f.path)

	def _remove(self, path:str):
		# onexc in Python Version >= 3.12, else onerror
		kw = 'onexc' if sys.version_info.major == 3 and sys.version_info.minor >= 12 else 'onerror'
		
		shutil.rmtree(path, **{
			kw : lambda _, path, ex: logger.error(f"Error deleting file on cleanup (path={path}, ex={ex})")
		})
		
		
