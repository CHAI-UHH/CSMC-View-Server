# CSMC File Server -- FastAPI implementation
# 	(c) 2024 Magnus Bender
# 	Institute of Humanities-Centered Artificial Intelligence (CHAI), Universitaet Hamburg
# 		https://www.philosophie.uni-hamburg.de/chai/personen/bender.html
# 	All rights reserved!

import os, re, time

from http.server import test as http_serve, SimpleHTTPRequestHandler, ThreadingHTTPServer

from core.csmc.prepare_index import PrepareIndex
from core.utils import const

class _SimpleHTTPRequestHandler(SimpleHTTPRequestHandler):

	last_modifications = {}
	
	def translate_path(self, path):
		path_before = path
		assumed_path = super().translate_path(path)

		if not os.path.isdir(assumed_path):
			matches = re.match(
				r'^\/(?:pre)?view\/(.*)\/record(s?)\/([A-Za-z\_\-0-9]+)\/files\/([A-Za-z\_\-0-9%\ ]+)\.csmc\/(.*)$',
				path_before
			);
			if matches: # its a viewer folder
				viewer_name = matches.group(4) 
				appendix =  matches.group(5) 

				# get path to the the viewer
				new_path = '/viewers/'+viewer_name+'/'+appendix
				# and check path again
				real_path = super().translate_path(new_path)

				# build the index page (inject items)
				if real_path.endswith(('/', '\\', '/index.html', '\\index.html')):
					real_path = real_path if real_path.endswith(('/', '\\')) else real_path[:-10]

					# check if index file needs rebuild
					last_modified = os.path.getmtime(real_path+'index.html')
					if real_path not in self.last_modifications or \
						last_modified > self.last_modifications[real_path]:
							print('Updating "index-processed.html"!')

							DevServer.brand_index(
								real_path+'index-processed.html',
								real_path+'index.html'
							)

							self.last_modifications[real_path] = last_modified

					real_path += 'index-processed.html'

			elif path_before.startswith('/static/'): # a static file to serve
				# get path to the the viewer
				new_path = '/server/web/public/' + path_before[8:]
				# and check path again
				real_path = super().translate_path(new_path)

			else:
				# will result in error!
				real_path = assumed_path
		else:
			# will serve *local page*
			real_path = assumed_path

		return real_path
	
class _ThreadingHTTPServer(ThreadingHTTPServer):
	def finish_request(self, request, client_address):
		self.RequestHandlerClass(
			request, client_address, self,
			directory=os.path.join(const.BASE_PATH, '..')
		)


class DevServer():

	BIND_IP = '127.0.0.1'
	BIND_PORT = 8000

	prepare_index = None
	
	def __init__(self):
		if self.__class__.prepare_index is None:
			pi = PrepareIndex()

			pi.VERSION = str(int(time.time()))
			pi.SERVER_PATH = 'http://{ip}:{port}'.format(ip=self.BIND_IP, port=self.BIND_PORT)
			pi.INSERT_ITEMS.append({
				"file" : None,
				"code" : '<script class="csmc-inject">CSMC._window_location_hostname = "csmc-view.chai.uni-hamburg.de";</script>',
				"locations" : [ '<body>' ],
				"after" : True,
				"remove_code" : None,
			})

			self.__class__.prepare_index = pi

	@classmethod
	def brand_index(cls, index_file:str, template_file:str):
		cls.prepare_index.prepare_index_file(index_file, template_file)

	def run(self):
		http_serve(
			HandlerClass=_SimpleHTTPRequestHandler,
			ServerClass=_ThreadingHTTPServer,
			port=self.BIND_PORT,
			bind=self.BIND_IP,
			protocol='HTTP/1.0'
		)
