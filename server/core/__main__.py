# CSMC File Server -- FastAPI implementation
# 	(c) 2024 Magnus Bender
# 	Institute of Humanities-Centered Artificial Intelligence (CHAI), Universitaet Hamburg
# 		https://www.philosophie.uni-hamburg.de/chai/personen/bender.html
# 	All rights reserved!

import argparse

from core.utils import const, fix_file_permissions

from core.dev.server import DevServer
from core.csmc.cleanup import CleanUp

class CLI():

	def __init__(self):
		self.parser = argparse.ArgumentParser(description='CSMC Viewer CLI Access') 
		self.parser.add_argument('-d', '--dev', help="start the dev server for viewers", action="store_true")
		self.parser.add_argument('-c', '--clean-up', help="run the cleanup task (remove old viewers)", action="store_true")
		self.parser.add_argument('-C', '--clean-all', help="run the cleanup task (remove all viewers)", action="store_true")
		self.parser.add_argument('-f', '--fix-permissions', help="fix all the file permissions", action="store_true")

	def run(self):
		args = self.parser.parse_args()

		if args.dev:
			print("Running the development server for viewers!")
			dev_server = DevServer()
			dev_server.run()

		elif args.clean_up or args.clean_all:
			print("Run the clean up task for stale viewers!")
			clean_up = CleanUp()
			clean_up.run(args.clean_all)

		elif args.fix_permissions:
			print("Run filesystem fix permissions!")
			print("\t"+const.DATA_PATH)
			fix_file_permissions(const.DATA_PATH)
		else:
			self.parser.print_help()	

if __name__ == "__main__":
	const.RUNNING_AS_CLI = True

	cli = CLI()
	cli.run()
