import re, os

from typing import Callable

from fastapi import Request, BackgroundTasks
from fastapi.responses import RedirectResponse, FileResponse, Response
from fastapi.templating import Jinja2Templates

from core.utils import const

import uuid
import shutil

from core.csmc.create.EXAMPLE.EXAMPLE_creator import EXAMPLECreationTask

class EXAMPLECreatorPage():
	
	def __init__(self, template:Jinja2Templates):
		self.template = template

	def show_form(self, request:Request):
		''' Show the form to create an EXAMPLE CSMC File. '''
		return self.template.TemplateResponse(
			'create/EXAMPLE/form.html',
			{ "request" : request }
		)
	
	def upload_form(self, request:Request, background_tasks:BackgroundTasks, files):
		''' Upload the files and start the creation process. Redirect user to waiting page. '''

		# Make sure create path exists
		os.makedirs(const.CREATE_PATH, exist_ok=True)

		# Create task id and populate folders
		task_id = str(uuid.uuid4())
		task_dir = os.path.join(const.CREATE_PATH, task_id)

		if os.path.exists(task_dir):
			return self.template.TemplateResponse(
					'create/EXAMPLE/error.html',
					{ "request" : request,	
						"message" : "Something went wrong. Please try again.",
						"additional": "Somehow an already given UUID has been reassigned"
					},
					status_code=400
				)

		os.makedirs(task_dir, exist_ok=True)
		task_dir_raw = os.path.join(task_dir, 'raw')
		os.makedirs(task_dir_raw, exist_ok=True)

		# Save the uploaded files to raw directory
		try:
			for file in files:
				file_path = os.path.join(task_dir_raw, file.filename)
				with open(file_path, "wb") as buffer:
					shutil.copyfileobj(file.file, buffer)
		except Exception as e:
			return self.template.TemplateResponse(
					'create/EXAMPLE/error.html',
					{ "request" : request,	
						"message" : "Could not upload the files.",
						"additional": str(e)
					},
					status_code=400
				)
		
		# Start the creation process
		task = EXAMPLECreationTask(task_id)
		task.lock()
		background_tasks.add_task(task.run)
		return RedirectResponse(url=f"/create/EXAMPLE/{task_id}", status_code=303)

	def show_status(self, request:Request, id:str):
		''' Show the current creation status or download page if finished. '''
		task = EXAMPLECreationTask(id)

		if not task.exists():
			return self.template.TemplateResponse(
				'create/EXAMPLE/error.html',
				{ "request": request,
					"message": "Task not found",
					"additional": "The task you are looking for does not exist"
				},
				status_code = 404
			)
		
		if task.has_error():
			message, additional = task.get_error()
			return self.template.TemplateResponse(
				'create/EXAMPLE/error.html',
				{ "request": request,
					"message": message,
					"additional": additional
				},
				status_code = 500
			)

		if task.is_running():
			step, progress = task.get_progress()
			return self.template.TemplateResponse(
				'create/EXAMPLE/waiting.html',
				{ "request": request,
	 				"step": step,
					"progress": progress
				},
				status_code = 200
			)
		else:
			return self.template.TemplateResponse(
				'create/EXAMPLE/download.html',
				{ "request": request,
	 				"task_id": id
				},
				status_code = 200
			)
	
	def download(self, request:Request, id:str):
		''' Download the EXAMPLE CSMC file. '''
		task = EXAMPLECreationTask(id)

		if task.is_finished():
			return FileResponse(os.path.join(task.dir, 'EXAMPLE.csmc'))
		else:
			return self.template.TemplateResponse(
				'create/EXAMPLE/error.html',
				{ "request": request,
					"message": "Requested archive not found",
					"additional": "The task may not be finished yet or you submitted an invalid task id"
				},
				status_code = 404
			)