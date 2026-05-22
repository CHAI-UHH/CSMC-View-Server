# CSMC File Server -- FastAPI implementation
# 	(c) 2024 Magnus Bender
# 	Institute of Humanities-Centered Artificial Intelligence (CHAI), Universitaet Hamburg
# 		https://www.philosophie.uni-hamburg.de/chai/personen/bender.html
# 	All rights reserved!

import re, hashlib, os, json

from datetime import datetime
from typing import Union, List, Dict
from urllib.parse import urlparse

import requests
from fastapi import BackgroundTasks

from core.csmc.file import CSMCFile
from core.utils import const, logger, fix_file_permissions

class FDR():

	# the host names of RDRs that can be used to download CSMC files, this is used to validate the FDR urls
	ALLOWED_HOSTNAMES = const.ALLOWED_HOSTNAMES

	FDR_FILE_PATTERN = r'^\/record(s?)\/([A-Za-z\_\-0-9]+)\/files\/([A-Za-z\_\-0-9%\ \.]+)\.csmc$'
	FDR_FILE_FORMATTED = "{scheme}://{host}/record{s}/{id}/files/{name}.csmc?download=1"

	def __init__(self, fdr_url:str):
		"""
			Args:
				- fdr_url: The url to download the CSMC file from FDF.
		"""
		if not os.path.isdir(const.VIEWERS_PATH):
			os.makedirs(const.VIEWERS_PATH)
		
		self.fdr_url = fdr_url
		self._init_infos();

	def _init_infos(self):
		self.fdr_url_clean = self._validate_url(self.fdr_url)
		if self.fdr_url_clean == False:
			logger.info(f"Invalid FDR url found: {self.fdr_url}")
		else:
			self.viewer_id = self._hash_url(self.fdr_url_clean)
			self.viewer_path = os.path.join(const.VIEWERS_PATH, self.viewer_id)
			self.lock_file = os.path.join(self.viewer_path, 'lock')
			self.finished_file = os.path.join(self.viewer_path, 'ready')
			self.error_log_file = os.path.join(self.viewer_path, 'error.log')

	def _hash_url(self, url:str) -> str:
		return hashlib.sha1(str(url).encode('utf-8')).hexdigest()

	def make_available(self, background_tasks:BackgroundTasks=None) -> bool:
		"""
			Make this CSMC file available for viewing, this will download the file if not already downloaded.

			Args:
				- background_tasks (BackgroundTasks): if set, schedule download and extraction in background

			Returns:
				True if extracted or extraction started, False on error
		"""

		if self.fdr_url_clean == False:
			return False
		
		# check if folder exists
		if os.path.isdir(self.viewer_path):
			# True: its already downloaded and can be served from, OR
			#	its locked, and under processing
			# False: folder exists, but not locked and not finished -> error 
			return os.path.isfile(self.finished_file) or os.path.isfile(self.lock_file)
		else:
			# create the folder, download, and extract
			os.makedirs(self.viewer_path)
			open(self.lock_file, 'w').close()

			# schedule download and extract as background task, if available
			if background_tasks is None:
				return self._make_available_background()
			else:
				background_tasks.add_task(self._make_available_background)

				return True

	def _make_available_background(self):
		csmc_file = os.path.join(self.viewer_path, 'csmc.zip')

		if self._download_viewer(csmc_file):
			csmc = CSMCFile(csmc_file, self.viewer_path)
			
			if not csmc.unpack(self._log_viewer):
				os.remove(self.lock_file)
				return False
		else:
			os.remove(self.lock_file)
			return False

		# add finished file and remove lock
		open(self.finished_file, 'w').close()
		os.remove(self.lock_file)

		# update file permissions
		if not const.DEVMODE:
			fix_file_permissions(self.viewer_path)

		return True

	def is_available(self) -> bool:
		"""
			Check if this CSMC file is available for viewing
		"""
		return self.fdr_url_clean != False and os.path.isfile(self.finished_file)
	
	
	def is_error(self) -> bool:
		"""
			Check if there is an error with this CSMC file.
		"""
		return self.fdr_url_clean == False or (
			os.path.isdir(self.viewer_path) and not (
				os.path.isfile(self.finished_file) or os.path.isfile(self.lock_file)
			)
		)
	
	def url_valid(self) -> bool:
		"""
			Check if the fdr_url is valid.
		"""
		return self.fdr_url_clean != False
	
	def get_path(self) -> str:
		"""
			Get the path, where the viewer is download to.
		"""
		return self.viewer_path

	def _log_viewer(self, msg:str, data=None) -> None:
		with open(self.error_log_file, 'a+') as f:
			f.write(json.dumps({
					"date" : str(datetime.now()),
					"msg" : msg,
					"data" : data
				}) + "\n"
			)

	def get_error_messages(self) -> List[Dict[str, str]]:
		if self.fdr_url_clean == False:
			return [{"msg":"Invalid URL"}]
		else:
			if os.path.isfile(self.error_log_file):

				errors = []
				with open(self.error_log_file, 'r') as f:
					for l in f:
						errors.append(json.loads(l))
				return errors
			
			else:
				return [{"msg":"Unknown"}]
	
	def get_raw_info(self) -> List[str]:
		""" Returns the list of top 20 filenames inside the 'raw' directory """
		raw_info_file = os.path.join(self.viewer_path, 'raw.json')
		if os.path.isfile(raw_info_file):
			with open(raw_info_file, 'r', encoding="utf-8") as f:
				return json.load(f)
		else:
			return []

	def _download_viewer(self, zip_path:str ) -> bool:
		try:
			with requests.get(self.fdr_url, stream=True) as r:
				if r.status_code != 200:
					logger.info(f"CSMC download got status code != 200: {self.fdr_url}")
					self._log_viewer('CSMC download got status code != 200', data=self.fdr_url)
					return False
			
				with open(zip_path, 'w+b') as t:
					for chunk in r.iter_content(chunk_size=1024*1024):
						if chunk:
							t.write(chunk)
		except Exception as e:
			logger.info(f"Error downloading CSMC file: {self.fdr_url} ({e})")
			self._log_viewer('Error downloading CSMC file', data=[self.fdr_url, str(e)])
			return False

		return True

	def _validate_url(self, url:str) -> Union[bool, str]:
		if const.DEVMODE:
			return url
		
		try:
			url = urlparse(url.strip(), scheme='', allow_fragments=True)
		except:
			return False

		if url.scheme not in ['http', 'https']:
			return False

		if url.hostname not in self.ALLOWED_HOSTNAMES:
			return False

		path = re.match(self.FDR_FILE_PATTERN, url.path)
		if not path:
			return False

		return self.FDR_FILE_FORMATTED.format(
			scheme=url.scheme, host=url.hostname, s=path.group(1), id=path.group(2), name=path.group(3)
		)
