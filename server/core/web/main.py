# CSMC File Server -- FastAPI implementation
#	 (c) 2024 Magnus Bender, Florian Marwitz
#	 Institute of Humanities-Centered Artificial Intelligence (CHAI), Universitaet Hamburg
#		 https://www.philosophie.uni-hamburg.de/chai/personen/bender.html
#	 released under the terms of GNU Public License Version 3
#     https://www.gnu.org/licenses/gpl-3.0.txt

import os, re

from typing import Union, List
from packaging.version import parse as parse_version

from fastapi import FastAPI, Request, BackgroundTasks, File, UploadFile, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, Response, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.openapi.docs import get_swagger_ui_html

from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError

from pydantic import validate_arguments

import mistune
from mistune.directives import RSTDirective, TableOfContents

from core.web.view_download import ViewDownload
from core.web.preview import PreviewPage
from core.web.create.EXAMPLE import EXAMPLECreatorPage

from core.utils import const

class WebMain():

	ERROR_MSG_CODE = {
		"404" : {
			"msg" : "Not found",
			"code" : 404,
			"html" : False
		},
		"403" : {
			"msg" : "Not allowed",
			"code" : 403,
			"html" : False
		},
		"uhh-internal" : {
			"msg" : "Access to the resource is only allowed from inside of a VPN network.<br/>Please use the organizations's VPN or an office computer!",
			"code" : 403,
			"html" : True
		}
	}

	def __init__(self):
		self._init_app()
		self._init_templates()

		self._add_routes()

		self._custom_swagger()

	def _init_app(self):
		self.app = FastAPI(
			title="CSMC Viewer",
			description="The Viewer Application for CSMC-Files: CHAI & CSMC @ UHH",
			version=const.VERSION,
			openapi_url="/api/schema.json",
			docs_url=None,
			redoc_url=None
		)

		if const.DEVMODE or not const.SERVE_STATIC_NGINX:
			# this makes static files accessible in dev-mode (in production its a task for NGINX)
			self.app.mount(
				"/static",
				StaticFiles(directory=os.path.join(const.BASE_PATH, 'web', 'public')),
				name="static"
			)
		
		if const.DEVMODE:
			# this makes docs accessible in dev-mode
			self.app.mount(
				"/docs",
				StaticFiles(directory=os.path.join(const.BASE_PATH, 'docs')),
				name="docs"
			)

		@self.app.exception_handler(StarletteHTTPException)
		async def http_exception_handler(request, exc):
			return self.error_response(request,
					exc.detail if const.DEVMODE else "An HTTP error (code {}) has occurred!".format(exc.status_code),
					exc.status_code
				)

		@self.app.exception_handler(RequestValidationError)
		async def validation_exception_handler(request, exc):
			return self.error_response(request,
					str(exc) if const.DEVMODE else "The data sent by your browser is invalid (check input values)!",
					400
				)

	def _init_templates(self):
		self.template = Jinja2Templates(
			directory=os.path.join(const.BASE_PATH, 'web', 'templates'),
			auto_reload=const.DEVMODE
		)
		self.template.env.globals["SERVER_PATH"] = const.SERVER_PATH
		self.template.env.globals["VERSION"] = const.VERSION
		self.template.env.globals["DEVMODE"] = const.DEVMODE
		self.template.env.globals["ALLOWED_HOSTNAMES_FIRST"] = const.ALLOWED_HOSTNAMES[0]
		self.template.env.globals["IMPRINT_URL"] = const.IMPRINT_URL
		self.template.env.globals["PRIVACY_POLICY_URL"] = const.PRIVACY_POLICY_URL
		self.template.env.globals["CONTACT_NAME"] = const.CONTACT_NAME
		self.template.env.globals["CONTACT_MAIL"] = const.CONTACT_MAIL		

	def _custom_swagger(self):
		@self.app.get("/api", include_in_schema=False)
		async def api():
			return get_swagger_ui_html(
				openapi_url=app.openapi_url,
				title=app.title + " &ndash; Swagger UI",
				swagger_js_url=const.SERVER_PATH+"/static/js/swagger-ui-bundle.js",
				swagger_css_url=const.SERVER_PATH+"/static/css/swagger-ui.css",
				swagger_favicon_url=const.SERVER_PATH+"/static/favicon.ico"
			)

	def _add_routes(self):
		##
		# Main Routes (Info Pages)
		##
		@self.app.get(
				"/",
				summary="Index & about page",
				response_class=HTMLResponse
			)
		def index(request: Request):
			"""
				The main information page about the CMSC Server.
			"""
			return self.template.TemplateResponse(
				'index.html',
				{"request" : request}
			)
		
		@self.app.get(
				"/error",
				summary="Error page",
				response_class=HTMLResponse, include_in_schema=False
			)
		def error(request: Request, cause:Union[str, None]=None):
			if cause in self.ERROR_MSG_CODE:
				msg, code, html = self.ERROR_MSG_CODE[cause]["msg"], self.ERROR_MSG_CODE[cause]["code"], self.ERROR_MSG_CODE[cause]["html"]
			else:
				msg, code, html = "An error occured", 400, False

			return self.error_response(request, msg, code, html)

		@self.app.get(
				"/favicon.ico",
				summary="Favicon", 
				response_class=FileResponse, include_in_schema=False
			)
		def favicon(_: Request):
			return FileResponse(os.path.join(const.BASE_PATH, 'web', 'public', 'favicon.ico'))

		@self.app.get(
				"/history",
				summary="Show the history of visited viewers",
				response_class=FileResponse, include_in_schema=False
			)
		def history(r:Request):
			return self.template.TemplateResponse(
				'history.html',
				{"request" : r}
			)
		
		@self.app.get(
				"/local-app/{kind}-latest",
				summary="Get the latest CSMC App installer (kind in 'windows, macos, macos-intel, linux')",
				response_class=RedirectResponse
			)
		def app_latest_download_latest(request: Request, kind:str):
			kind_files = {
				"windows" : r"^CSMC-App_Windows_v(\d+\.\d+\.\d+)\.exe$",
				"macos" : r"^CSMC-App_macOS_v(\d+\.\d+\.\d+)\.dmg$",
				"macos-intel" : r"^CSMC-App_macOS-Intel_v(\d+\.\d+\.\d+)\.dmg$",
				"linux" : r"^CSMC-App_Linux_v(\d+\.\d+\.\d+)\.AppImage$",
			}
			if not kind in kind_files.keys():
				return RedirectResponse('/error?cause=404')
			
			# get the newest version from the server
			app_regex = re.compile(kind_files[kind])
			app_dir = os.path.join(const.BASE_PATH, 'web', 'public', 'local-app');
			max_version, max_version_file = parse_version('0.0.0'), "__non__existent__"
			for app_file in os.listdir(app_dir):
				# matches platform
				match = app_regex.match(app_file)
				if not match is None:
					version = parse_version(match.group(1))
					# is newest
					if version > max_version:
						max_version_file = app_file
						max_version = version

			# redirect to newest version
			if os.path.isfile(os.path.join(app_dir, max_version_file)):
				return RedirectResponse('/static/local-app/' + max_version_file)
			else:
				return RedirectResponse('/error?cause=404')

		@self.app.get(
				"/specification",
				summary="Show the specification of CSMC file format",
				response_class=HTMLResponse
			)
		def specification(request: Request):
			markdown = mistune.create_markdown(
				plugins=[
					RSTDirective([TableOfContents()]),
				]
			)

			try:
				content = "An error occured while reading the specification file."
				
				# Read the markdown file and convert it to HTML
				with open(os.path.join(const.BASE_PATH, 'web', 'public', 'specification.md'), 'r') as f:
					content = f.read()
					content = markdown(content)

				# Render the template
				return self.template.TemplateResponse(
					'specification.html',
					{"request" : request,
						"content": content}
				)
			except Exception as e:
				return self.error_response(request, "An error occured while reading the specification file.", 500)

		##
		# Viewer and Download
		##
		view_download = ViewDownload(self.template, self.error_response)
		
		@self.app.get(
				"/view/{fdr_file:path}.csmc",
				summary="Prepare a viewer",
				response_class=Response # HTMLResponse|RedirectResponse
			)
		def view_prepare(request: Request, fdr_file:str, background_tasks:BackgroundTasks):
			"""
				Prepare a viewer from the FDR, the `fdr_file` is the url to the csmc file in the FDR.
				This endpoint will prepare the viewer on the server and open it afterwards (by redirecting).
			"""
			return view_download.view_prepare(request, fdr_file+".csmc", background_tasks)

		@self.app.get(
				"/view/{fdr_file:path}.csmc/{viewer_resource:path}",
				summary="Serve a viewer and its files",
				response_class=Response # FileResponse|RedirectResponse
			)
		def view_serve(request: Request, fdr_file:str, viewer_resource:str):
			"""
				Show a viewer extracted from an CSMC file available in the FDR.
				The `fdr_file` again is the url to the csmc file in the FDR.
				While the `viewer_resource` is the path to the assets in the CSMC file (e.g. `static/app.js`, `index.html`, ...).

				There is also a special `viewer_resource` file named `data.zip`, which contains the extracted data.
			"""
			return view_download.view_serve(request, fdr_file+".csmc", viewer_resource)

		@self.app.get(
				"/download/{fdr_file:path}.csmc",
				summary="Extract a viewers data",
				response_class=Response # HTMLResponse|RedirectResponse
			)
		def download(request: Request, fdr_file:str, background_tasks:BackgroundTasks):
			"""
				Prepare a viewer from the FDR, the `fdr_file` is the url to the csmc file in the FDR.
				This endpoint will prepare the viewer on the server and download provide the extracted data to the user afterwards.
			"""
			return view_download.download(request, fdr_file+".csmc", background_tasks)
		
		##
		# Server Preview
		##
		preview = PreviewPage(self.template, self.error_response)
		
		@self.app.get(
				"/preview",
				summary="Show form for uploading csmc file for preview",
				response_class=Response # HTMLResponse
		)
		def preview_form(request: Request):
			"""
				Upload a CSMC file to preview it.
			"""
			return preview.show_form(request)
		
		@self.app.post(
			"/preview",
			summary = "Upload csmc file",
			response_class=Response # HTMLResponse|RedirectResponse
		)
		def preview_upload(request:Request, background_tasks:BackgroundTasks, files: List[UploadFile] = File(...)):
			"""
				Upload the file and start unpacking. Redirect user to waiting page.
			"""
			return preview.upload_form(request, background_tasks, files)
		
		@self.app.get(
			"/preview/{task_id:str}",
			summary= "Show the waiting page or redirect to preview",
			response_class=Response # HTMLResponse
		)
		def preview_status(request:Request, task_id:str):
			"""
				Show the waiting page or redirect to preview.
			"""
			return preview.show_status(request, task_id)
		
		@self.app.get(
				"/preview/{task_id:str}/{viewer_resource:path}",
				summary="Serve a viewer and its files",
				response_class=Response # FileResponse|RedirectResponse
			)
		def view_serve(request: Request, task_id:str, viewer_resource:str):
			"""
				Show a viewer uploaded from a local computer.
				The `task_id` is the id of the task.
				While the `viewer_resource` is the path to the assets in the CSMC file (e.g. `static/app.js`, `index.html`, ...).

				There is also a special `viewer_resource` file named `data.zip`, which contains the extracted data.
			"""
			return preview.serve(request, task_id, viewer_resource)

		##
		# Create: EXAMPLE
		##
		example = EXAMPLECreatorPage(self.template)
		
		@self.app.get(
				"/create/EXAMPLE",
				summary="Upload form for EXAMPLE project files",
				response_class=Response # HTMLResponse
			)
		def create_EXAMPLE_form(request:Request):
			"""
				Show the form to create an EXAMPLE CSMC File.
			"""
			return example.show_form(request)
		
		@self.app.post(
			"/create/EXAMPLE",
			summary = "Upload files",
			response_class=Response # HTMLResponse|RedirectResponse
		)
		def create_EXAMPLE_upload(request:Request, background_tasks:BackgroundTasks, files: List[UploadFile] = File(...)):
			"""
				Upload the files to create an EXAMPLE CSMC File.
			"""
			return example.upload_form(request, background_tasks, files)

		@self.app.get(
			"/create/EXAMPLE/{task_id:str}",
			summary= "Show the status of the EXAMPLE creation or download page",
			response_class=Response # HTMLResponse
		)
		def create_EXAMPLE_status(request:Request, task_id:str):
			"""
				Show the status of the EXAMPLE creation or download page.
			"""
			return example.show_status(request, task_id)
		
		@self.app.get(
			"/create/EXAMPLE/{task_id:str}/EXAMPLE.csmc",
			summary= "Download the EXAMPLE CSMC file",
			response_class=Response # FileResponse|HTMLResponse
		)
		def create_EXAMPLE_download(request:Request, task_id:str):
			"""
				Download the EXAMPLE CSMC file.
			"""
			return example.download(request, task_id)
		
		##
		# Further ...
		##
		# TODO -- implement more functions like preview, create, upload, use data (in LLM, query db)

	@validate_arguments(config=dict(arbitrary_types_allowed=True))
	def error_response(self, request:Request, message:str, status_code:int=400, html:bool=False):
		request.state.error = message
		request.state.error_safe = html # do not filter html, message content is 'safe'
		return self.template.TemplateResponse(
			'csmc-base.html',
			{"request" : request, "title_prefix" : "Error"},
			status_code=status_code
		)

if __name__ == "core.web.main":
	const.RUNNING_AS_WEB = True
	
	main = WebMain()
	app = main.app