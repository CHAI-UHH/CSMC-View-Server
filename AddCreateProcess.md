
# Documentation of Building a Create Process
*March 2026, Florian Marwitz*

The so-called *create process* is an automated procedure to build a project-specific csmc file on demand.
Each project has its own create process.
The create process lives at a designated URL, providing an upload form, where the user may enter some data and upload files.
Next, the server starts the creation process and provides updates and let the user download the newly created csmc file.
In this file, we describe how to build a new create process.

A create process consists mainly of two parts: The background task and the web handler.
The web handler is responsible for serving web pages, taking requests and uploads from the user, placing files into the right directory, and starting the background task as well as providing the result of the background task.
The background task is the procedure of transforming everything the user uploaded (data and files) to a final csmc file output.

We split the documentation in five parts:
First, we talk about the prerequisites like folder structure and URLs used.
Second, we give a quick start guide.
Afterwards, we start the actual documentation by, third, explaining the structure of the background task.
Fourth, we describe the web page handler connecting requests and the background tasks.
Fifth, we link the web page handler to the existing main script for the server to recognize it.

## Prerequisites
The create process consists of two parts, the background task and the web handler, as well as some additional files, like the html templates for the website and maybe some other files needed.
We give an overview over the used files and URLs in this section.
We assume that `PROJECT` is a short label identifying the project for which we build a create process.
Each create process listens on three URLs:
* `/create/PROJECT` for serving the upload form (GET request), and taking the upload (POST request)
* `/create/PROJECT/ID` for showing progress information
* `/create/PROJECT/ID/PROJECT.csmc` for downloading the created csmc file

Moreover, the create process itself is split across multiple directories and files:
* `/server/core/csmc/create/PROJECT_creator.py` for the background task. In more complex cases, this script is moved to its own subdirectory `/server/core/csmc/create/PROJECT/PROJECT_creator.py` to allow for other scripts to reside in the same directory, seperating the files of each create process.
* `/server/core/web/create/PROJECT.py` for the web handler
* `/server/core/web/main.py` is used to link the web handler to the overall web server
* `/server/web/templates/create/PROJECT/` containing html templates for the web pages used by the create process, e.g., the upload form, html code for the progress page, and so on
* `/server/create_additional_files/PROJECT` may contain any files the create process may need, e.g., the viewer to be copied

In the next section, we give a quick start guide by simply copying another viewer and adjusting the code.
Afterwards, we explain each component in more depth.

## Quick Start
As a rule of thumb, you may just copy an existing create process and modify it:

1. Create `/server/core/csmc/create/PROJECT_creator.py` by copying it from another create process (up until the `run(self)` function, which must be implemented on your own, but of course you may reuse existing code for similar tasks)
2. Create `/server/core/web/create/PROJECT.py` by copying it from another create process and modify it accordingly, in particular the `upload_form` function
3. Go into `/server/core/web/main.py` and copy the four function definitions of another viewer and modify them to fit your needs (in particular the form upload), and make sure to import your web handler, see the section on linking for more details
4. Copy `/server/web/templates/create/PROJECT/*` from another viewer and modify it accordingly
5. Place your viewer to be copied during the background task inside `/server/create_additional_files/PROJECT/viewer/`
6. Update the [`index.html`](./server/web/templates/index.html) to include a link to `/create/PROJECT`.
7. Start the server and debug

We now go over to the actual documentation, explaining each component and function usage.

## Background Task
We start with the description of the background task.
We assume that the web handler already uploaded the user's files into a directory, at the moment `/server/data/create/ID`, where `ID` is replaced by a unique id.
The background task is started by the web handler and runs asynchronously in the background, hence the name.
The background task takes as input the files uploaded by the user and any other form elements the user provided.
The output of the background task is the `PROJECT.csmc` csmc file.
Along the process of transforming the files to the csmc file, the background process may provide some kind of feedback, e.g., a lock file indicating that it is still running or a progress file stating the current step and progress within the step.

### Code Localization
Switching to code localization, the background task is a python script `/server/core/csmc/create/PROJECT_creator.py`, where `PROJECT` is replaced by a project-specific label (e.g., `EXAMPLE`).
Sometimes, the background task requires a more complex setup with more scripts.
In this case, the background task gets its own directory `/server/core/csmc/create/PROJECT/`, in which the `PROJECT_creator.py` then resides alongside other scripts, which are called by `PROJECT_creator.py`.

### Code Organization
Let us dive into the structure of a background task.
The `PROJECT_creator.py` provides a single class, namely `PROJECTCreationTask`.
The key idea is that the task class itself is stateless, obviously apart from the actually task running.
We mean with stateless that we can create another `PROJECTCreationTask` object to check the status of this task.
Each task is assigned a unique id per user-initiated run.
All state requests like *Is this task running?* should be answered without requiring access to the specific `PROJECTCreationTask` instance that originally started the process.

At the moment, all my background tasks have mostly the following functions:

* `__init__(self, id:str)` to initialize the class by setting variables to the paths later used
* `exists(self)` to check whether the task exists (which is mostly as simple as checking whether the task directory is present)
* `lock(self)` and `unlock(self)` to create/delete a lockfile (and progress file) for indicating that this task is running and in which state the task currently is
* `is_running(self)` for checking whether this task is running (which is mostly as simple as checking whether the lockfile is present)
* `is_finished(self)` for checking whether this task is finished (which is mostly as simple as checking whether the final `PROJECT.csmc` exists)
* `get_progress(self)` to get the process of the task, i.e., mostly two numbers for the current step and for the current progress (in percentage points, i.e., 0 to 100) within the step
* `_write_error(self, message:str, additional:str)` to have a function used in the script when an error occurs to write the error into a file
* `has_error(self)` for checking whether an error occured (which is mostly as simple as checking whether the error file is present)
* `_write_status(self, step, progress)` to write the status information to the progress file
* `run(self)` for actually running the task, e.g., processing the files from the user, copying the viewer to the task directory and zipping everything into a csmc file. This may incldue calls to your own functions or scripts.

All these functions serve the process of enabling the web handler to start the process and then to lookup the current status including progress information, error handling, and serving the final csmc file to download.
You may have a look at the background tasks for the example project so-far, [EXAMPLE](./server/core/csmc/create/EXAMPLE/EXAMPLE_creator.py) to familiarize you with the structure.
Look only up until the definition of the `run` function and you will see mostly the same code.
Then have a look at the `run` functions, which all somehow process the files from the user, copy the viewer and zip the directory.
Additional files, like the viewer, may be located in `/server/create_additional_files/PROJECT`.

## Web Handler
We connect the background task with the user through the web handler.
The web handler is responsible for answering the web requests by the user and deciding which web pages to server, e.g., the upload form, progress information, error messages, and the final csmc file download.
We discuss first the necessary html templates and then go on with the web handler itself.

### HTML Templates
Each creation process has some html templates for providing the upload form, progress or error information and the download page for the created csmc file.
The templates are located at `/server/web/templates/create/PROJECT/` and include
* `form.html` for the upload form,
* `waiting.html` for progress information,
* `error.html` for showing the error message if an error has occurred, and
* `download.html` for providing a download page for the created csmc file.

These files are similar across the different creation processes, with differences mostly in the `form.html` due to different needs for information and files.
Have a look at the template directories for [EXAMPLE](./server/web/templates/create/EXAMPLE/) to familiarize yourself with the files.

### Web Handler Class
The web handler is a script located at `/server/core/web/create/PROJECT.py`, serving a class `PROJECTCreatorPage` responsible for answering the web requests from the user.
The task of the web handler is now to serve the upload form, take the files for being uploaded, show the status page, and deliver the final csmc file.

The class has the following functions:

* `__init__(self, template:Jinja2Templates)` to save the template engine reference
* `show_form(self, request:Request)` to serve the upload form html template
* `def upload_form(self, request:Request, background_tasks:BackgroundTasks, files)` to actually perform the upload (i.e., handling the request when the user submits the form) and start the background task. The variable `files` in the end contains the uploaded files, if the form has more entries that are processed, then they go in the function definition as well. In the next subsection, we describe the linking.
* `show_status(self, request:Request, id:str)` to show the progress information of the requested task
* `download(self, request:Request, id:str)` to download the created csmc file

You may have a look at the web handlers of [EXAMPLE](./server/core/web/create/EXAMPLE.py) for exemplary implementations, which are all quite similar.

## Linking

Until now, we have successfully created all code for handling the web requests and for running the background task.
However, the main server is still unaware of our functions.
Next, we link URLs to our functions inside the [web main script](./server/core/web/main.py).
Each create process has three URLs: `/create/PROJECT` for the upload form, `/create/PROJECT/ID` for a running task, and `/create/PROJECT/ID/PROJECT.csmc` for downloading the created csmc file.

Go inside the `_add_routes(self)` method of the class [`WebMain`](./server/core/web/main.py) and add the following four functions.
We have four functions, since the URL for serving the upload form is used in two ways: For serving the upload form in a GET request, and for uploading the form in a POST request.
Before the functions, we create an instance of the web handler so that we can call the corresponding functions.
Please take a look at the already linked create processes in [`WebMain`](./server/core/web/main.py) on how to link the form fields, which are currently denoted by `...` in the code.
Also, make sure to import your web handler at the top of the file.

```
PROJECT = PROJECTCreatorPage(self.template)

@self.app.get(
		"/create/PROJECT",
		summary="Upload form for PROJECT project files",
		response_class=Response # HTMLResponse
	)
def create_PROJECT_form(request:Request):
	"""
		Show the form to create an PROJECT CSMC File.
	"""
	return PROJECT.show_form(request)

@self.app.post(
	"/create/PROJECT",
	summary = "Upload files",
	response_class=Response # HTMLResponse|RedirectResponse
)
def create_PROJECT_upload(request:Request, background_tasks:BackgroundTasks, ...):
	"""
		Upload the files to create an PROJECT CSMC File.
	"""
	return PROJECT.upload_form(request, background_tasks, ...)

@self.app.get(
	"/create/PROJECT/{task_id:str}",
	summary= "Show the status of the PROJECT creation or download page",
	response_class=Response # HTMLResponse
)
def create_PROJECT_status(request:Request, task_id:str):
	"""
		Show the status of the PROJECT creation or download page.
	"""
	return PROJECT.show_status(request, task_id)

@self.app.get(
	"/create/PROJECT/{task_id:str}/PROJECT.csmc",
	summary= "Download the PROJECT CSMC file",
	response_class=Response # FileResponse|HTMLResponse
)
def create_PROJECT_download(request:Request, task_id:str):
	"""
		Download the PROJECT CSMC file.
	"""
	return PROJECT.download(request, task_id)
```

To complete the linking, we make sure that the [`index.html`](./server/web/templates/index.html) includes a link to the `/create/PROJECT` URL.
Now, we can start the server and debug our newly built create process.