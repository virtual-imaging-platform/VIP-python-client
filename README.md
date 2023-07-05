[vip-portal]: https://vip.creatis.insa-lyon.fr/ "https://vip.creatis.insa-lyon.fr/"

# Table of Contents
[TODO]
- [Introduction](#introduction)
- [VipSession](#vipsession)
  - [Get Started](#get-started)
    - [Basic Steps][steps]
    - [VipSession Properties](#vipsession-properties)
    - [VipSession Outputs](#session-outputs)
  - [Best Practices](#best-practices)
    - [Use VipSession Shortcuts][shortcuts]
    - [Use the Session Backup][backup]
    - [Parallelize your Executions][parallelize]
    - [Run Multiple `VipSession`s on the Same Dataset][multiple_vipsessions]
- [VipCI](#vipci)
- [vip.py](#vip.py)
  - [How to use it](#how-to-use-it)
  - [Raised errors](#raised-errors)
  - [Improvement](#improvement)
- [Get a VIP API key](#get-a-vip-api-key)

---

# Introduction

*Python client for the [Virtual Imaging Platform](vip-portal) (VIP).*

Ready-to-use Python classes are contained in the `src` directory. Most useful methods are implemented in class `VipSession` (see [below](#vipsession)). Classes `VipLauncher` and `VipCI` are mostly used by the VIP team for current projecs' requirements.

*If you encounter any issues, please contact us at: <vip-support@creatis.insa-lyon.fr>*

**/!\\ Prerequisites /!\\**

 1. This Python client uses the [VIP API](./vip.py) by making calls to the [`requests`](https://pypi.org/project/requests/) Python library. This may require installing this library on your machine:
  ```
  pip install requests
  ```

2. Communication with VIP requires a **valid API key**.
  It can easily be obtained in two steps: 
  - [Create free account](#create-a-vip-account) on the [VIP portal](vip-portal);
  - [Get your API key](#get-a-vip-api-key) from your account settings.

---

# VipSession

This Python class launches executions on [VIP](vip-portal) from any machine where the input data are stored (*e.g.*, one's server or PC). 
It works both on Windows and Posix OS (Linux, Mac).

Running an application ("pipeline") on VIP implies the following process:

*Upload one's Dataset on VIP servers* **>>** *Run the Pipeline* **>>** *Download the Pipeline Results from VIP servers*.

<img src="imgs/Upload_Run_Download.png" alt="Procedure" height="200" title="The Upload-Run-Download Procedure"/>

`VipSession` implements this procedure in a few methods. 

## Get Started
[get-started]: #get-started "Get Started"

This section presents the main [methods][steps], [inputs](#vipsession-properties) and [outputs](#vipsession-outputs) of the VipSession class.

### Basic Steps
[steps]: #basic-steps "Basic Steps"

From the root of this repository, the VipSession class must be imported from the *src* folder.
```python
from src.VipSession import VipSession
```

Any session with the Python client starts by initiating a connection with VIP through the `init()` class method.
```python
# Step 0. Connect with VIP
VipSession.init(api_key="VIP_API_KEY")
# One call applies to multiple VipSession instances (until connection is lost).
```

Once connection with VIP is established, the *upload-run-download* procedure is achieved through six elementary steps:

1. **Create** a `VipSession` instance
```python
# Step 1. Create a Session
session = VipSession(session_name="my-session")
```
2. **Upload** the your dataset on VIP servers
```python
# Step 2. Upload the input data
session.upload_inputs(input_dir="path/to/my/dataset")
```
3. **Launch** your application on VIP
```python
# Step 3. Launch a pipeline on VIP
session.launch_pipeline(pipeline_id="my_app/0.1", input_settings=my_settings)
```
4. **Monitor** its progress on VIP until all executions are over 
```python
# Step 4. Monitor the pipeline's workflow(s)
session.monitor_workflows()
```
5. **Download** pipeline's output files from VIP servers when all executions are over
```python
# Step 5. Download the outputs 
session.download_outputs()
```
6. **Finish** the `VipSession` instance by removing your input/output data from VIP servers.
```python
# Step 6. Remove the data from VIP servers
session.finish()
```

In this example, `VipSession` [properties](#vipsession-properties "VipSession Properties") (*e.g.* `session_name`, `input_dir`) are progressively passed as inputs during steps 1, 2 & 3. They can also be defined when instanciating `VipSession` (*i.e.* during `step 1` or `step 0`, see [below](#use-session-shortcuts "Session Shortcuts")). Additionnally, VipSession methods accept specific arguments (*e.g.* `nb_runs`, `refresh_time`) to fine-tune their behavior. See each method's doc-string for detailed information.

### VipSession Properties

As stated [above](#introduction), communication with VIP requires a valid [API key](#get-a-vip-api-key).
This requirement is not bound to a given Session.

0. `api_key` (*str*, **required**): your VIP API key.
    - *The API key can be provided in secure ways. See `VipSession.init()` docstring for detailed information.*

Once created, a VipSession instance allows you to run __(1) one pipeline__ on __(2) one dataset__ with __(3) one parameter set__. Therefore, it requires at least 3 arguments:

1. `pipeline_id` (*str*, **required**): The name of your pipeline on VIP.
    - Run `VipSession.show_pipeline(my_app)`
    to [show the pipeline identifiers](show_pipeline) relative to `my_app`.
    - Usually in the format: *application_name*/*version*.
2. `input_dir` (*str | os.PathLike*, **required**): The local path to your dataset.
    - This directory will be uploaded on VIP before launching the pipeline.
3. `input_settings` (*dict*, **required**): All parameters needed to run the pipeline.
    - Run `VipSession.show_pipeline(`*`pipeline_id`*`)` to [display the parameters][show_pipeline] for `pipeline_id`.
    - The dictionary can contain any object that can be converted to strings, or lists of such objects.
    - Parameters with a *list of values* launch [*parallel jobs*][parallelize] on VIP.

3 optional arguments can be provided to personalize the user experience:

4. `session_name` (*str*, **recommended**) A name to identify this session and the corresponding outputs. 
    - *Default value: 'VipSession-[date]-[time]-[id]'*
5. `output_dir` (*str | os.PathLike*, **optional**) Local path to the directory where: 
    - session properties will be saved; 
    - pipeline outputs will be downloaded from VIP servers.
    - *Default value: './vip_outputs/`session_name`'*

6. `verbose` (bool, **optional**) Verbose state of the *session*.
    - The *session* will display logs when True (default value).

Arguments 1 to 6 are `VipSession`'s **properties**: they fully define its behavior throughout the *upload-run-download* procedure. They can be accessed, set and deleted with classical dot notation: `session.property` (see [below][manipulate-properties]). 

### VipSession Outputs

When running a VipSession instance for the first time, a directory (`output_dir`) is made to store the pipeline results and the *session* backup file.
By default, this `output_dir` is `./vip_outputs/session_name`.

#### Pipeline Outputs

The `download_outputs()` procedure stores the pipeline results on your machine. If the VIP implementation of the pipeline yields a tarball (`*\*.tar.gz*`), its content is extracted (by default) and the archive is removed from your machine.

When a single job *(\*)* is submitted to VIP, the pipeline results are stored in `output_dir` mirroring their structure on VIP servers:

```
my-session
├── 02-02-2023_09:21:23
│   └── job_results.tgz
│       ├── file_x
│       └── file_y
└── session_data.json
```

In this file tree:
- Pipeline results correspond to `file_x` & `file_y`.
- `job_results.tgz` contains results from the same job.
  - It may be a tarball or a folder depending on the downloading options.
- `02-02-2023_09:21:23` is named after the starting time of the workflow.
- `session_data.json` is the session backup file.

See [below](#jobs-and-workflows "Jobs and Workflows") for detailed information about jobs and workflows.

#### Session Backup

At the end of steps 2, 3, 4, 5 & 6, session properties (*e.g.*, `session_name`, `pipeline_id`) are automatically saved in a JSON file (*session_data.json*).
This backup can be used to [resume a finished or running Session][backup].

## Best Practices

In this section you will learn how to [use VipSession shortcuts][shortcuts], get your [`pipeline_id` and `input_settings`][show_pipeline], [parallelize your executions][parallelize], [use the *session* backup][backup], [manipulate the VipSession properties][manipulate-properties] and [run multiple VipSessions on the same dataset][multiple_vipsessions]

### Use VipSession Shortcuts
[shortcuts]: #use-vipsession-shortcuts "Use VipSession Shortcuts"

VipSession properties (*e.g.*, `input_dir`, `pipeline_id`, `input_settings`) can be declared at instantiation:
```python
session = VipSession(session_name=..., input_dir=..., pipeline_id=..., input_settings=..., ouput_dir=...)
```

*Setting all session properties at instantiation allows earlier detection of common mistakes (*e.g.*, missing parameters or input files).*

This can also be done while handshaking with VIP ([steps 0-1][steps]) through `VipSession.init()`:
```python
session = VipSession.init(api_key=..., session_name=..., input_dir=..., pipeline_id=..., input_settings=..., ouput_dir=...)
```

When all properties are set, the full **upload-run-download** process ([steps 2-5][steps]) can be performed with `run_session()`:
```python
session.run_session()
```

Do not forget to remove your temporary data from VIP once the download is complete:
```python
session.finish()
```

All methods can be run in cascade, so everything holds in a single command:
```python
VipSession.init(api_key="VIP_API_KEY", input_dir="path/to/data", [...]).run_session().finish()
```

### Use `show_pipeline()` to Set the Inputs
[show_pipeline]: #use-show_pipeline-to-set-the-inputs "Use show_pipeline() to Set the Inputs"

The class method `show_pipeline()` can help you getting the `pipeline_id` you need and writing your `input_settings`. 

#### Get the `pipeline_id`

The pipeline identifier (`pipeline_id`) can be displayed by providing the application name. For example:
```python
VipSession.show_pipeline("freesurfer")
```
will show every `pipeline_id` that contains `"freesurfer"` with a partial, case-insensitive match:
```
Available pipelines
-------------------
Freesurfer (recon-all)/0.3.7
Freesurfer (recon-all)/0.3.8
FreeSurfer-Recon-all/v7.3.1
FreeSurfer-Recon-all-fuzzy/v7.3.1
-------------------
```
*__N.B.__: If the output is "`(!) No pipeline found for pattern 'freesurfer'`", you may need to register with the pipeline's **group** on [VIP Portal](vip-portal). Please find the procedure [below](#register-to-your-application-group).*

#### Write the `input_settings`

When `show_pipeline()` finds a single match among VIP applications, it displays a full description of the pipeline, including the parameters that can be fed in the `input_settings`. For example: 
```python
VipLauncher.show_pipeline("FreeSurfer-Recon-all/v7.3.1")
```
will display the following (large output truncated by "*[...]*"):
```
===========================
FreeSurfer-Recon-all/v7.3.1
======================================================================
NAME: FreeSurfer-Recon-all | VERSION: v7.3.1
----------------------------------------------------------------------
DESCRIPTION:
    Performs all, or any part of, the FreeSurfer cortical 
    reconstruction process [...]
----------------------------------------------------------------------
INPUT_SETTINGS:
REQUIRED..............................................................
- directives
    [STRING] $esc.xml($input.getDescription())
- license
    [FILE] Valid license file needed to run FreeSurfer.
- nifti
    [FILE] Single NIFTI file from series.
[...]
OPTIONAL..............................................................
- 3T_flag
    [STRING] The -3T flag enables two specific options in recon-all 
    for images acquired with a 3T scanner:  [...]
[...]
======================================================================
```
The list of inputs below "*INPUT_SETTINGS*" can be used to build the `input_settings` dictionary. This must include at least the *REQUIRED* inputs.
```python
input_settings = {
  "directives": "-all", # Options for recon-all, see Fressurfer documentation
  "license": "path/to/my/license.txt", # FreeSurfer License
  "nifti": "path/to/my/input/file.nii.gz", # Input file
  # [...]
}
```
The tag at the beginning of the parameter description provides the input type.
- *STRING* inputs should be of type `str`. For experimented users, they can be of any Python type that can converts to string (*e.g.* `bool`, `int`...), provided that the converted value fits the application.
- *FILE* inputs require a valid path to some file, either on **VIP** or in the **local file system**. This path can be `str` or any `os.PathLike` object, including from `pathlib`.

For each parameter in `input_settings`, the user can also provide a **list** of values. This launches parallel jobs on VIP, as explained below.

### Parallelize your Executions
[parallelize]: #parallelize-your-executions "Parallelize your Executions"

#### Illustration

If you are launching a VIP application on **multiple inputs** (*e.g.* multiple acquisitions or parameter sets), your executions must be **parallelized**. This is done by providing *list(s) of values* (*e.g.*, a list of input files) in the `input_settings`. For example:
```python
input_settings = {
  "directives": "-all", # Options
  "license": "path/to/my/license.txt", # License
  "nifti": [ # List of inputs files :
    "path/to/my/input/file_1.nii.gz", # Input file 1
    "path/to/my/input/file_2.nii.gz", # Input file 2
    # [...]
    "path/to/my/input/file_n.nii.gz", # Input file N
  ]
  # [...]
}
```
With the above `input_settings`, the VipSession instance will submit N *jobs* to VIP (one per input file). 

#### Jobs and Workflows

A **job** is a single task run by the pipeline on VIP, *e.g.*, with 1 input file and 1 parameter set. When *lists* of files or parameters are provided in the `input_settings`, the corresponding jobs run in parallel (the pipeline runs on all files and parameters at the same time).

A **workflow** is a collection of jobs submitted at the same time. A single `VipSession` instance can launch multiple workflows on the same `pipeline_id` with the same `input_settings` (see footnote *(\*)* [below](#in-practice)).

#### Output files

In the `VipSession` output directory (`output_dir`), the file tree displayed [above](#pipeline-outputs) can be generalized as below:
```
.
├── Workflow_1
│   ├── Job_A
│   │   ├── file_x
│   │   └── file_y
│   └── Job_B
│       ├── file_x
│       └── file_y
├── Workflow_2
│   ├── Job_A
│   │   ├── file_x
... ... ...
└── session_data.json
```

#### In Practice

VIP pipelines can be run on large datasets by submitting jobs in parallel.
1. A **single job** is submitted on VIP when `input_settings` are filled with a **single value** for each parameter;
2. A **single workflow** is used to run **multiple jobs** in parallel, when providing a **list of values** in the `input_settings`;
3. A **single VipSession instance** can be used to run **multiple workflows** on the same `pipeline_id` with the same `input_settings`) *(\*, \*\*)*;

__N.B.__: For large datasets, it is recommended to run the pipeline with workflows of 100 or 200 jobs.

*(\*)* *One `VipSession` instance can launch multiple workflows: by calling `launch_pipeline()` several times, by increasing argument `nb_runs`, or by [re-starting the session](#relaunch-a-finished-session) after it was "finished". In the first two cases, the workflows will run in parallel on VIP. To run parallel workflows, please contact <vip-support@creatis.insa-lyon.fr> to increase your execution capacity (1 by default).*

*(\*\*)* *Multiple Vipsession instances can extend these rules to multiple `pipeline_id` and multiple `input_settings`: see [below][multiple_vipsessions]*.

### Use the *Session* Backup
[backup]: #use-the-session-backup "Use the Session Backup"

A *session* is backed up after every step.
To restore a previous *session*, instantiate it with `ouput_dir`:
```python
session = VipSession(output_dir='./vip_outputs/my_session')
```
If `ouput_dir` is the default (like above), **just provide the `session_name`**:
```python
session = VipSession('my_session') # Equivalent to: session = VipSession(session_name='my_session')
```

This will load the session data stored in the backup file (*session_data.json*). This backup system is useful to:
- [Run a *session* intermittently][progress] without a dedicated variable ;
- [Relaunch a *session*][finished] after it has been "finished".

[progress]: #run-a-session-intermittently "Run a Session Intermittently"
[finished]: #relaunch-a-finished-session "Relaunch a Finished Session"

#### Run a *Session* Intermittently

Some pipeline runs can take hours or days.
These runs should be monitored on the [VIP portal](vip-portal) while turning off your Python interpreter.
Using an identifiable `session_name`, the procedure can be left at any time and resumed with an identical VipSession object.
```python
# Connect with VIP
VipSession.init(api_key="VIP_API_KEY")
# Start a Session with a new name and upload your dataset
VipSession("my_session").upload_inputs(input_dir=...)
# When the upload is over, launch the pipeline
VipSession("my_session").launch_pipeline(pipeline_id=..., input_settings=...)
#
# Exit your Python interpreter and monitor the pipeline execution on VIP website.
#
# When the execution is over, connect with VIP again and download the outputs
VipSession.init(api_key="VIP_API_KEY", session_name="my_session").download_ouputs()
# When the download is over, remove your data from VIP servers
VipSession("my_session").finish()
```
Unlike our [first examples][get-started], here the `VipSession` instance is run without a dedicated variable. If for some reason a personalized `output_dir` has been set, it must be used instead of `session_name` to resume the *session* (like [above][backup]).

#### Relaunch a Finished *Session*

A `VipSession` instance can also be resumed after running `finish()`.
For example, to display a short report about previous pipeline runs:
```python
VipSession("my_session").monitor_workflows()
```

The same `VipSession` instance can be used to relaunch a full *upload-run-download* procedure with the same parameters:
```python
# Connect with VIP
VipSession.init(api_key="VIP_API_KEY")
# Relaunch the full procedure & finish
VipSession("my_session").run_session().finish()
```

In that case, the new pipeline outputs will be downloaded next to the previous ones.
This feature can be used to run repeatability experiments.


### Manipulate VipSession Properties
[manipulate-properties]: #manipulate-vipsession-properties "Manipulate VipSession Properties"

#### Use Dot Notation

As stated above, properties of a VipSession instance can be **set**, **accessed** and **deleted** using dot notation. For example:
```python
my_session = VipSession() # Instantiate an anonymous session
print(my_session.session_name) # Access the default value for `session_name`
my_session.input_dir = "/path/to/my/data" # Set the input directory
del my_session.input_dir # Delete the input directory
```

#### Edit an Incorrect Property

To avoid accidental loss of metadata, a session property cannot be modified directly. For instance:
```python
my_session = VipSession(input_dir="/path/to/may/data") 
# Ooops, there is some typo in "may/data". Let's try to fix it :
my_session.input_dir = "/path/to/my/data" # this will throw an error
```
throws the following error: 
```
ValueError: 'local_input_dir' is already set
```
This can be addressed by *deleting* the property *before* editing its value:
```python
my_session = VipSession(input_dir="/path/to/may/data") # Value with typo
del my_session.input_dir # Delete the wrong value
my_session.input_dir = "/path/to/my/data" # Set the correct value
```

#### Properties and their Default Values
[TODO]

### Run Multiple `VipSession`s on the Same Dataset
[multiple_vipsessions]: #run-multiple-vipsessions-on-the-same-dataset "Run Multiple VipSessions on the Same Dataset"

As stated [above][get-started], **a single _session_** allows to run **a single `pipeline_id`** on **a single `input_dir`** with **a single `input_settings`**. To run a pipeline with *multiple `input_settings`*, or *multiple `pipeline_id`*, one has to use multiple `VipSession` instances.

#### Illustration
Assume one has *two parameter sets* (`input_settings` A & B) for running the same application on the same dataset:
```python
# Input data
my_dataset = "path/to/my/data"
# Pipeline
pipeline_id = "my_app/0.1"
# Parameters sets
settings_A = {...} # Parameter set A
settings_B = {...} # Parameter set B
# Connect with VIP
VipSession.init(api_key="VIP_API_KEY")
```

#### Without `get_inputs()`

To run `pipeline_id` with `settings_A` *and* `settings_B`, one has to run two different sessions:
```python
# Run Session A with settings A and finish
session_a = VipSession(input_dir=my_dataset, [...], input_settings=settings_A
  ).run_session().finish()
# Run Session B with settings B and finish
session_b = VipSession(input_dir=my_dataset, [...], input_settings=settings_B
  ).run_session().finish()
```

By default, each dataset uploaded on VIP is bound to a single _session_. In the above example, `my_dataset` is thus **uploaded twice** on VIP servers (and removed twice at the end), as depicted in the diagram below.

<img src="imgs/VipSession_without_get_inputs.png" alt="without_get_inputs" height="250" title="Two VIP Sessions without get_inputs()"/>

#### With `get_inputs()`

Unlike the previous example, `VipSession` method `get_inputs()` allows *session B* to accces the inputs of *session A* on VIP servers.
```python
session_b.get_inputs(session_a)
```

`get_inputs()` is meant to **replace** `upload_inputs()` during [Step 2][steps] of the *upload-run-download* procedure.

```python
# Create & Run Session A
session_a = VipSession(input_dir=my_dataset, [...], input_settings=settings_A
  ).run_session() # Do not run `finish()` until the entire process is over.
# Create, Run & Finish Session B with `get_inputs`
session_b = VipSession([...], input_settings=settings_B
  ).get_inputs(session_a # Access the inputs of Session A
  ).run_session(update_files=False # Run the session by skipping the "upload" step
  ).finish() # Run & Finish Session B
# Finish Session A
session_a.finish()
```

**/!\\** Running `finish()` on *session B* will not remove its inputs (i.e., `my_dataset`) from VIP servers, because they belong to *session A* (see the diagram below).

<img src="imgs/VipSession_with_get_inputs.png" alt="with_get_inputs" height="220" title="Two VIP Sessions with get_inputs()"/>

#### Generalization

The previous case can be easily generalized to any number of VipSession instances. A smart way to implement this is provided in this [Python script](examples/tutorials/demo-multiple-sessions.py) to avoid overloading the doc.

Besides saving memory on VIP servers, **smart management of the input dataset can save a lot of time**, since there is no easy way to parallelize the upload and download steps between multiple sessions.

---

# VipLauncher

[Description to come]

---

# VipCI

[Description to come]

---

# vip.py

This module is used to communicate with the VIP API using the Python
language.
This is a synchronous implementation.

## How to use it

This module works like a state machine: first, set the `apikey` with
`setApiKey(str)`. All the functions will refer to this `apikey` later.

## Raised errors

If there are any VIP issues, functions will raise *RuntimeError* errors. See
`detect_errors` and `manage_errors` functions if you want to change this.

## Improvement

- an asynchronous version
- missing a few optional parameters for some functions (not important)

---

# Manage your VIP Account

## Create a VIP account

### Fill the Registration Form

[TODO]

### Register to your Application Group

[TODO]

## Get a VIP API key

### Find your API key

One can easily create a VIP account to generate one's API key: the procedure is summarized in the image below.

<img src="imgs/VIP_key.png" alt="VIP API key" height="250" title="How to get a VIP API key"/>

*Useful tips*:
- In **Step 3**, the user is asked to select an *Account Type*. This can be modified later: select only the entries relevant to your research area.
- In **Step 6**, scroll down to the bottom of the page.

If you encounter any issues, please contact us at:
<vip-support@creatis.insa-lyon.fr>

### Hide your API key

[TODO]

In the following cell, `VIP_API_KEY` key can be replaced by:
- Your API key (as a string)
- A path to a text file containing your API key
- The name of an environment variable containing your API key.

---

# Release Notes

## Future Work

**Major changes**
- New file management class for specific user needs
- Public test suite and integration to PyPI

**Minor changes**
- `VipLauncher`: method to kill VIP executions 
- Maximize log width with `textwrap`
- Speed up upload / download time

## Current Release

### June 2023

**Major changes**
- Class [`VipLauncher`](#viplauncher) is introduced for specific user needs, as a parent of `VipSession` & `VipCI` for better maintainability.
- Session properties (`session_name`, `pipeline_id`, *etc.*) can now be safely accessed and modified in all "`Vip*`" classes;
- A list of available pipelines and detailed informations about each pipeline can be displayed through new class method `show_pipeline()`;

**Minor changes**
- The `verbose` state is now common to all instance methods and can be modified through the public interface (`self.verbose`);
- Any file path can be provided as *os.PathLike* object (including `pathlib` objects);
- Class `VipSession`: outputs from unfinished workflows can be now downloaded using argument `get_status`;
- Argument `force_remove` is no more available in the VipSession/VipLauncher method `finish()`;
- Bugs corrections and improvements following user remarks

## Past Releases

### April 2023
- Initial release of class [`VipCI`](#vipci): interacts with Girder datasets (tailored for CI tests in the ReproVIP project).

### March 2023
- Initial release of class [`VipSession`](#vipsession): user-friendly interface to run VIP jobs on local dataset.

### Sept. 2018
- Initial release of package [`vip.py`](#vippy): generic methods to interact with the VIP REST API.

