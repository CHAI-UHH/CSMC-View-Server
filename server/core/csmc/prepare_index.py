# CSMC File Server -- FastAPI implementation
# 	(c) 2024 Magnus Bender
# 	Institute of Humanities-Centered Artificial Intelligence (CHAI), Universitaet Hamburg
# 		https://www.philosophie.uni-hamburg.de/chai/personen/bender.html
# 	All rights reserved!

import os
from io import StringIO

from jinja2 import Template

from core.utils import const, file_get_contents, file_put_contents

class PrepareIndex():

	SERVER_PATH = const.SERVER_PATH
	VERSION = const.VERSION

	INSERT_ITEMS = [
		{
			"file" : None,
			"code" : '<script class="csmc-inject" src="{{SERVER_PATH}}/static/js/history.js?{{VERSION}}"></script><script class="csmc-inject" src="{{SERVER_PATH}}/static/js/citation.js?{{VERSION}}"></script><script class="csmc-inject" src="{{SERVER_PATH}}/static/js/preview.js?{{VERSION}}"></script><style class="csmc-inject">div.csmc-branding a:hover {text-decoration: underline !important;}</style>',
			"locations" : [ '<!-- CSMC-Header -->', '<head>', '<html>' ],
			"after" : True,
			"remove_code" : '<script>class CSMC{static isAvailable(){return false;}}</script>'
		},
		{
			"file" : None,
			"code" : '<div class="csmc-legal" style="position: fixed; bottom: 10px; right: 10px; z-index: 9999;background-color: #eeeeee;padding: 10px;box-shadow: 2px 2px black;"><a href="{{SERVER_PATH}}/" target="_blank" style="text-decoration: none;" title="Website of CSMC Viewer">provided by CSMC Viewer</a></div>',
			"locations" : [ '<!-- CSMC-Legal -->', '</body>', '</html>', '' ],
			"after" : False,
			"remove_code" : None
		},
		{
			"file" : os.path.join(const.BASE_PATH, 'web', 'templates', 'csmc-branding.html'),
			"code" : None,
			"locations" : [ '<!-- CSMC-Branding -->', '<body>', '<html>', '' ],
			"after" : True,
			"remove_code" : None
		}
	]

	def __init__(self, index_file:str=None):
		if not index_file is None:
			self.prepare_index_file(index_file)

	def prepare_index_file(self, index_name:str, index_template:str=None):
		content = file_get_contents(index_name if index_template == None else index_template)

		for item in self.INSERT_ITEMS:
			insert = ''
			if item['file']:
				insert += file_get_contents(item['file'])
			if item['code']:
				insert += item['code']

			# apply Jinja2 for processing the items to insert
			buffer = StringIO()
			Template(insert).stream(
				is_viewer=True,
				SERVER_PATH=self.SERVER_PATH,
				ALLOWED_HOSTNAMES_FIRST=const.ALLOWED_HOSTNAMES[0],
				VERSION=self.VERSION
			).dump(buffer)
			insert = buffer.getvalue()
			
			for location in item['locations']:
				full_insert = location + "\n" + insert if item['after'] else insert + "\n" + location
				if len(location) == 0:
					content += "\n" + full_insert
					break
				elif location in content and len(location) > 0:
					content = content.replace(location, full_insert)
					break

			if item['remove_code']:
				content = content.replace(item['remove_code'], '')

		file_put_contents(index_name, content)
	