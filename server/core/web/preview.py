import os, uuid, shutil, re

from core.csmc.server_preview import PreviewTask
from core.utils import const

from typing import Callable

from fastapi import Request, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, FileResponse

class PreviewPage():

	def __init__(self, template:Jinja2Templates, error_response:Callable):
		self.template = template
		self.error_response = error_response

	def show_form(self, request:Request):
		''' Show the form to upload a CSMC file for preview. '''
		return self.template.TemplateResponse(
			'preview.html',
			{ "request" : request }
		)
	
	def upload_form(self, request:Request, background_tasks:BackgroundTasks, files):
		''' Upload the csmc file and start preparation task. Redirect user to waiting page. '''

		# Make sure create path exists
		os.makedirs(const.PREVIEW_PATH, exist_ok=True)

		# Try to find filename
		filename = "No filename found"
		try:
			for file in files:
				filename = file.filename
				break
		except Exception as e:
			pass

		# Create task id and populate folders
		task_id = str(uuid.uuid4())
		task_dir = os.path.join(const.PREVIEW_PATH, task_id)

		if os.path.exists(task_dir):
			return self.template.TemplateResponse(
					'error.html',
					{ "request" : request,
	  					"url_valid": True,
						"fdr_file": filename,
						"error_messages": [{"msg":"Something went wrong. Please try again.", "additional":"Somehow an already given UUID has been reassigned"}]
					},
					status_code=400
				)
		
		if len(files) !=1:
			return self.template.TemplateResponse(
					'error.html',
					{ "request" : request,
	  					"url_valid": True,
						"fdr_file": filename,
						"error_messages": [{"msg":"Please upload only one file", "additional":"You uploaded "+str(len(files))+" files"}]
					},
					status_code=400
				)

		os.makedirs(task_dir, exist_ok=True)

		# Save the uploaded file
		try:
			for file in files:
				file_path = os.path.join(task_dir, file.filename)
				with open(file_path, "wb") as buffer:
					shutil.copyfileobj(file.file, buffer)
		except Exception as e:
			return self.template.TemplateResponse(
					'error.html',
					{ "request" : request,	
						"url_valid": True,
						"fdr_file": filename,
						"error_messages": [{"msg":"Could not upload the file.", "additional":str(e)}]
					},
					status_code=400
				)
		
		# Start the creation process
		task = PreviewTask(task_id)
		task.lock()
		background_tasks.add_task(task.run)
		return RedirectResponse(url=f"/preview/{task_id}", status_code=303)
	
	def show_status(self, request:Request, id:str):
		''' Show the current creation status or download page if finished. '''
		task = PreviewTask(id)

		if not task.exists():
			return self.error_response(request, "Not Found", 404)
		
		if task.has_error():
			message, additional = task.get_error()
			return self.template.TemplateResponse(
				'error.html',
				{ "request": request,
					"url_valid": True,
					"fdr_file": task.get_filename(),
					"error_messages": [{"msg":message, "additional":additional}]
				},
				status_code = 400
			)
		
		if task.is_running():
			return self.template.TemplateResponse(
				'waiting.html',
				{ "request": request,
					"fdr_file": task.get_filename(),
					"view_link": f"/preview/{id}"
				}
			)
		
		return RedirectResponse(url=f"/preview/{id}/index.html", status_code=303)
	
	def serve(self, request:Request, id:str, viewer_resource:str):
		''' Serve a viewer and its files. '''
		task = PreviewTask(id)
		if task.exists() and not task.is_running():
			if (
					not '..' in viewer_resource and
					not re.match(r'^[A-Za-z0-9\.\-\/\_]+$', viewer_resource) is None
				) and (
					viewer_resource in ('index.html', 'data.zip') or 
					viewer_resource.startswith(('raw/', 'static/'))
				):
					path = task.dir
					serve_file = os.path.join(path, viewer_resource)

					if os.path.isfile(serve_file) and os.path.realpath(serve_file).startswith(path):
						return FileResponse(serve_file)
					else:
						return self.error_response(request, "Not Found", 404)
			else:
				return self.error_response(request, "Not Allowed", 403)
		else:
			return RedirectResponse("/preview/"+id)