# CSMC File Server -- FastAPI implementation
# 	(c) 2024 Magnus Bender
# 	Institute of Humanities-Centered Artificial Intelligence (CHAI), Universitaet Hamburg
# 		https://www.philosophie.uni-hamburg.de/chai/personen/bender.html
# 	released under the terms of GNU Public License Version 3
#     https://www.gnu.org/licenses/gpl-3.0.txt

import os, shutil

from core.utils.const import FILES_OWN_USER_GROUP

def file_get_contents(fn):
	with open(fn, 'r') as f:
		return f.read()
	
def file_put_contents(fn, ct):
	with open(fn, 'w+') as f:
		f.write(ct)

def fix_file_permissions(path, recursive:bool=True, skip_owner:bool=False):
	file_mode = 0b110_110_100 # rw-rw-r--
	dir_mode = 0b111_111_101 | 0o2000 # (d)rwxrwsr-x

	# the base path
	if not skip_owner:
		shutil.chown(path, *FILES_OWN_USER_GROUP)
		
	os.chmod(path,
		dir_mode if os.path.isdir(path) else file_mode, 
		follow_symlinks=False
	)

	# all files and sub paths
	if recursive:
		for base_path, dirs, files in os.walk(path, topdown=False, followlinks=False):
			if not skip_owner:
				shutil.chown(path, *FILES_OWN_USER_GROUP)

			for name in files:
				os.chmod(os.path.join(base_path, name), file_mode, follow_symlinks=False)
			for name in dirs:
				os.chmod(os.path.join(base_path, name), dir_mode, follow_symlinks=False)