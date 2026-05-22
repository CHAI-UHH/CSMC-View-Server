import os

from core.utils import const
from core.csmc.file import CSMCFile
from core.utils.functions import fix_file_permissions

class PreviewTask():

	def __init__(self, task_id):
		"""
			Initialize the preview task.

			Args:
				- task_id: The task id
		"""
		self.id = task_id
		self.dir = os.path.join(const.PREVIEW_PATH, task_id)
		self.lockpath = os.path.join(self.dir, 'lock')
		self.errorpath = os.path.join(self.dir, 'error')

	def exists(self):
		""" Checks whether the task exists. """
		return os.path.isdir(self.dir)
	
	def get_filename(self):
		""" Returns the filename of the task. """
		filename = "No filename found"
		for file in os.listdir(self.dir):
			if file.endswith('.csmc'):
				filename = file
				break
		return filename
	
	def has_error(self):
		""" Checks whether the task has an error. """
		return os.path.isfile(self.errorpath)
	
	def get_error(self):
		""" Returns the error message of the task.
			Returns:
				- message: The error message
				- additional: Additional information about the error
		"""
		with open(self.errorpath, 'r') as f:
			message, additional = f.read().split('\n')
		return message, additional

	def lock(self):
		""" Create the lock file. """
		open(self.lockpath, 'w').close()
	
	def unlock(self):
		""" Remove the lock file. """
		os.remove(self.lockpath)
	
	def is_running(self):
		""" Checks whether this task is still running.
			Returns:
				True iff the task is running
		"""
		return os.path.isfile(self.lockpath)

	def _write_error(self, msg:str, data=None) -> None:
		""" Writes an error message to the error file.
			Args:
				- msg: The error message
				- data: Additional information
		"""
		with open(self.errorpath, 'w') as f:
			f.write(f"{msg}\n{str(data)}")

	def run(self):
		''' Extract the csmc file. '''

		filename = self.get_filename()
		if not filename.endswith('.csmc'):
			self._write_error("No csmc file found")
			self.unlock()
			return
		
		# Start the extraction process
		csmc = CSMCFile(os.path.join(self.dir, filename), self.dir)
		if csmc.unpack(self._write_error):
			# return value is true, so the extraction was successful
			# remove the error file, which may be created due to group names
			if os.path.isfile(self.errorpath):
				os.remove(self.errorpath)

		# update file permissions
		if not const.DEVMODE:
			fix_file_permissions(self.dir)

		self.unlock()