[vip-portal]: https://vip.creatis.insa-lyon.fr/ "https://vip.creatis.insa-lyon.fr/"
[vipsession-tutorial]: #examples/tutorials/demo-vipsession.ipynb "VipSession Tutorial"

# VipSession

```python
from vip_client import VipSession
```

This Python class launches executions on [VIP][vip-portal] from any machine where the dataset is stored (*e.g.*, one's server or PC). 
Running an application ("pipeline") on VIP implies the following process:

*__Upload__ one's dataset on VIP servers* **>>** *__Run__ the pipeline* **>>** *__Download__ the results from VIP servers*.

<img src="imgs/Upload_Run_Download.png" alt="Procedure" height="200" title="The Upload-Run-Download Procedure"/>

`VipSession` implements this procedure in a few basic steps. 

- [Get Started](#get-started)
  - [Basic Steps][steps]
  - [VipSession Inputs](#vipsession-inputs)
  - [VipSession Outputs](#vipsession-outputs)
- [Best Practices](#best-practices)
  - [Use VipSession Shortcuts][shortcuts]
  - [Use show_pipeline() to Set VipSession Inputs][show_pipeline]
  - [Parallelize your Executions][parallelize]
  - [Use VipSession Backup][backup]
  - [Manipulate VipSession Properties][manipulate-properties]
  - [Run Multiple Sessions on the Same Dataset][multiple-sessions]

---

# Get Started
[get-started]: #get-started "Get Started"

This section presents the main [methods][steps], [inputs](#vipsession-inputs) and [outputs](#vipsession-outputs) of the `VipSession` class. A [tutorial][vipsession-tutorial] is also available on Binder.

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/virtual-imaging-platform/VIP-python-client/HEAD?labpath=examples%2Ftutorials%2Fdemo-vipsession.ipynb)

## Basic Steps
[steps]: #basic-steps "Basic Steps"

Any session with the Python client starts by initiating a connection with VIP.
```python
# Step 0. Connect with VIP (1 call applies to multiple VipSession instances)
VipSession.init(api_key="VIP_API_KEY") # << paste your API key here
```
Here `"VIP_API_KEY"` should be replaced by user's own [API key](account.md#get-a-vip-api-key "Get a VIP API Key"). There are several ways to [avoid hardcoding your key](account.md#hide-your-api-key "Hide your API Key").

Once connection with VIP is established, the *upload-run-download* procedure is achieved through 6 basic steps.

1. **Create** a `VipSession` instance ("*session*");
```python
# Step 1. Create a Session
session = VipSession(session_name="my-session")
```
2. **Upload** the your dataset on VIP servers;
```python
# Step 2. Upload the input data
session.upload_inputs(input_dir="path/to/my/dataset")
```
3. **Launch** your application on VIP;
```python
# Step 3. Launch a pipeline on VIP
session.launch_pipeline(pipeline_id="my_app/0.1", input_settings=my_settings)
```
4. **Monitor** its progress on VIP until all executions are over;
```python
# Step 4. Monitor the pipeline's workflow(s)
session.monitor_workflows()
```
5. **Download** the output files from VIP servers when all executions are over;
```python
# Step 5. Download the outputs 
session.download_outputs()
```
6. **Finish** the *session* by removing your input/output data from VIP servers.
```python
# Step 6. Remove the data from VIP servers
session.finish()
```

In this example, `VipSession` [properties](#vipsession-inputs "VipSession Inputs") (*e.g.* `session_name`, `input_dir`) are progressively passed as inputs during steps 1, 2 & 3. They can also be defined when instanciating `VipSession` (*i.e.* during `step 1` or `step 0`, see [below][shortcuts]). Additionnally, VipSession methods accept specific arguments (*e.g.* `nb_runs`, `refresh_time`) to fine-tune their behavior. See each method's doc-string for detailed information.

## VipSession Inputs

A valid [API key](account.md#find-your-api-key) is a prerequisite for communicating with VIP .
A single handshake applies to several `VipSession` instances.

0. `api_key` (*str*, **required**): your VIP API key.
    - See `VipSession.init()` docstring for more information.

One `VipSession` instance allows you to run __(1) one pipeline__ on __(2) one dataset__ with __(3) one parameter set__. These are 3 required inputs:

1. `pipeline_id` (*str*, **required**): The name of your pipeline (application) on VIP.
    - Run `VipSession.show_pipeline("my_app")` to [show the pipeline identifiers][show_pipeline] relative to `"my_app"`.
    - Usually in the format: *application_name*/*version*.
2. `input_dir` (*str | os.PathLike*, **required**): The local path to your dataset.
    - This directory will be uploaded on VIP before launching the pipeline.
3. `input_settings` (*dict*, **required**): All parameters needed to run the pipeline.
    - Run `VipSession.show_pipeline(`*`pipeline_id`*`)` to [display the parameters][show_pipeline] for `pipeline_id`.
    - The dictionary can contain any object that can be converted to strings, or lists of such objects.
    - Parameters with a *list of values* launch [*parallel jobs*][parallelize] on VIP.

Finally, 3 optional inputs can be provided depending on user needs:

4. `session_name` (*str*, **recommended**) A name to identify this session and the corresponding outputs. 
    - *Default value: 'VipSession-[date]-[time]-[id]'*
5. `output_dir` (*str | os.PathLike*, **optional**) Local path to the directory where: 
    - session properties will be saved; 
    - pipeline outputs will be downloaded from VIP servers.
    - *Default value: './vip_outputs/`session_name`'*

6. `verbose` (bool, **optional**) Verbose state of the current *session*.
    - The *session* will display logs when True (default value).

Inputs 1 to 6 are `VipSession`'s main **properties**: they fully define its behavior throughout the *upload-run-download* procedure. They can be accessed, set and deleted with classical dot notation: `session.property` (see [below][manipulate-properties] for detailed infromation). 

## VipSession Outputs

When running a VipSession instance for the first time, its output directory (`output_dir`) is made to store the *session* [backup file](#session-backup) and later the [pipeline outputs](#pipeline-outputs).

### Session Backup

At the end of steps 2, 3, 4, 5 & 6, session properties (*e.g.*, `session_name`, `pipeline_id`) are automatically saved in a backup file (*session_data.json*).
This backup can be used to [resume a finished or running *session*][backup].

### Pipeline Outputs

Pipeline results are stored in `output_dir` mirroring their structure on VIP servers. By default, when the VIP implementation of the pipeline produces a tarball (`*.tar.gz`), its contents are extracted to a folder named after that archive. 

A typical output directory will have the following structure: 
```
my-session
├── 02-02-2023_09:21:23
│   └── job_results.tgz
│       ├── file_x
│       └── file_y
└── session_data.json
```

Where:
- `file_x` & `file_y` are the pipeline outputs;
- `job_results.tgz` contains results from the same *job*;
- `02-02-2023_09:21:23` is named after the starting time of the *workflow*;
- `session_data.json` is the session backup file.

See [below](#jobs-and-workflows "Jobs and Workflows") for detailed information about *jobs* and *workflows*.

# Best Practices

In this section you will learn how to [use VipSession shortcuts][shortcuts], [write `VipSession` inputs][show_pipeline], [parallelize your executions][parallelize], [use `VipSession` backup][backup], [manipulate `VipSession` properties][manipulate-properties] and [run multiple *sessions* on the same dataset][multiple-sessions].

## Use VipSession Shortcuts
[shortcuts]: #use-vipsession-shortcuts "Use VipSession Shortcuts"

VipSession properties (*e.g.*, `input_dir`, `pipeline_id`, `input_settings`) can be declared at instantiation:
```python
session = VipSession(session_name=..., input_dir=..., pipeline_id=..., input_settings=..., ouput_dir=...)
```
*Setting all session properties at instantiation allows earlier detection of common mistakes, like missing parameters or input files.*

This can also be done while handshaking with VIP ([steps 0-1][steps]) through `VipSession.init()`:
```python
session = VipSession.init(api_key=..., session_name=..., input_dir=..., pipeline_id=..., input_settings=..., ouput_dir=...)
```

When all properties are set, the full *upload-run-download* process ([steps 2-5][steps]) can be performed with `run_session()`:
```python
session.run_session()
```
*Do not forget to remove your temporary data from VIP after downloading the outputs (`session.finish()`).*

All `VipSession` methods can be run in cascade, so everything holds in a single command:
```python
VipSession.init(api_key=..., session_name=..., input_dir=..., [...]).run_session().finish()
```

## Use `show_pipeline()` to Set VipSession Inputs
[show_pipeline]: #use-show_pipeline-to-set-vipsession-inputs "Use show_pipeline() to Set VipSession Inputs"

The class method `show_pipeline()` can help you getting a `pipeline_id` and writing your `input_settings`. 

### Get the `pipeline_id`

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
*__N.B.__: If the output is "`(!) No pipeline found for pattern 'freesurfer'`", you may need to register with the pipeline's **group** on the [VIP Portal][vip-portal]. The procedure is written [here](account.md#join-a-new-group).*

### Write the `input_settings`

#### Parameter Names

When `show_pipeline()` finds a single match among VIP applications, it displays a full description of the pipeline, including the parameters that can be fed in your `input_settings`. For example: 
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
    [FILE] Single NIFTI file from series. [...]
OPTIONAL..............................................................
- 3T_flag
    [BOOLEAN] The -3T flag enables two specific options in recon-all 
    for images acquired with a 3T scanner:  [...]
======================================================================
```
The list of parameters below "*INPUT_SETTINGS*" can be used to build your `input_settings` for VipSession. These must include at least the "*REQUIRED*" parameters.
```python
input_settings = {
  "directives": "-all", # Options for recon-all, see Fressurfer documentation
  "license": "path/to/my/license.txt", # FreeSurfer License
  "nifti": "path/to/my/input/file.nii.gz", # Input file
  # [...]
}
```

#### Parameter Values

The input type is displayed at the beginning of each parameter description.
- **[STRING]**: input should be of type `str`. *(for advanced users, it can be of any Python type that can converts to `str` (*e.g.* `bool`, `int`) provided the converted `str` value fits the pipeline)*
- **[BOOLEAN]**: input should be of type `str`, containing exactly `"true"` or `"false"` (please **mind the case**).
- **[FILE]**: input requires a valid path to some file, either on **VIP** or in the **local** file system. This path can be `str` or any `os.PathLike` object, including from [`pathlib`](https://docs.python.org/3/library/pathlib.html).

For each parameter in the `input_settings`, you can can also provide a **list** of values. This launches parallel jobs on VIP, as explained below.

## Parallelize your Executions
[parallelize]: #parallelize-your-executions "Parallelize your Executions"

### Illustration

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
  ] # End of list
  # [...]
}
```
With the above `input_settings`, the VipSession instance will submit N *jobs* to VIP (one per input file). 

### Jobs and Workflows

A **job** is a single task run by the pipeline on VIP, *e.g.*, with 1 input file and 1 parameter set. When *lists* of files or parameters are provided in the `input_settings`, the corresponding jobs run in parallel (the pipeline runs on all files and parameters at the same time).

A **workflow** is a collection of jobs submitted at the same time. A single `VipSession` instance can launch multiple workflows on the same `pipeline_id` with the same `input_settings` (see [below](#caveats--comments)).

In practice, VIP pipelines can be run on all types of datasets by following these three rules:
1. A **single job** is submitted on VIP when `input_settings` are filled with a **single value** for each parameter;
2. A **single workflow** is used to run **multiple jobs** in parallel, when providing a **list of values** in the `input_settings`;
3. A **single VipSession instance** can be used to run **multiple workflows** on the same `pipeline_id` with the same `input_settings` ;

### Output files

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

### Caveats & Comments

* For large datasets, it is recommended to launch **separate workflows of a few hundred jobs** to limit the risk of errors.

* One `VipSession` instance can launch multiple workflows: 
  - by calling `launch_pipeline()` several times, 
  - by increasing argument `nb_runs`, 
  - by calling `run_session()` several times, 
  - by [re-starting the session](#relaunch-a-finished-session) after it was "finished". 

* In the two first options, the workflows will run in parallel on VIP. To run *parallel workflows* on VIP, please [contact VIP support](<vip-support@creatis.insa-lyon.fr>) to **increase your execution capacity** (1 by default).

* Multiple Vipsession instances can be smartly used to run multiple `pipeline_id` and multiple `input_settings` on the same dataset. See [below][multiple-sessions] for a detailed procedure.

## Use VipSession Backup
[backup]: #use-vipsession-backup "Use VipSession Backup"

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

### Run a *Session* Intermittently
[progress]: #run-a-session-intermittently "Run a Session Intermittently"

Some pipeline runs can take hours or days.
These runs should be monitored on the [VIP portal][vip-portal] while turning off your Python interpreter.
Using an identifiable `session_name`, the procedure can be left at any time and resumed with an identical VipSession object.
```python
# Connect with VIP
VipSession.init(api_key="VIP_API_KEY")
# Start a Session with a new name and upload your dataset
VipSession("my_session").upload_inputs(input_dir=...)
# When the upload is over, launch the pipeline
VipSession("my_session").launch_pipeline(pipeline_id=..., input_settings=...)
# ----------------------------------------------------------------------------------
# Exit your Python interpreter and monitor the pipeline execution on the VIP portal
# ----------------------------------------------------------------------------------
# When the execution is over, connect with VIP again and download the outputs
VipSession.init(api_key="VIP_API_KEY", session_name="my_session").download_ouputs()
# When the download is over, remove your data from VIP servers
VipSession("my_session").finish()
```
In this example, the `VipSession` instance is run without a dedicated variable. 

*If for some reason a personalized `output_dir` has been set, it must be used instead of `session_name` to resume the `VipSession` instance (like [above][backup]).*

### Relaunch a Finished *Session*
[finished]: #relaunch-a-finished-session "Relaunch a Finished Session"

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

## Manipulate VipSession Properties
[manipulate-properties]: #manipulate-vipsession-properties "Manipulate VipSession Properties"

### Use Dot Notation

As stated above, properties of a VipSession instance can be **set**, **accessed** and **deleted** using dot notation. For example:
```python
my_session = VipSession() # Instantiate an anonymous session
print(my_session.session_name) # Access the default value for `session_name`
my_session.input_dir = "/path/to/my/data" # Set the input directory
del my_session.input_dir # Delete the input directory
```

### Edit an Incorrect Property

To avoid accidental loss of metadata, a session property cannot be directly modified. For instance:
```python
my_session = VipSession(input_dir="/path/to/may/data") 
# Oops, there is some typo in "may/data". Let's try to fix it :
my_session.input_dir = "/path/to/my/data" # this will throw an error
```
throws the following error: 
```
ValueError: 'local_input_dir' is already set
```
This must be addressed by *deleting* the property *before* editing its value:
```python
my_session = VipSession(input_dir="/path/to/may/data") # Value with typo
del my_session.input_dir # Delete the wrong value
my_session.input_dir = "/path/to/my/data" # Set the correct value
```

### Additional Properties

Beyond the six [`VipSession` inputs](#vipsession-inputs) introduced above, additional properties are accessible and editable with dot (`.`) notation.
multiple-sessions
Property | Description | Default Value
---: | :--- | :---
`local_input_dir` | Dataset location (`input_dir` is an alias) | *None* (str)
`local_output_dir` | Results location (`output_dir` is an alias) | *"vip_outputs/`session_name`"*
`vip_input_dir` | Dataset location on VIP (temporary data) | *"/vip/Home/API/`session_name`/INPUTS"*
`vip_output_dir` | Results location on VIP (temporary data) | *"/vip/Home/API/`session_name`/OUTPUTS"*
`workflows` | Workflows inventory with metadata | *{}* (dict)

Setting personnalized `vip_input_dir` and `vip_output_dir` can fine-tune `VipSession` behaviour and answer specific user needs.
This is not without risk for user metadata. 

An example of user-specific need is sharing the same dataset between several *sessions* **after** it has been uploaded on VIP. This can be done safely with method `get_inputs()`, as explained below. 

## Run Multiple Sessions on the Same Dataset

[multiple-sessions]: #run-multiple-sessions-on-the-same-dataset "Run Multiple Sessions on the Same Dataset"

As stated [above][get-started], **a single _session_** allows to run **a single `pipeline_id`** on **a single `input_dir`** with **a single `input_settings`**. To run a pipeline with *multiple `input_settings`*, or *multiple `pipeline_id`*, one has to use multiple `VipSession` instances.

### Illustration
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

### Without `get_inputs()`

To run `pipeline_id` with `settings_A` *and* `settings_B`, one has to run two different sessions:
```python
# Run & Finish Session A with settings A
session_a = VipSession(input_dir=my_dataset, [...], input_settings=settings_A)
session_a.run_session().finish()
# Run & Finish Session B with settings B
session_b = VipSession(input_dir=my_dataset, [...], input_settings=settings_B)
session_b.run_session().finish()
```

By default, each dataset uploaded on VIP is bound to a single _session_. In the above example, `my_dataset` is thus **uploaded twice** on VIP servers (and removed twice at the end), as depicted in the diagram below.

<img src="imgs/VipSession_without_get_inputs.png" alt="without_get_inputs" height="250" title="Two VIP Sessions without get_inputs()"/>

### With `get_inputs()`

Unlike the previous example, `VipSession` method `get_inputs()` allows *session B* to accces the inputs of *session A* on VIP servers.
```python
session_b.get_inputs(session_a)
```

`get_inputs()` is meant to **replace** `upload_inputs()` during [Step 2][steps] of the *upload-run-download* procedure.

```python
# Run Session A
session_a = VipSession(input_dir=my_dataset, [...], input_settings=settings_A)
session_a.run_session() # Do not run `finish()` until the entire process is over.
# Run & Finish Session B with `get_inputs()`
session_b = VipSession([...], input_settings=settings_B)
session_b.get_inputs(session_a) # Access the inputs of Session A
session_b.run_session(update_files=False).finish() # (skips the "upload" step)
# Finish Session A
session_a.finish()
```

**/!\\** Running `finish()` on *session B* will not remove its inputs (i.e., `my_dataset`) from VIP servers, because they belong to *session A* (see the diagram below).

<img src="imgs/VipSession_with_get_inputs.png" alt="with_get_inputs" height="220" title="Two VIP Sessions with get_inputs()"/>

### Generalization

The previous case can be easily generalized to any number of VipSession instances. A smart way to implement this is provided **in this [Python script](../examples/tutorials/demo-multiple-sessions.py)**.

Besides saving memory on VIP servers, **smart management of the input dataset can save a lot of time**, since there is no easy way to parallelize the upload and download steps between multiple sessions.

---