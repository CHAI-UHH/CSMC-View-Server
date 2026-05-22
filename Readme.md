# CSMC-View-Server

- *See [&darr; below](#about) for more about CSMC files, viewers, and servers*
- [Specification of the CSMC file format](./server/web/public/specification.md)
- CSMC-View-Server of University of Hamburg: <https://csmc-view.chai.uni-hamburg.de/>
- Research Data Repository of University of Hamburg: <https://www.fdr.uni-hamburg.de/>

## Create a CSMC file
This is the repository of the view server, which can be run by, e.g., an university to together with a research data repository for hosting CSMC files.

- For bundling data with a viewer in CSMC files, see the [Generic Viewer](https://github.com/CHAI-UHH/Generic-CSMC-Viewer).
- There is also the [CMSCGen CLI](https://github.com/CHAI-UHH/Generic-CSMC-Viewer/blob/main/python/Readme.md) which provides an easy way to create a CSMC file by providing CSV files.
	In addition, *CSMCGen CLI* provides a local preview for CSMC files. 
	This preview can also be used while working or developing viewers.

## Deploy a CSMC-View-Server
	
### Virtual Environment
- Setup
	- `uv venv .venv --python 3.12`
	- `source .venv/bin/activate`
	- `uv pip install -r requirements-frozen.txt` [install packages with fix versions]
	- (`uv pip install --upgrade -r requirements.txt` [update all packages, may break things])
	- (`uv pip freeze > requirements-frozen.txt` [store package details])
- Run (in folder `./server`!!)
	- `DEVMODE=true fastapi dev core/web/main.py` [development server]
	- `python -m core` [CLI interface]
	- `pdoc --output-directory ./../docs --no-browser --docformat google core` [update docs, or [here](https://chai-uhh.github.io/CSMC-View-Server/)]

### Docker
- `docker compose build`
- `docker compose up -d`

### Configuration
- Environment
	- `SERVER_PATH`: The path/ url for external access, defaults to `http://127.0.0.1:8000`
      - `DEVMODE`: Run in development mode (defaults to `false`)
	- `ALLOWED_HOSTNAMES`: A comma speparated list of host names of RDRs to allow downloading CSMC files from (all hostnames are allowed in devmode), example `rdr.example.com,rde-staging.example.com`
	- `IMPRINT_URL` and `PRIVACY_POLICY_URL`: Urls to imprint and privacy policy
	- `CONTACT_NAME` and `CONTACT_MAIL`: Name and mail address of a contact person
- Electron App
	- The server distributes the latest version of the local CSMC-App, an Electron based app to open CSMC files locally.
	- The server expects the four bundles of the app to be called like below (version string has the form `vX.Y.Z`, e.g., `v1.2.1`): 
		- `CSMC-App_Linux_vX.Y.Z.AppImage`
		- `CSMC-App_macOS-Intel_vX.Y.Z.dmg`
		- `CSMC-App_Windows_vX.Y.Z.exe`
		- `CSMC-App_macOS_vX.Y.Z.dmg`
	- Put the bundles in the folder `./server/web/public/local-app/` (e.g., use bind-mount for Docker)
	- The server will redirect to the newest files a at `https://my-csmc-server.example.com/local-app/{kind}-latest`
- Cleanup
	- The server stores data in the data-folder. There is a clean-up task that should be run periodically to remove old items from the data cache: CLI via `python -m core -c`  
- DOI Citations
	- More setup needed, change among others the [citation.js](./server/web/public/js/citation.js)

### Hidden Endpoints
- `{SERVER_PATH}/api`: http://127.0.0.1:8000/api
- `{SERVER_PATH}/history`: http://127.0.0.1:8000/history
- `{SERVER_PATH}/docs/core.html`: http://127.0.0.1:8000/docs/core.html [devmode only]

## About
### The View Server
*CSMC-View-Server* by Magnus Bender, Florian Marwitz, Thomas Asselborn, Sylvia Melzer, 
Institute for Humanities-Centered Artificial Intelligence (CHAI),
University of Hamburg, <https://www.chai.uni-hamburg.de/>,

*CSMC-View-Server* is released unter the terms of GNU Public License Version 3 ([GPLv3](./LICENSE.txt)).

### CSMC Files
- A general introduction into CSMC files for data management: 
      [Dataset Provision and Citation in the Digital Age](https://www.philosophie.uni-hamburg.de/chai/forschung/research-data-management.html)
- Different demos using CSMC files and viewers while being integrated in a rResearch Data Repository (RDR):
      [Demos](https://www.philosophie.uni-hamburg.de/chai/demos.html)
- [View-Server at University of Hamburg](https://csmc-view.chai.uni-hamburg.de/)
- [RDR of University of Hamburg](https://www.fdr.uni-hamburg.de/search?page=1&size=20&file_type=csmc)