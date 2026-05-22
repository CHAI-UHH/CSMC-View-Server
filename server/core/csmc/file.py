# CSMC File Server -- FastAPI implementation
# 	(c) 2024 Magnus Bender
# 	Institute of Humanities-Centered Artificial Intelligence (CHAI), Universitaet Hamburg
# 		https://www.philosophie.uni-hamburg.de/chai/personen/bender.html
# 	released under the terms of GNU Public License Version 3
#     https://www.gnu.org/licenses/gpl-3.0.txt

import os
import json

from zipfile import ZipFile, BadZipFile, LargeZipFile, ZIP_DEFLATED
from typing import Callable, List, Dict

from core.csmc.prepare_index import PrepareIndex
from core.utils import logger

class CSMCFile():

	# max show 50 elements in preview of raw files
	TRUNCATE_NAMES = 50
	# show 2 files before ... symbolize similar names
	SHOW_SAME_PREFIX = 2
	# max length of prefixes
	PREFIX_LENGTH = 5

	def __init__(self, file_path:str, viewer_path:str):
		self.file_path = file_path
		self.viewer_path = viewer_path

	def unpack(self, log_viewer:Callable) -> bool:
		# check zip
		if not self._validate_file(self.file_path, log_viewer):
			logger.info(f"Invalid CSMC file: {self.viewer_path}")
			log_viewer('Invalid CMSC file')
			return False

		# extract zip
		try:
			with ZipFile(self.file_path, 'r') as zip_ref:
				zip_ref.extractall(self.viewer_path)

		except Exception as e:
			logger.info(f"Unable to extract zip: {self.file_path} ({e})")
			log_viewer("Unable to extract zip", data=str(e))
			return False
		
		# os.remove(self.file_path)
		
		# zip the raw data (for extract data download) and prepare raw.json info file
		try:
			# Zip all files in the extracted 'raw' directory
			raw_dir = os.path.join(self.viewer_path, 'raw')
			raw_info = []
			if os.path.exists(raw_dir):
				zip_path = os.path.join(self.viewer_path, "data.zip")
				with ZipFile(
						zip_path,
						mode='w',
						compression=ZIP_DEFLATED,
					) as zip_ref:
					for path, _, files in os.walk(raw_dir):
						for i, f in enumerate(files):
							zip_ref.write(
								os.path.join(path, f),
								os.path.relpath(
									os.path.join(path, f),
									start=raw_dir
								)
							)
							raw_info.append(f)

				with open(os.path.join(self.viewer_path, 'raw.json'), 'w', encoding="utf-8") as f:
					try:
						names = self._group_names(raw_info)
					except:
						logger.debug(f"Error with _group_names(): {self.file_path}")
						log_viewer("Error with _group_names()")
						names = raw_info[:self.TRUNCATE_NAMES]

					json.dump(names, f)
			else:
				logger.debug(f"No raw data folder in CSMC file: {self.file_path}")
				log_viewer("No raw data folder in CSMC file")

		except Exception as e:
			logger.error(f"Unable to zip raw data: {self.file_path} ({e})")
			log_viewer("Unable to zip raw data", data=str(e))
			return False
		
		try:
			PrepareIndex(os.path.join(self.viewer_path, 'index.html'))
		except Exception as e:
			logger.error(f"Unable to brand: {self.file_path} ({e})")
			log_viewer("Unable to brand", data=str(e))
			# not error here, cause viewer may work without branding

		return True

	def _validate_file(self, file_path:str, log_viewer:Callable=None):
		if log_viewer is None:
			log_viewer = lambda x,data=None:x;
		
		try:
			with ZipFile(file_path, mode='r') as z:
				if z.testzip() != None:
					log_viewer("CSMC file is not a zip archive")
					return False

				isIndex = False
				isStatic = False
				isRaw = False

				containsIndex = False
				size = 0
				for f in z.infolist():
					size += f.file_size

					if ".." in f.filename:
						log_viewer("CSMC file contains file with '..' in name")
						return False

					if not f.is_dir() and f.filename == 'index.html':
						containsIndex = True
						isIndex = True
					else:
						if f.filename.startswith('static/'):
							isStatic = True
						elif f.filename.startswith('raw/'):
							isRaw = True
					
					if not isIndex and not isStatic and not isRaw:
						log_viewer("CSMC file contains items which are not index, raw, or static")
						return False

			if not containsIndex:
				log_viewer("Did not find index of CSMC file")
				return False

			if size > 500 * 1024 * 1024: # limit size to 500 MB
				log_viewer("CSMC file is to large (limit 500 MB)")
				return False

		except BadZipFile as e:
			logger.error(f"BadZipFile: {file_path} ({e})")
			log_viewer("BadZipFile", data=str(e))
			return False
		except LargeZipFile:
			logger.error(f"LargeZipFile: {file_path} ({e})")
			log_viewer("LargeZipFile", data=str(e))
			return False
		except Exception as e:
			logger.error(f"Validate File Error: {file_path} ({e})")
			log_viewer("Validate File Error", data=str(e))
			return False

		return True
	
	def _group_names(self, names:List[str]):	
		names.sort()

		def trie(words:List[str]) -> Dict:
			# https://stackoverflow.com/a/11016430
			root = dict()
			for word in words:
				current_dict = root
				for letter in word:
					current_dict = current_dict.setdefault(letter, {})
				current_dict[''] = ''
			return root

		def trie2patricia(trie:Dict) -> Dict:
			prefix, sub_trie = '', trie
			while len(sub_trie) == 1:
				key = next(iter(sub_trie))

				prefix += key
				sub_trie = sub_trie[key]

			if isinstance(sub_trie, str):
				return prefix
			
			rest = {
				k : trie2patricia(v)
					for k,v in sub_trie.items()
			} if len(sub_trie) > 0 else {'':''}
			return rest if len(prefix) == 0 else {prefix : rest}
		
		def names4trie(p_trie:Dict, name_prefix:str=''):
			for k,v in p_trie.items():
				if isinstance(v, str):
					yield name_prefix+k, name_prefix+k+v
				else:
					yield name_prefix+k, None
					yield from names4trie(v, name_prefix+k)

		p_trie = trie2patricia(trie(names))

		truncated = []
		current_prefix, with_current_prefix = '', 0
		last_with_prefix = None
		for prefix, name in names4trie(p_trie):
			prefix = prefix[:self.PREFIX_LENGTH]

			if current_prefix != prefix:
				if not last_with_prefix is None and with_current_prefix > self.SHOW_SAME_PREFIX:
					truncated.append('...')
					truncated.append(last_with_prefix)

				current_prefix, with_current_prefix = prefix, 0

			if prefix == current_prefix and not name is None:
				if with_current_prefix < self.SHOW_SAME_PREFIX:
					truncated.append(name)

				last_with_prefix = name
				with_current_prefix += 1

		if not last_with_prefix is None and with_current_prefix > self.SHOW_SAME_PREFIX:
			truncated.append('...')
			truncated.append(last_with_prefix)

		return truncated if len(truncated) <= self.TRUNCATE_NAMES \
			else (truncated[:self.TRUNCATE_NAMES] + ['... ...'])