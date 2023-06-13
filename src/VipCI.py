from __future__ import annotations
import os
import time
from pathlib import *

import girder_client
import vip
from VipLauncher import VipLauncher

class VipCI(VipLauncher):
    """
    Python class to run VIP pipelines on datasets located on Girder.

<<<<<<< HEAD:src/VipCI.py

    1 "session" allows to run 1 pipeline with 1 parameter set (any number of pipeline runs).
    Minimal inputs:
    - `pipeline_id` (str) Name of the pipeline in VIP nomenclature.
        Usually in format : "[application_name]/[version]".
=======
    A single instance allows to run 1 pipeline with 1 parameter set (any number of runs).
    Pipeline runs need at least three inputs:
    - `pipeline_id` (str) Name of the pipeline. 
>>>>>>> future-branch:VipCI.py
    - `input_settings` (dict) All parameters needed to run the pipeline.
    - `output_dir` (str) Path to a Girder folder where execution results will be stored.

<<<<<<< HEAD:src/VipCI.py
    N.B.: all instance methods require that `VipSession.init()` has been called with:
    - a valid VIP API key.
=======
    N.B.: all instance methods require that `VipCI.init()` has been called with:
    - a valid VIP API key;
>>>>>>> future-branch:VipCI.py
    - a valid Girder API key.
    """

    ##################
    ################ Class Attributes ##################
    ##################

<<<<<<< HEAD:src/VipCI.py
    _GIRDER_URL = "https://pilot-warehouse.creatis.insa-lyon.fr/api/v1"
    _PREFIX_GIRDER_ID = "pilotGirder"
    _PREFIX_GIRDER_PATH = "/collection"
=======
    # --- Overriden from the parent class ---

    # Class name
    __name__ = "VipCI"
    # Properties to save / display for this class
    _PROPERTIES = [
        "session_name", 
        "pipeline_id",
        "vip_output_dir", 
        "input_settings", 
        "workflows"
    ]
    # Default location for VIP inputs/outputs (different from the parent class)
    _SERVER_NAME = "girder"
    # Prefix that defines a Girder path 
    _SERVER_PATH_PREFIX = "/collection"
    # Default backup location 
    # (set to None to avoid saving and loading backup files)
    _BACKUP_LOCATION = "girder"

    # --- New Attributes ---

    # Prefix that defines a Girder ID
    _GIRDER_ID_PREFIX = "pilotGirder"
    # Grider portal
    _GIRDER_PORTAL = 'https://pilot-warehouse.creatis.insa-lyon.fr/api/v1'

                    #################
    ################ Main Properties ##################
                    ################# 
    
    # Same as the parent class
>>>>>>> future-branch:VipCI.py

    #############
    ################ Constructor ##################
    #############
    def __init__(
<<<<<<< HEAD:src/VipCI.py
        self,
        output_dir="",
        pipeline_id="",
        input_settings: dict = {},
        session_name="",
        verbose=True,
    ) -> None:
        """
        Create a VipCI instance from keyword arguments.
        Displays informations if `verbose` is True.
=======
        self, output_dir=None, pipeline_id: str=None, input_settings: dict=None, 
        session_name: str=None, verbose: bool=None
    ) -> None:
        """
        Creates a VipCI instance and sets its properties from keyword arguments.
>>>>>>> future-branch:VipCI.py

        ## Parameters
        - `output_dir` (str | os.PathLike) Path to a Girder folder where execution results will be stored.
            - Does not need to exist
            - Usually in format : "/collection/[collection_name]/[path_to_folder]"
            - User must have read/write permissions on the Girder collection/folder.

<<<<<<< HEAD:src/VipCI.py
        - `pipeline_id` (str) Name of your pipeline in VIP.
            Usually in format : "[application_name]/[version]".
=======
        - `pipeline_id` (str) Name of your pipeline in VIP. 
            - Usually in format : *application_name*/*version*.
            - Run VipLauncher.show_pipeline() to display available pipelines.
>>>>>>> future-branch:VipCI.py

        - `input_settings` (dict) All parameters needed to run the pipeline.
            - Run VipSession.show_pipeline(`pipeline_id`) to display these parameters.
            - The dictionary can contain any object that can be converted to strings, or lists of such objects.
            - Lists of parameters launch parallel workflows on VIP.

<<<<<<< HEAD:src/VipCI.py
        If `output_dir` leads to data from a previous session,
        all properties will be loaded from the folder metadata on Girder.
=======
        - `session_name` [Optional/Recommended] (str) A name to identify this session.
            - Default value: 'VipCI-[date]-[time]-[id]'
        
        - `verbose` [Optional] (bool) Verbose mode for this instance.
            - If True, instance methods will display logs;
            - If False, instance methods will run silently.

        `session_name` is only set at instantiation; other properties can be set later in function calls.
        If `output_dir` leads to data from a previous session, properties will be loaded from the metadata on Girder.
>>>>>>> future-branch:VipCI.py
        """
        # Initialize with the name, pipeline and input settings
        super().__init__(
<<<<<<< HEAD:src/VipCI.py
            session_name=session_name,
            output_dir=output_dir,
            pipeline_id=pipeline_id,
            input_settings=input_settings,
            verbose=verbose,
        )
        # Update the output directory
        self._vip_output_dir = output_dir

=======
            output_dir = output_dir,
            session_name = session_name, 
            pipeline_id = pipeline_id, 
            input_settings = input_settings,
            verbose = verbose
        )
        # End display
        if any([session_name, output_dir]) and (self.__name__ == "VipCI"): 
            self._print()
>>>>>>> future-branch:VipCI.py
    # ------------------------------------------------

    ################
    ################ Public Methods ##################
    ################

    #################################################
    # ($A) Manage a session from start to finish
    #################################################

    # Login to VIP and Girder
    @classmethod
    def init(cls, vip_key="VIP_API_KEY", girder_key="GIRDER_API_KEY", verbose=True, **kwargs) -> VipCI:
        """
<<<<<<< HEAD:src/VipCI.py
        Handshakes with VIP and Girder using your own API keys.
        Prints a list of pipelines available with the API key, unless `verbose` is False.
        Returns a VipSession instance which properties can be provided as keyword arguments (`kwargs`).
=======
        Handshakes with VIP using your own API key. 
        Returns a class instance which properties can be provided as keyword arguments.
        
        ## Parameters
        - `vip_key` (str): VIP API key. This can be either:
            A. [unsafe] A **string litteral** containing your API key,
            B. [safer] A **path to some local file** containing your API key,
            C. [safer] The **name of some environment variable** containing your API key (default: "VIP_API_KEY").
        In cases B or C, the API key will be loaded from the local file or the environment variable. 
>>>>>>> future-branch:VipCI.py

        - `girder_key` (str): Girder API key. Can take the same values as `vip_key`.
        
        - `verbose` (bool): default verbose mode for all instances.
            - If True, all instances will display logs by default;
            - If False, all instance methods will run silently by default.

<<<<<<< HEAD:src/VipCI.py
        In cases B or C, the API key will be loaded from the local file or the environment variable.
=======
        - `kwargs` [Optional] (dict): keyword arguments or dictionnary setting properties of the returned instance.     
>>>>>>> future-branch:VipCI.py
        """
        # Initiate a Vip Session
        super().init(api_key=vip_key)
        # Instantiate a Girder client
        cls._girder_client = girder_client.GirderClient(apiUrl=cls._GIRDER_PORTAL)
        # Check if `girder_key` is in a local file or environment variable
<<<<<<< HEAD:src/VipCI.py
        if os.path.exists(girder_key):  # local file
            with open(girder_key, "r") as kfile:
                true_key = kfile.read().strip()
        elif girder_key in os.environ:  # environment variable
            true_key = os.environ[girder_key]
        else:  # string litteral
            true_key = girder_key
        # Authenticate with Girdre API key
        cls._girder_client.authenticate(apiKey=true_key)
        # Return a VipCI instance for method cascading
        return VipCI(verbose=True if kwargs else False, **kwargs)

    # ------------------------------------------------

    # Temporary mock function for upload_inputs()
    def upload_inputs(self) -> VipSession:
        """
        This function does not work in VipCI.
        """
        # Print error message
        print("(!) Class VipCI cannot upload local data.")
        # Return for method cascading
        return self

    # ------------------------------------------------

    def launch_pipeline(
        self,
        pipeline_id="",
        input_settings: dict = {},
        output_dir="",
        nb_runs=1,
        verbose=True,
    ) -> VipSession:
=======
        true_key = cls._get_api_key(girder_key)
        # Authenticate with Girder API key
        cls._girder_client.authenticate(apiKey=true_key)
        # Return a VipCI instance for method cascading
        return cls(verbose=(verbose and kwargs), **kwargs)
    # ------------------------------------------------

    def launch_pipeline(
            self, pipeline_id: str=None, input_settings: dict=None, output_dir=None, nb_runs=1, 
            verbose: bool=None
        ) -> VipCI:
>>>>>>> future-branch:VipCI.py
        """
        Launches pipeline executions on VIP.

        Input parameters :
        - `pipeline_id` (str) The name of your pipeline in VIP, 
            usually in format : *application_name*/*version*.
        - `input_settings` (dict) All parameters needed to run the pipeline.
<<<<<<< HEAD:src/VipCI.py
        - `output_dir` (str) Path to the Girder folder where execution results will be stored.
        - `nb_runs` (int) Number of parallel runs of the same pipeline with the same settings.
        - Set `verbose` to False to run silently.

=======
            - Run VipSession.show_pipeline(`pipeline_id`) to display these parameters.
            - The dictionary can contain any object that can be converted to strings, or lists of such objects.
            - Lists of parameters launch parallel workflows on VIP.
        - `output_dir` (str) Path to the VIP folder where execution results will be stored.
        - `nb_runs` (int) Number of parallel workflows to launch with the same settings.
        
>>>>>>> future-branch:VipCI.py
        Default behaviour:
        - Raises AssertionError in case of wrong inputs 
        - Raises RuntimeError in case of failure on VIP servers.
        - In any case, session is backed up after pipeline launch
        """
<<<<<<< HEAD:src/VipCI.py
        if verbose:
            print("\n<<< LAUNCH PIPELINE >>>\n")
            print("Checking parameters and data ... ", end="")
        # Update the pipeline identifier
        if pipeline_id:
            # check conflicts with instance value
            if self._pipeline_id and (pipeline_id != self._pipeline_id):
                raise ValueError(
                    f"Pipeline identifier is already set for this session ('{self._pipeline_id}')."
                )
            # update instance property
            self._set(pipeline_id=pipeline_id)
        # Check pipeline existence
        if not self._pipeline_id:
            raise TypeError(
                "Please provide a pipeline identifier for Session: %s"
                % self._session_name
            )
        # Check the pipeline identifier
        self._check_pipeline_id()
        # Update the output directory
        if output_dir:
            self._vip_output_dir = output_dir
        # Check existence
        if not self._vip_output_dir:
            raise TypeError(
                "Please provide an output directory for Session: %s"
                % self._session_name
            )
        # Ensure the directory exists
        self._make_dir(
            path=self._vip_output_dir,
            location="girder",
            description=f"VIP executions from the VipCI client under Session name: '{self._session_name}'",
        )
        # Update the input parameters
        if input_settings:
            # check conflicts with instance value
            if self._input_settings and (
                self._vip_input_settings(input_settings) != self._input_settings
            ):
                raise ValueError(
                    f"Input settings are already set for Session: %s"
                    % self._session_name
                )
            self._set(input_settings=input_settings)
        # Check existence
        if not self._input_settings:
            raise TypeError(
                f"Please provide input parameters for Session: %s" % self._session_name
            )
        # Check content
        try:
            assert (
                self._check_input_settings()
            ), "Input parameters could not be checked."
        except RuntimeError as handled_error:
            # this may throw a RuntimeError (handled upstream)
            # if pipeline definition could not be loaded from VIP
            if verbose:
                print("\n(!) Input settings could not be checked.")
            raise handled_error
        if verbose:
            print("Done.\n")
        # First Display
        if verbose:
            print("Launching %d new execution(s) on VIP" % nb_runs)
            print("-------------------------------------")
            print("\tSession Name:", self._session_name)
            print("\tPipeline Identifier:", self._pipeline_id)
            print("\tStarted workflows:", end="\n\t\t")
        # Launch all executions in parallel on VIP
        try:
            for nEx in range(nb_runs):
                # Create a workflow-specific result directory
                res_path = pathlib.PurePosixPath(self._vip_output_dir) / time.strftime(
                    "%Y-%m-%d_%H:%M:%S", time.localtime()
                )  # no way to rename later with workflow_id
                res_id = self._create_dir(
                    path=res_path,
                    location="girder",
                    description="VIP outputs from a single workflow",
                )["_id"]
                # Update the input_settings with new results directory
                self._input_settings["results-directory"] = self._vip_girder_id(res_id)
                # Initiate Execution
                workflow_id = vip.init_exec(
                    self._pipeline_id, self._session_name, self._input_settings
                )
                # Display the workflow name
                if verbose:
                    print(workflow_id, end=", ")
                # Update the workflow inventory
                self._workflows[workflow_id] = self._get_exec_infos(workflow_id)
                # Add the path to output files
                self._workflows[workflow_id]["output_path"] = str(res_path)
            # Update the input_settings with no results directory
            del self._input_settings["results-directory"]
            # Display success
            if verbose:
                print("\n-------------------------------------")
                print("Done.")
        except RuntimeError as vip_error:
            print("\n-------------------------------------")
            print(f"(!) Stopped after {nEx} execution(s).")
            self._handle_vip_error(vip_error)
        finally:
            # In any case, save session properties on Girder
            self._save_session(verbose=True)
        # Return for method cascading
        return self

    # ------------------------------------------------

    # ($A.4) Monitor worflow executions on VIP
    def monitor_workflows(self, waiting_time=30, verbose=True) -> VipSession:
=======
        return super().launch_pipeline(
            pipeline_id = pipeline_id, # default
            input_settings = input_settings, # default
            output_dir = output_dir, # default
            nb_runs = nb_runs, # default
        )
    # ------------------------------------------------

    # ($A.4) Monitor worflow executions on VIP 
    def monitor_workflows(self, refresh_time=30) -> VipCI:
>>>>>>> future-branch:VipCI.py
        """
        Updates and displays the status of each execution launched in the current session.
        - If an execution is still runnig, updates status every `refresh_time` (seconds) until all runs are done.
        - Displays a full report when all executions are done.
        """
<<<<<<< HEAD:src/VipCI.py
        return super().monitor_workflows(waiting_time=waiting_time, verbose=verbose)

    # ------------------------------------------------

    # Temporary mock function for download_outputs()
    def download_outputs(self) -> VipSession:
        """
        This function does not work in VipCI.
        """
        # Print error message
        print("(!) Class VipCI cannot download distant data.")
        # Return for method cascading
        return self

    # ------------------------------------------------

    # Temporary mock function for finish()
    def finish(self) -> VipSession:
        """
        This function does not work in VipCI.
        """
        # Print error message
        print("(!) Class VipCI cannot delete distant data.")
        # Return for method cascading
        return self

    # ------------------------------------------------

    # ($A.2->A.5) Run a full VIP session
    def run_session(self, nb_runs=1, waiting_time=30, verbose=True) -> VipSession:
=======
        return super().monitor_workflows(refresh_time=refresh_time)
    # ------------------------------------------------

    # ($A.2->A.5) Run a full VIP session 
    def run_session(self, nb_runs=1, refresh_time=30) -> VipCI:
>>>>>>> future-branch:VipCI.py
        """
        Runs a full session from Girder data:
        1. Launches pipeline executions on VIP;
        2. Monitors pipeline executions until they are all over;
            and Adds metadata on Girder output folder.

        /!\ This function assumes that all session properties are already set.
        Optional arguments can be provided:
        - Increase `nb_runs` to run more than 1 execution at once;
        - Set `refresh_time` to modify the default refresh time.
        """
<<<<<<< HEAD:src/VipCI.py
        return (
            # 1. Launch `nb_runs` pipeline executions on VIP
            self.launch_pipeline(nb_runs=nb_runs, verbose=verbose)
            # 2. Monitor pipeline executions until they are over
            .monitor_workflows(waiting_time=waiting_time, verbose=verbose)
        )

=======
        return super().run_session(nb_runs=nb_runs, refresh_time=refresh_time)
>>>>>>> future-branch:VipCI.py
    # ------------------------------------------------

    # ($B.1) Display session properties in their current state
    def display(self) -> VipCI:
        """
        Displays useful properties in JSON format.
        - `session_name` : current session name
        - `pipeline_id`: pipeline identifier
<<<<<<< HEAD:src/VipCI.py
        - `local_output_dir` : path to the pipeline outputs *on your machine*
        - `vip_ouput_dir` : path to the pipeline outputs *in your VIP Home directory*
        - `input_settings` : input parameters sent to VIP
        (note that file locations are bound to `vip_input_dir`).
        - `workflows`: workflow inventory, identifying all pipeline runs in this session.
        """
        # Data to display
        vip_data = {
            "session_name": self._session_name,
            "pipeline_id": self._pipeline_id,
            "vip_output_dir": self._vip_output_dir,
            "workflows": self._workflows,
            "input_settings": self._input_settings,
        }
        # Display
        print(json.dumps(vip_data, indent=4))
        # Return for method cascading
        return self

=======
        - `output_dir` : path to the pipeline outputs
        - `input_settings` : input parameters sent to VIP
        - `workflows`: workflow inventory, identifying all pipeline runs in this session.
        """
        # Return for method cascading
        return super().display()
>>>>>>> future-branch:VipCI.py
    # ------------------------------------------------

    # Mock function for finish()
    def finish(self, verbose: bool=None) -> None:
        """
        This function does not work in VipCI.
        """
<<<<<<< HEAD:src/VipCI.py
        # Print error message
        print("(!) Method get_inputs is useless in VipCI.")
        # Return for method cascading
        return self

    # -----------------------------------------------
=======
        # Update the verbose state and display
        self._verbose = verbose
        self._print("\n=== FINISH ===\n", max_space=2)
        # Raise error message
        raise NotImplementedError(f"Class {self.__name__} cannot delete the distant data.")
    # ------------------------------------------------
>>>>>>> future-branch:VipCI.py

    #################
    ################ Private Methods ################
    #################

    ###################################################################
    # Methods that must be overwritten to adapt VipLauncher methods to
    # new location: "girder"
    ###################################################################

<<<<<<< HEAD:src/VipCI.py
    # Save session properties in a JSON file
    def _save_session(self, verbose=False) -> None:
        """
        Saves useful properties as metadata in session's Girder directory.
        Also displays this path is `verbose` is True.

        The saved properties are :
        - `session_name`: current session name
        - `pipeline_id`: pipeline identifier
        - `input_settings`: input parameters sent to VIP,
        - `workflows`: workflow inventory.
        """
        # Data to save
        vip_data = {
            "session_name": self._session_name,
            "pipeline_id": self._pipeline_id,
            "workflows": self._workflows,
            "input_settings": self._input_settings,
        }
        # Ensure the output directory exists on Girder
        self._make_dir(path=self._vip_output_dir, location="girder")
        # Save metadata in the global output directory
        folderId, _ = self._girder_path_to_id(self._vip_output_dir)
        self._girder_client.addMetadataToFolder(folderId=folderId, metadata=vip_data)
        # Update metadata for each workflow
        for workflow_id in self._workflows:
            metadata = self._meta_workflow(workflow_id=workflow_id)
            folderId, _ = self._girder_path_to_id(
                path=self._workflows[workflow_id]["output_path"]
            )
            self._girder_client.addMetadataToFolder(
                folderId=folderId, metadata=metadata
            )
        # Display
        if verbose:
            print("\nSession properties were saved as metadata under folder:")
            print(f"\t{self._vip_output_dir}")
            print(f"\t(Girder ID: {folderId})\n")

    # ------------------------------------------------

    # Load session properties from Girder metadata
    def _load_session(self, verbose=True) -> bool:
        """
        Loads Session properties from the metadata stored in the Session folder on Girder.
        Returns a success flag. Displays success message unless `verbose` is False.
        If current properties (i.e. `session_name`, etc.) are already set, they will be replaced.
        """
        try:
            # Load the metadata on Girder
            girder_id, _ = self._girder_path_to_id(
                self._local_output_dir, verbose=False
            )
            folder = self._girder_client.getFolder(folderId=girder_id)
        except girder_client.HttpError as e:
            if e.status == 400:  # Folder was not found
                return False
        # Set all instance properties
        self._set(**folder["meta"])
        # Update the output directory
        self._set(vip_output_dir=self._local_output_dir)
        # Display
        if verbose:
            print("An existing session was found.")
            print("Session properties were loaded from:\n\t", self._local_output_dir)
        # Return
        return True

    # ------------------------------------------------

    #################################################
    # Manipulate Resources on Girder
    #################################################

    # Function to get a resource ID
=======
    # Path to delete during session finish
    def _path_to_delete(self) -> dict:
        """Returns the folders to delete during session finish, with appropriate location."""
        return {}
    # ------------------------------------------------

    # Method to check existence of a resource on Girder.
>>>>>>> future-branch:VipCI.py
    @classmethod
    def _exists(cls, path: PurePath, location="girder") -> bool:
        """
<<<<<<< HEAD:src/VipCI.py
        Returns a resource ID from its `path` within a Girder collection.
        Parameter `path` should begin with: "/collection/[collection_name]/...".

        Raises `girder_client.HttpError` if the resource was not found.
        Adds intepretation message unless `verbose` is False.
        """
        try:
            resource = cls._girder_client.resourceLookup(path)
        except girder_client.HttpError as e:
            if verbose and e.status == 400:
                print(
                    "(!) The following path is invalid or refers to a resource that does not exist:"
                )
                print(f"    \t{path}")
                print("    Original error from Girder API:")
            raise e
        # Return the resource ID and type
        try:
            return resource["_id"], resource["_modelType"]
        except KeyError as ke:
            if verbose:
                print("Unhandled type of resource: \n\t{resource}\n")
            raise ke

    # ------------------------------------------------

    # Function to get a resource path
    @classmethod
    def _girder_id_to_path(cls, id: str, type: str, verbose=True) -> str:
        """
        Returns a resource path from its Girder `id`.
        The resource `type` (item, folder, collection) must be provided.

        Raises `girder_client.HttpError` if the resource was not found.
        """
        try:
            return cls._girder_client.get(f"/resource/{id}/path", {"type": type})
        except girder_client.HttpError as e:
            if verbose and e.status == 400:
                print("(!) Invalid Girder ID or resource type.")
                print("    Original error from Girder API:")
            raise e

    # ------------------------------------------------

    # Function to convert a Girder ID to Girder-VIP standard
    @classmethod
    def _vip_girder_id(cls, girder_id) -> str:
        """
        Prefixes a Girder ID with the VIP standard.
        Input `girder_id` should be a string or a list of strings.
        """
        if isinstance(girder_id, str):
            return ":".join([cls._PREFIX_GIRDER_ID, girder_id])
        elif isinstance(girder_id, list):
            return [":".join([cls._PREFIX_GIRDER_ID, id]) for id in girder_id]
        else:
            raise TypeError("Input should be a string or a list of strings")

    # ------------------------------------------------

    # Function
    def _vip_input_settings(self, my_settings: dict = {}) -> dict:
        """
        Fits `my_settings` to the VIP-Girder standard, i.e. converts Girder paths to:
        "[_PREFIX_GIRDER_ID]:[Girder_ID]".
        Returns the modified settings.

        Input `my_settings` (dict) must contain only strings or lists of strings.
        """

        # Function to get the VIP-Girder standard from 1 input path
        def get_files(input_path: str, get_folder=True):
            # Check if the input is a Girder path
            assert input_path.startswith(
                self._PREFIX_GIRDER_PATH
            ), f"The following parameter should contain only Girder paths: {parameter}"
            # Look up for the resource in Girder & get the Girder ID
            girder_id, girder_type = self._girder_path_to_id(input_path)
            #
            if girder_type == "file":
                # Prefix the girder ID
                return self._vip_girder_id(girder_id)
            elif girder_type == "item":
                # Retrieve the files ID
                files = [
                    f["_id"] for f in self._girder_client.listFile(itemId=girder_id)
                ]
                # Check the number of files (1 per item)
                nFiles = len(files)
                if nFiles != 1:
                    msg = f"Item : {self._girder_id_to_path(id=itemId, type='item')}"
                    msg += f"contains {nFiles} files : it cannot be handled in VIP input settings."
                    raise AssertionError(msg)
                # Prefix the girder ID
                return self._vip_girder_id(files[0])
            elif girder_type == "folder":
                if not get_folder:
                    raise ValueError(
                        f"Girder type: '{girder_type}' is not permitted in this context.\n\tBad resource: {input_path}"
                    )
                new_inputs = []
                # Retrieve all items
                items = [
                    it["_id"] for it in self._girder_client.listItem(folderId=girder_id)
                ]
                for itemId in items:
                    # Retrieve the corresponding files
                    files = [
                        f["_id"] for f in self._girder_client.listFile(itemId=itemId)
                    ]
                    # Check the number of files (1 per item)
                    nFiles = len(files)
                    if nFiles != 1:
                        msg = (
                            f"Item : {self._girder_id_to_path(id=itemId, type='item')}"
                        )
                        msg += f"contains {nFiles} files : it cannot be handled in VIP input settings."
                        raise AssertionError(msg)
                    # Update the file list with prefixed Girder ID
                    new_inputs.append(self._vip_girder_id(files[0]))
                # Append the list of files
                return new_inputs
            else:
                # Girder type = collection or other
                raise ValueError(
                    f"Girder type: '{girder_type}' is not permitted in this context.\n\tBad resource: {input_path}"
                )

        # -----------------------------------------------
        # Return if my_settings is empty:
        if not my_settings:
            return {}
        # Check the input type
        assert isinstance(
            my_settings, dict
        ), "Please provide input parameters in dictionnary shape."
        # Convert local paths into VIP-Girder IDs
        vip_settings = {}
        for parameter in my_settings:
            input = my_settings[parameter]
            # Check if this parameter (either string or list) contains a Girder path
            if isinstance(input, str) and input.startswith(self._PREFIX_GIRDER_PATH):
                vip_settings[parameter] = get_files(input)
            elif (
                isinstance(input, list)
                and (len(input) != 0)
                and isinstance(input[0], str)
                and input[0].startswith(self._PREFIX_GIRDER_PATH)
            ):
                vip_settings[parameter] = [get_files(path) for path in input]
            else:
                # No Girder path was found: append the original object
                vip_settings[parameter] = input
        # Return
        return vip_settings

    # ------------------------------------------------

    # Check the input settings based on pipeline descriptor
    def _check_input_settings(self, input_settings: dict = {}) -> bool:
        """
        Checks `input_settings` with respect to pipeline descriptor.
        If `input_settings` is not provided, checks the instance attribute.

        This function uses instance properties like `_pipeline_id` to run assertions.
        Returns True if each assertion could be tested, False otherwise.

        Detailed behaviour:
        - Raises AssertionError if `input_settings` do not match pipeline requirements
        or if any file does not exist.
        - Raises RuntimeError if communication failed with VIP servers.
        """
        # Check arguments & instance properties
        if not input_settings:
            assert self._input_settings, "Please provide input settings."
            input_settings = self._input_settings
        # Check the pipeline identifier
        if not self._pipeline_id:
            warn("Input settings could not be checked without a pipeline identifier.")
            return False
        # Get the true pipeline parameters
        try:
            parameters = vip.pipeline_def(self._pipeline_id)["parameters"]
        except RuntimeError as vip_error:
            super()._handle_vip_error(vip_error)
        # PARAMETER NAMES -----------------------------------------------------------
        # Check every required field is there
        missing_fields = (
            # requested pipeline parameters
            {
                param["name"]
                for param in parameters
                if not param["isOptional"]
                and (param["defaultValue"] == "$input.getDefaultValue()")
            }
            # current parameters in self
            - set(input_settings.keys())
        )
        assert not missing_fields, "Missing input parameters :\n" + ", ".join(
            missing_fields
        )
        # Check every input parameter is a valid field
        unknown_fields = set(input_settings.keys()) - {  # current parameters in self
            param["name"] for param in parameters
        }  # pipeline parameters
        assert not unknown_fields, (
            "The following parameters are not in the pipeline description :\n"
            + ", ".join(unknown_fields)
        )  # "results-directory" should be absent in VipCI
        return True

    # ---------------------------------------------------------

    # Method to check existence of a distant or local resource.
    @classmethod
    def _exists(cls, path, location="girder") -> bool:
        """
        Checks existence
        """
        # Check input type
        if not isinstance(path, str):
            path = str(path)
        # Check path existence existence
        if location == "local":
            return os.path.exists(path)
        elif location == "girder":
            try:
                cls._girder_client.resourceLookup(path=path)
=======
        Checks existence of a resource on Girder.
        """
        # Check path existence in `location`
        if location=="girder":
            try: 
                cls._girder_client.resourceLookup(path=str(path))
>>>>>>> future-branch:VipCI.py
                return True
            except girder_client.HttpError:
                return False
        else:
            raise NotImplementedError(f"Unknown location: {location}")

    # ------------------------------------------------

    # Method to create a distant or local directory
    @classmethod
    def _create_dir(cls, path: PurePath, location="girder", **kwargs) -> str:
        """
        Creates a directory at `path` on Girder if `location` is "girder".

        `path` should be a PathLib object.
        `kwargs` can be passed as keyword arguments to `girder-client.createFolder()`.
        Returns the Girder ID of the newly created folder.
        """
<<<<<<< HEAD:src/VipCI.py
        if location == "local":
            # Check input type
            if isinstance(path, str):
                path = pathlib.PurePath(path)
            # Check the parent is a directory
            assert os.path.isdir(
                path.parent
            ), f"Cannot create subdirectories in '{str(path.parent)}': not a folder"
            # Create the new directory with additional keyword arguments
            return os.mkdir(path=path, **kwargs)
        elif location == "girder":
            # Check input type
            if isinstance(path, str):
                path = pathlib.PurePosixPath(path)
            # Find the parent ID and type
            parentId, parentType = cls._girder_path_to_id(str(path.parent))
            # Check the parent is a directory
            assert (
                parentType == "folder"
            ), f"Cannot create subdirectories in '{str(path.parent)}': not a Girder folder"
            # Create the new directory with additional keyword arguments
            return cls._girder_client.createFolder(
                parentId=parentId, name=str(path.name), reuseExisting=True, **kwargs
            )

    # ------------------------------------------------

    # Method to create a distant or local directory leaf on the top of any path
    @classmethod
    def _make_dir(cls, path, location="girder", **kwargs) -> str:
        """
        Creates each non-existent directory in `path` :
        - locally if `location` is "local";
        - on Girder if `location` is "girder".

        `kwargs` can be passed as additional arguments to the girder-client method `createFolder()`.
        Returns the newly created part of `path` (empty string if `path` already exists).
        """
        # Create a PathLib object depending on the location
        if location == "local":
            path = pathlib.PurePath(path)
        else:
            path = pathlib.PurePosixPath(path)
        # Case : the current path exists
        if cls._exists(path=path, location=location):
            return ""
        # Find the 1rst non-existent node in the arborescence
        first_node = path
        while not cls._exists(first_node.parent, location):
            first_node = first_node.parent
        # Make the path from there
        if location == "local":
            # Create the full arborescence locally
            os.makedirs(path, exist_ok=True)
        else:
            # Create the first node
            cls._create_dir(path=first_node, location=location, **kwargs)
            # Make the other nodes one by one
            dir_to_make = first_node
            while dir_to_make != path:
                # Find the next directory to make
                dir_to_make /= path.relative_to(dir_to_make).parts[0]
                # Make the directory
                cls._create_dir(path=dir_to_make, location=location, **kwargs)
        # Return the created nodes
        return str(path.relative_to(first_node.parent))

=======
        if location == "girder": 
            # Find the parent ID and type
            parentId, parentType = cls._girder_path_to_id(str(path.parent))
            # Check the parent is a directory
            if not (parentType == "folder"):
                raise ValueError(f"Cannot create folder {path} in '{path.parent}': parent is not a Girder folder")
            # Create the new directory with additional keyword arguments
            return cls._girder_client.createFolder(
                parentId=parentId, name=str(path.name), reuseExisting=True, **kwargs
                )["_id"]
        else: 
            raise NotImplementedError(f"Unknown location: {location}")
>>>>>>> future-branch:VipCI.py
    # ------------------------------------------------

    # Function to delete a path
    @classmethod
    def _delete_path(cls, path: PurePath, location="vip") -> None:
        raise NotImplementedError("VipCI cannot delete data.")

    # Function to delete a path on VIP with warning
    @classmethod
    def _delete_and_check(cls, path: PurePath, location="vip", timeout=300) -> bool:
        raise NotImplementedError("VipCI cannot delete data.")
    
    ##################################################
     # (A.3) Launch pipeline executions on VIP servers
    ##################################################

    def _init_exec(self) -> str:
        """
        Initiates one VIP workflow with `pipeline_id`, `session_name`, `input_settings`, `output_dir`.
        Returns the workflow identifier.
        """
        # Get function arguments
        # input_settings = self._vip_input_settings(self._input_settings)
        input_settings = self._get_input_settings(location="vip-girder")
        # Create a workflow-specific result directory
        res_path = self._vip_output_dir / time.strftime('%Y-%m-%d_%H:%M:%S', time.localtime()) 
            # no simple way to rename later with workflow_id
        res_id = self._create_dir(
            path=res_path, location="girder", 
            description=f"VIP outputs from one workflow in Session '{self._session_name}'"
        )
        res_vip = self._vip_girder_id(res_id)
        # Launch execution
        workflow_id = vip.init_exec(
            pipeline = self.pipeline_id, 
            name = self.session_name, 
            inputValues = input_settings,
            resultsLocation = res_vip
        )
        # Record the path to output files (create the workflow entry)
        self._workflows[workflow_id] = {"output_path": str(res_path)}
        return workflow_id
    # ------------------------------------------------
    
    #################################################
    # Workflow Monitoring
    #################################################

    # Function extract metadata from a single workflow
    def _meta_workflow(self, workflow_id: str) -> dict:
        return {
            "session_name": self._session_name,
            "workflow_id": workflow_id,
            "workflow_start": self._workflows[workflow_id]["start"],
            "workflow_status": self._workflows[workflow_id]["status"],
        }

    # Overwrite _get_exec_infos() to bypass call to vip.get_exec_results() (does not work at this time)
    @classmethod
    def _get_exec_infos(cls, workflow_id: str) -> dict:
        """
        Returns succint information on `workflow_id`:
        - Execution status (VIP notations)
        - Starting time (local time, format '%Y/%m/%d %H:%M:%S')
        - List of paths to the output files.
        """
        try:
            # Get execution infos
            infos = vip.execution_info(workflow_id)
            # Secure way to get execution results
            # files = vip.get_exec_results(workflow_id)
        except RuntimeError as vip_error:
            cls._handle_vip_error(vip_error)
        # Return filtered information
        return {
            # Execution status (VIP notations)
            "status": infos["status"],
            # Starting time (human readable)
            "start": time.strftime(
                "%Y/%m/%d %H:%M:%S", time.localtime(infos["startDate"] / 1000)
            ),
            # # Returned files
            # "outputs": infos["returnedFiles"]["output_file"]
        }

    # ------------------------------------------------

<<<<<<< HEAD:src/VipCI.py
=======
    #################################################
    # Save / Load Session as / from Girder metadata
    #################################################

    # Save session properties in a JSON file
    def _save_session(self, session_data: dict, location="girder") -> bool:
        """
        Saves dictionary `session_data` as metadata in the output directory on Girder.
        Returns a success flag.
        Displays success / failure unless `_verbose` is False.
        """
        # Thow error if location is not "girder" because this session does no interact with VIP
        if location != "girder":
            return NotImplementedError(f"Location '{location}' is unknown for {self.__name__}")
        # Ensure the output directory exists on Girder
        is_new = self._mkdirs(path=self._vip_output_dir, location=location)
        # Save metadata in the global output directory
        folderId, _ = self._girder_path_to_id(self._vip_output_dir)
        self._girder_client.addMetadataToFolder(folderId=folderId, metadata=session_data)
        # Update metadata for each workflow
        for workflow_id in self._workflows:
            metadata = self._meta_workflow(workflow_id=workflow_id)
            folderId, _ = self._girder_path_to_id(path=self._workflows[workflow_id]["output_path"])
            self._girder_client.addMetadataToFolder(folderId=folderId, metadata=metadata)
        # Display
        self._print()
        if is_new:
            self._print(">> Session was backed up as Girder metadata in:")
            self._print(f"\t{self._vip_output_dir} (Girder ID: {folderId})\n")
        else:
            self._print(">> Session backed up\n")
        # Return
        return True
    # ------------------------------------------------

    def _load_session(self, location="girder") -> dict:
        """
        Loads backup data from the metadata stored in the output directory on Girder.
        If the metadata could not be found, returns None.
        Otherwise, returns session properties as a dictionary.
        """
        # Thow error if location is not "girder"
        if location != "girder":
            return NotImplementedError(f"Location '{location}' is unknown for {self.__name__}")
        # Check the output directory is defined
        if self.vip_output_dir is None: 
            return None
        # Load the metadata on Girder
        with self._silent_class():
            try:
                girder_id, _ = self._girder_path_to_id(self.vip_output_dir)
                folder = self._girder_client.getFolder(folderId=girder_id)
            except girder_client.HttpError as e:
                if e.status == 400: # Folder was not found
                    return None
        # Display success if the folder was found
        self._print("<< Session restored from its output directory\n")
        # Return session metadata 
        return folder["meta"]
    # ------------------------------------------------
    
    #################################################
    # Manipulate Resources on Girder
    #################################################

    # Function to get a resource ID
    @classmethod
    def _girder_path_to_id(cls, path) -> tuple[str, str]:
        """
        Returns a resource ID from its `path` within a Girder collection.
        `path` should begin with: "/collection/[collection_name]/...".
        `path` can be a string or PathLib object.

        Raises `girder_client.HttpError` if the resource was not found. 
        Adds intepretation message unless `cls._VERBOSE` is False.
        """
        try :
            resource = cls._girder_client.resourceLookup(str(path))
        except girder_client.HttpError as e:
            if e.status == 400:
                cls._printc("(!) The following path is invalid or refers to a resource that does not exist:")
                cls._printc(f"    \t{path}")
                cls._printc("    Original error from Girder API:")
            raise e
        # Return the resource ID and type
        try:
            return resource['_id'], resource['_modelType']
        except KeyError as ke:
            cls._printc(f"Unhandled type of resource: \n\t{resource}\n")
            raise ke
    # ------------------------------------------------
    
    # Function to get a resource path
    @classmethod
    def _girder_id_to_path(cls, id: str, type: str) -> PurePosixPath:
        """
        Returns a resource path from its Girder `id`.
        The resource `type` (item, folder, collection) must be provided.

        Raises `girder_client.HttpError` if the resource was not found.
        """
        try :
            return PurePosixPath(cls._girder_client.get(f"/resource/{id}/path", {"type": type}))
        except girder_client.HttpError as e:
            if e.status == 400:
                cls._printc(f"(!) Invalid Girder ID: {id} with resource type:{type}")
                cls._printc("    Original error from Girder API:")
            raise e
    # ------------------------------------------------
    
    # Function to convert a Girder ID to Girder-VIP standard
    @classmethod
    def _vip_girder_id(cls, resource) -> str:
        """
        Prefixes a Girder ID with the VIP standard. 
        Input `resource` should be a Girder Id (str) or a Girder path (PurePosixPath)
        """
        if isinstance(resource, str):
            # Prefix the ID
            return ":".join([cls._GIRDER_ID_PREFIX, resource])
        elif isinstance(resource, PurePath):
            # Get the Girder ID
            girder_id, _ = cls._girder_path_to_id(resource)
            # Prefix the ID
            return ":".join([cls._GIRDER_ID_PREFIX, girder_id])
    # ------------------------------------------------

    # Store the VIP paths as PathLib objects.
    def _parse_input_settings(self, input_settings) -> dict:
        """
        Parses the input settings, i.e.:
        - Resolves any reference to a Binder collection and turns a folder name 
            into a list of files
        - Converts all Girder paths to PathLib objects 
        - Leaves the other parameters untouched.
        """
        # Function to extract file from Girder item
        def get_file_from_item(itemId: str) -> str:
            """Returns the Girder ID of a single file contained in `itemId`"""
            files = [
                f["_id"] for f in self._girder_client.listFile(itemId=itemId)
            ]
            # Check the number of files (1 per item)
            if len(files) != 1:
                msg = f"Unable to parse the Girder item : {self._girder_id_to_path(id=itemId, type='item')}"
                msg += "Contains more than 1 file."
                raise NotImplementedError(msg)
            return files[0]
        # -- End of get_file_from_item() --
        # Function to extract all files from a Girder resource
        def get_files(input_path: str):
            """
            Returns the path of all files contained in the Girder resource pointed by `input_path`.
            The Girder resource can be a file, an item with 1 file or a folder with multiple items.
            """
            # Look up for the resource in Girder & get the Girder ID
            girder_id, girder_type = self._girder_path_to_id(input_path)
            # Retrieve all files based on the resource type
            if girder_type == "file":
                # Return the Girder path
                return PurePosixPath(input_path)
            elif girder_type == "item":
                # Retrieve the corresponding file
                fileId = get_file_from_item(girder_id)
                # Return the Girder path
                return self._girder_id_to_path(id=fileId, type='file')
            elif girder_type == "folder":
                # Retrieve all items
                items = [ it["_id"] for it in self._girder_client.listItem(folderId=girder_id) ]
                # Browse items
                for itemId in items:
                    new_inputs = []
                    # Retrieve the corresponding file
                    fileId = get_file_from_item(itemId)
                    # Update the file list with new Girder path
                    new_inputs.append(self._girder_id_to_path(id=fileId, type='file'))
                # Return the list of files
                return new_inputs
            else: 
                # Girder type = collection or other
                raise ValueError(f"Bad resource: {input_path}\n\tGirder type '{girder_type}' is not permitted in this context.")
        # -- End of get_files() --
        # Function to parse Girder paths
        def parse_value(input):
            # Case: single input, string or path-like
            if isinstance(input, (str, os.PathLike)):
                # Case: Girder path
                if str(input).startswith(self._SERVER_PATH_PREFIX): 
                    return get_files(input)
                # Case: any other input
                else: return input
            # Case: multiple inputs
            elif isinstance(input, list):
                new_input = []
                # Browse elements
                for element in input:
                    # Parse element
                    parsed = parse_value(element)
                    # Merge the lists if `element` is a folder
                    if isinstance(parsed, list): new_input += parsed
                    # Append if `element` is a file
                    else: new_input.append(parsed)
                # Return the list of files
                return new_input
           # Case not string nor path-like: return as is
            else: return input
        # -- End of parse_value() --
        # Return the parsed value of each parameter
        return {
            key: parse_value(value)
            for key, value in input_settings.items()
        }
    # ------------------------------------------------

    # Get the input settings after files are parsed as PathLib objects
    def _get_input_settings(self, location="girder") -> dict:
        """
        Returns the input settings with filenames adapted to `location`.
        - if `location` = "girder", returns Girder paths string format.
        - if `location` = "vip-girder", returns the prefixed Girder ID for VIP.

        Returns a string version of any other parameter.
        """
        # Function to get the VIP-Girder standard from 1 input path
        def get_input(value, location) -> str:
            """
            If `value` is a path, returns the corresponding string.
            Value can be a single input or a list of inputs.
            """
            # Case: multiple inputs
            if isinstance(value, list):
                return [ get_input(element, location) for element in value ]
            # Case : path to Girder resource
            elif isinstance(value, PurePath): 
                if location == "girder":
                    return str(value)
                elif location == "vip-girder":
                    return self._vip_girder_id(value)
            # Case: other parameter
            else: return str(value)
        # --------------------
        # Raise an error if `location` cannot be parsed
        if location not in ("girder", "vip-girder"):
            raise NotImplementedError(f"Unknown location: {location}")
        # Browse input settings
        return {
            key: get_input(value, location)
            for key, value in self._input_settings.items()
        }
    # ------------------------------------------------
>>>>>>> future-branch:VipCI.py

######################################################

if __name__ == "__main__":
    pass
