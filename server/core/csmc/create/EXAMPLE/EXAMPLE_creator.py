import csv
import time
import os
import shutil
import uuid
import zipfile

from jinja2 import Environment, FileSystemLoader, select_autoescape
from core.utils import const

import re
from urllib.parse import urlparse
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from html.parser import HTMLParser
import csv
import tempfile
import os
import subprocess

class EXAMPLECreationTask:
	def __init__(self, id:str):
		"""
			Initialize the EXAMPLE creation task.

			Args:
				- id: The task id
		"""
		self.id = id
		self.dir = os.path.join(const.CREATE_PATH, id)
		self.lockpath = os.path.join(self.dir, 'lock')
		self.progresspath = os.path.join(self.dir, 'progress')
		self.errorpath = os.path.join(self.dir, 'error')
	
	def exists(self):
		""" Checks whether the task exists. """
		return os.path.isdir(self.dir)

	def lock(self):
		""" Create the lock and progress files. """
		open(self.lockpath, 'w').close()
		with open(self.progresspath, 'w') as f:
			f.write('0\n0')
	
	def unlock(self):
		""" Remove the lock file. """
		os.remove(self.lockpath)
		os.remove(self.progresspath)
	
	def is_running(self):
		""" Checks whether this task is still running.
			Returns:
				True iff the task is running
		"""
		return os.path.isfile(self.lockpath)

	def is_finished(self):
		""" Checks whether the task is finished.
			Returns:
				True iff the task is finished
		"""
		return os.path.isfile(os.path.join(self.dir, 'EXAMPLE.csmc'))

	def get_progress(self):
		""" Returns the progress of the task.
			Returns:
			- step: The current step number the task is in
			- progress: The progression percentage between 0 and 100 of the current step

			Returns (-1,-1) if task is not running or progress file is corrupted
		"""
		if not self.is_running():
			return -1, -1
		
		try:
			with open(self.progresspath, 'r') as f:
				step, progress = f.read().split('\n')
				return int(step), int(progress)
		except:
			return -1, -1

	def _write_error(self, message:str, additional:str):
		""" Writes an error message to the error file.
			Args:
				- message: The error message
				- additional: Additional information
		"""
		with open(self.errorpath, 'w') as f:
			f.write(f"{message}\n{additional}")
	
	def has_error(self):
		""" Checks whether an error occurred.
			Returns:
				True iff an error occurred
		"""
		return os.path.isfile(self.errorpath)

	def get_error(self):
		""" Returns the error message and additional information.
			Returns:
				- message: The error message
				- additional: Additional information
		"""
		if not os.path.isfile(self.errorpath):
			return None, None
		
		with open(self.errorpath, 'r') as f:
			message, additional = f.read().split('\n')
			return message, additional

	def _write_status(self, step, progress):
		""" Writes the current status to the progress file. """
		with open(self.progresspath, 'w') as f:
			f.write(f"{step}\n{progress}")

	def run(self):
		""" 
			Runs the creation task. It consists of three steps:
				1. Configurate viewer
				2. Copy viewer
				3. Create zip file
		"""

		# Step 1: Configurate viewer
		self._write_status(1, 0)
		try:
			self._configurate_viewer()
		except Exception as e:
			self._write_error('Error during configurating viewer', str(e))
			return
		self._write_status(1, 100)

		# Step 2: Copy viewer
		self._write_status(2, 0)
		try:
			self._copy_viewer()
		except Exception as e:
			self._write_error('Error during copying viewer', str(e))
			return
		self._write_status(2, 100)

		# Step 3: Create zip file
		self._write_status(3, 0)
		try:
			self._zip_files()
		except Exception as e:
			self._write_error('Error during zipping files', str(e))
			return
		self._write_status(3, 100)

		# Finish
		self.unlock()

	def _configurate_viewer(self):
		""" Configurates the viewer. """
		
		# At the moment, only one csv file is supported
		# Check if there is exactly one csv file in the raw directory
		csv_files = [f for f in os.listdir(os.path.join(self.dir, 'raw')) if f.endswith('.csv')]
		if len(csv_files) != 1:
			self._write_error('Error during zipping files', 'There must be exactly one csv file')
			return
		
		# Rename the csv file to EXAMPLE.csv
		csv_file = csv_files[0]
		csv_path = os.path.join(self.dir, 'raw', csv_file)
		new_csv_path = os.path.join(self.dir, 'raw', 'input_html.csv')
		os.rename(csv_path, new_csv_path)

		# Copy viewer config
		env = Environment(
			loader=FileSystemLoader(os.path.join(const.CREATE_ADDITIONAL_PATH, 'EXAMPLE', 'viewer')),
			autoescape=select_autoescape(['js'])
		)
		viewer_template = env.get_template('viewer_config.js')
		viewer_config = viewer_template.render(
			uuid = uuid.uuid4()
		)
		with open(os.path.join(self.dir, "raw", 'viewer_config.js'), 'w') as f:
			f.write(viewer_config)

	def _copy_viewer(self):
		""" Copies the viewer to the task directory. """
		viewer_path = os.path.join(const.CREATE_ADDITIONAL_PATH, 'EXAMPLE', 'viewer', 'empty.csmc')
		shutil.copy(viewer_path, os.path.join(self.dir, 'EXAMPLE.csmc'))	
	
	def _zip_files(self):
		""" Zips the files in the task directory as csmc file. """

		# Create the archive file name
		archive_path = os.path.join(self.dir, "EXAMPLE.csmc")

		# Count files in raw directory
		file_count = 0
		for root, _, files in os.walk(os.path.join(self.dir, 'raw')):
			file_count += len(files)

		# Copy to csmc file
		with zipfile.ZipFile(archive_path, 'a') as zip_ref:
			file_index = 0
			for root, _, files in os.walk(os.path.join(self.dir, 'raw')):
				for file in files:
					file_path = os.path.join(root, file)
					# Preserve the folder structure within 'raw'
					arcname = os.path.relpath(file_path, self.dir)
					zip_ref.write(file_path, arcname=arcname)
					file_index += 1
					self._write_status(3, int((file_index / file_count) * 100))
