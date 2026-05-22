# CSMC File Server -- FastAPI implementation
# 	(c) 2024 Magnus Bender
# 	Institute of Humanities-Centered Artificial Intelligence (CHAI), Universitaet Hamburg
# 		https://www.philosophie.uni-hamburg.de/chai/personen/bender.html
# 	released under the terms of GNU Public License Version 3
#     https://www.gnu.org/licenses/gpl-3.0.txt

import re, os

from typing import Callable, Union

from fastapi import Request, BackgroundTasks
from fastapi.responses import RedirectResponse, FileResponse, Response
from fastapi.templating import Jinja2Templates

from core.csmc.fdr import FDR

class ViewDownload():

	def __init__(self, template:Jinja2Templates, error_response:Callable):
		self.template = template
		self.error_response = error_response

	def view_prepare(self, request:Request, fdr_file:str, background_tasks:BackgroundTasks):
		view_link = "/view/"+fdr_file+"/index.html"

		fdr = self._prepare(
			request, fdr_file, background_tasks,
			view_link
		)

		return fdr if not isinstance(fdr, FDR) else RedirectResponse(view_link)
		
	def download(self, request:Request, fdr_file:str, background_tasks:BackgroundTasks):
		view_link = "/download/"+fdr_file

		fdr = self._prepare(
			request, fdr_file, background_tasks,
			view_link
		)

		return fdr if not isinstance(fdr, FDR) else self.template.TemplateResponse(
			'download.html',
			{ "request" : request,
				"fdr_file" : fdr_file,
				"raw_info" : fdr.get_raw_info()
    			}
		)
		
	def _prepare(self,
		request:Request, fdr_file:str, background_tasks:BackgroundTasks,
		view_link:str
	) -> Union[Response, FDR]:
		fdr = FDR(fdr_file)
		# ready for display -> redirect 
		if fdr.is_available():
			return fdr
		
		# error -> show error message
		elif fdr.is_error():
			return self.template.TemplateResponse(
				'error.html',
				{ "request" : request,
					"url_valid" : fdr.url_valid(),
					"fdr_file" : fdr_file,
					"error_messages" : fdr.get_error_messages()
				},
				status_code=400
			)
		
		# not ready for display -> download or wait
		else:
			# this will schedule the download as "background_tasks"
			if fdr.make_available(background_tasks):
				return self.template.TemplateResponse(
					'waiting.html',
					{ "request" : request,
						"fdr_file" : fdr_file,
						"view_link" : view_link
					}
				)
			else:
				return self.template.TemplateResponse(
					'error.html',
					{ "request" : request,	
						"fdr_file" : fdr_file,
						"url_valid" : fdr.url_valid(),
						"error_messages" : fdr.get_error_messages()
					},
					status_code=400
				)
			
	def view_serve(self, request:Request, fdr_file:str, viewer_resource:str):
		fdr = FDR(fdr_file)
		if fdr.is_available():
			if (
					not '..' in viewer_resource and
					not re.match(r'^[A-Za-z0-9\.\-\/\_]+$', viewer_resource) is None
				) and (
					viewer_resource in ('index.html', 'data.zip') or 
					viewer_resource.startswith(('raw/', 'static/'))
				):
					path = fdr.get_path()
					serve_file = os.path.join(path, viewer_resource)

					if os.path.isfile(serve_file) and os.path.realpath(serve_file).startswith(path):
						return FileResponse(serve_file)
					else:
						return self.error_response(request, "Not Found", 404)
			else:
				return self.error_response(request, "Not Allowed", 403)
		else:
			return RedirectResponse("/view/"+fdr_file)