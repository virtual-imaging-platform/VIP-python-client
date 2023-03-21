from __future__ import annotations
import os
import json
import time
import pathlib
from warnings import warn

import girder_client
import vip
from VipSession import VipSession

class VipCI(VipSession):
    """
    Python class to run VIP pipelines on datasets stored a Girder repository.

    1 "session" allows to run 1 pipeline with 1 parameter set (any number of pipeline runs).
    Minimal inputs:
    - `pipeline_id` (str) Name of the pipeline in VIP nomenclature. 
        Usually in format : "[application_name]/[version]".
    - `input_settings` (dict) All parameters needed to run the pipeline.
        See pipeline description.
    - `output_dir` (str) Path to a Girder folder where execution results will be stored.
        Usually in format : "/collection/[collection_name]/[path_to_folder]".

    N.B.: all instance methods require that `VipSession.init()` has been called with:
    - a valid VIP API key. 
    - a valid Girder API key.
    See GitHub documentation to get your VIP API key.
    """

                    ##################
    ################ Class Attributes ##################
                    ##################

    _GIRDER_URL = 'https://pilot-warehouse.creatis.insa-lyon.fr/api/v1'
    _PREFIX_GIRDER_ID = "pilotGirder"
    _PREFIX_GIRDER_PATH = "/collection"

                    #############
    ################ Constructor ##################
                    #############
    def __init__(
        self, output_dir="", pipeline_id="", 
        input_settings:dict={}, session_name="",
        verbose=True
    ) -> None:
        """
        Create a VipCI instance from keyword arguments. 
        Displays informations if `verbose` is True.

        Available keywords:
        - `output_dir` (str) Path to a Girder folder where execution results will be stored.
            Usually in format : "/collection/[collection_name]/[path_to_folder]"

        - `session_name` (str) A name to identify this session.
            Default value: 'session_[date]_[time]'

        - `pipeline_id` (str) Name of your pipeline in VIP. 
            Usually in format : "[application_name]/[version]".

        - `input_settings` (dict) All parameters needed to run the pipeline.
            See pipeline description for more information.

        If `output_dir` leads to data from a previous session, 
        all properties will be loaded from the folder metadata on Girder.
        """
        # Initialize the name, pipeline and input settings
        super().__init__(
            session_name=session_name, 
            output_dir=output_dir,
            pipeline_id=pipeline_id, 
            input_settings=input_settings,
            verbose=verbose
        )
        # Update the output directory
        self._vip_output_dir = output_dir
    # ------------------------------------------------

                    ################
    ################ Public Methods ##################
                    ################

    #################################################
    # ($A) Manage a session from start to finish
    #################################################

    # Login to VIP and Girder
    @classmethod
    def init(cls, vip_key: str, girder_key: str, **kwargs) -> VipCI:
        """
        Handshakes with VIP and Girder using your own API keys. 
        Prints a list of pipelines available with the API key, unless `verbose` is False.
        Returns a VipSession instance which properties can be provided as keyword arguments (`kwargs`).

        Inputs `vip_key` and `girder_key` can be either:
        A. (unsafe) a string litteral containing your API key, or
        B. (safer) a path to some local file containing your API key, or
        C. (safer) the name of some environment variable containing your API key.

        In cases B or C, the API key will be loaded from the local file or the environment variable.        
        """
        # Initiate a Vip Session
        super().init(api_key=vip_key)
        # Instantiate a Girder client
        cls._girder_client = girder_client.GirderClient(apiUrl=cls._GIRDER_URL)
        # Check if `girder_key` is in a local file or environment variable
        if os.path.exists(girder_key): # local file
            with open(girder_key, "r") as kfile:
                true_key = kfile.read().strip()
        elif girder_key in os.environ: # environment variable
            true_key = os.environ[girder_key]
        else: # string litteral
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

    def launch_pipeline(self, pipeline_id="", input_settings: dict = {}, output_dir="", nb_runs=1, verbose=True) -> VipSession:
        """
        Launches pipeline executions on VIP.

        Input parameters :
        - `pipeline_id` (str) The name of your pipeline in VIP.
        - `input_settings` (dict) All parameters needed to run the pipeline.
        - `output_dir` (str) Path to the Girder folder where execution results will be stored.
        - `nb_runs` (int) Number of parallel runs of the same pipeline with the same settings.
        - Set `verbose` to False to run silently.
        
        Default behaviour:
        - Raises TypeError if inputs are missing
        - Raises ValueError in case of conflict with previous inputs
        - Raises RuntimeError in case of failure on VIP servers.
        - After pipeline launch, the Session is saved in `output_dir`'s metadata on Girder.
        """
        if verbose:
            print("\n<<< LAUNCH PIPELINE >>>\n")
            print("Checking parameters and data ... ", end="")
        # Update the pipeline identifier
        if pipeline_id:
            # check conflicts with instance value
            if self._pipeline_id and (pipeline_id != self._pipeline_id):
                raise ValueError(f"Pipeline identifier is already set for this session ('{self._pipeline_id}').")
            # update instance property
            self._set(pipeline_id=pipeline_id)
        # Check pipeline existence
        if not self._pipeline_id:
            raise TypeError("Please provide a pipeline identifier for Session: %s" %self._session_name)
        # Check the pipeline identifier
        self._check_pipeline_id()
        # Update the output directory
        if output_dir: 
            self._vip_output_dir = output_dir
        # Check existence
        if not self._vip_output_dir:
            raise TypeError("Please provide an output directory for Session: %s" %self._session_name)
        # Ensure the directory exists
        self._make_dir(path=self._vip_output_dir, location="girder",
                        description=f"VIP executions from the VipCI client under Session name: '{self._session_name}'")
        # Update the input parameters
        if input_settings:
            # check conflicts with instance value
            if self._input_settings and (self._vip_input_settings(input_settings) != self._input_settings):
                raise ValueError(f"Input settings are already set for Session: %s" %self._session_name)
            self._set(input_settings=input_settings)
        # Check existence
        if not self._input_settings:
            raise TypeError(f"Please provide input parameters for Session: %s" %self._session_name)  
        # Check content
        try:
            assert self._check_input_settings(), "Input parameters could not be checked."
        except RuntimeError as handled_error:
            # this may throw a RuntimeError (handled upstream)
            # if pipeline definition could not be loaded from VIP 
            if verbose: print("\n(!) Input settings could not be checked.")
            raise handled_error
        if verbose: print("Done.\n")
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
                res_path = pathlib.PurePosixPath(self._vip_output_dir) \
                    /  time.strftime('%Y-%m-%d_%H:%M:%S', time.localtime()) # no way to rename later with workflow_id
                res_id = self._create_dir(
                    path=res_path, location="girder", 
                    description="VIP outputs from a single workflow"
                )["_id"]
                # Update the input_settings with new results directory
                self._input_settings["results-directory"] = self._vip_girder_id(res_id)
                # Initiate Execution
                workflow_id = vip.init_exec(self._pipeline_id, self._session_name, self._input_settings)
                # Display the workflow name
                if verbose: print(workflow_id, end=", ")
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
        """
        Updates and displays the status of each execution launched in the current session.
        - If an execution is still runnig, updates status every `waiting_time` (seconds) until all runs are done.
        - If `verbose`is True, displays a full report when all executions are done.
        """
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
    def run_session(
            self, nb_runs=1, waiting_time=30, verbose=True
        ) -> VipSession:
        """
        Runs a full session from Girder data:
        1. Launches pipeline executions on VIP;
        2. Monitors pipeline executions until they are all over;
            and Adds metadata on Girder output folder.

        /!\ This function assumes that all session properties are already set.
        Optional arguments can be provided:
        - Increase `nb_runs` to run more than 1 execution at once;
        - Set `waiting_time` to modify the default monitoring time;
        - Set `verbose` to False to run silently.
        """
        return (
            # 1. Launch `nb_runs` pipeline executions on VIP
            self.launch_pipeline(nb_runs=nb_runs, verbose=verbose)
            # 2. Monitor pipeline executions until they are over
            .monitor_workflows(waiting_time=waiting_time, verbose=verbose)
        )
    # ------------------------------------------------

    ###########################################
    # ($B) Additional Features for Advanced Use
    ###########################################

    # ($B.1) Display session properties in their current state
    def display_properties(self) -> VipSession:
        """
        Displays useful instance properties in JSON format.
        - `session_name` : current session name
        - `pipeline_id`: pipeline identifier
        - `local_output_dir` : path to the pipeline outputs *on your machine*
        - `vip_ouput_dir` : path to the pipeline outputs *in your VIP Home directory*
        - `input_settings` : input parameters sent to VIP 
        (note that file locations are bound to `vip_input_dir`).
        - `workflows`: workflow inventory, identifying all pipeline runs in this session.
        """
        # Data to display 
        vip_data={
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
    # ------------------------------------------------

    # Temporary mock function for get_inputs()
    def get_inputs(self) -> VipSession:
        """
        This function does not work in VipCI.
        """
        # Print error message
        print("(!) Method get_inputs is useless in VipCI.")
        # Return for method cascading
        return self
    # -----------------------------------------------

                    #################
    ################ Private Methods ################
                    #################

    #################################################
    # Save / Load Session as / from Girder metadata
    #################################################

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
        vip_data={
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
            folderId, _ = self._girder_path_to_id(path=self._workflows[workflow_id]["output_path"])
            self._girder_client.addMetadataToFolder(folderId=folderId, metadata=metadata)
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
            girder_id, _ = self._girder_path_to_id(self._local_output_dir, verbose=False)
            folder = self._girder_client.getFolder(folderId=girder_id)
        except girder_client.HttpError as e:
            if e.status == 400: # Folder was not found
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
    @classmethod
    def _girder_path_to_id(cls, path: str, verbose=True) -> tuple[str, str]:
        """
        Returns a resource ID from its `path` within a Girder collection.
        Parameter `path` should begin with: "/collection/[collection_name]/...".

        Raises `girder_client.HttpError` if the resource was not found. 
        Adds intepretation message unless `verbose` is False.
        """
        try :
            resource = cls._girder_client.resourceLookup(path)
        except girder_client.HttpError as e:
            if verbose and e.status == 400:
                print("(!) The following path is invalid or refers to a resource that does not exist:")
                print(f"    \t{path}")
                print("    Original error from Girder API:")
            raise e
        # Return the resource ID and type
        try:
            return resource['_id'], resource['_modelType']
        except KeyError as ke:
            if verbose: print("Unhandled type of resource: \n\t{resource}\n")
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
        try :
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
            return [ ":".join([cls._PREFIX_GIRDER_ID, id]) for id in girder_id ]
        else:
            raise TypeError("Input should be a string or a list of strings")
    # ------------------------------------------------

    # Function 
    def _vip_input_settings(self, my_settings:dict={}) -> dict:
        """
        Fits `my_settings` to the VIP-Girder standard, i.e. converts Girder paths to: 
        "[_PREFIX_GIRDER_ID]:[Girder_ID]".
        Returns the modified settings.

        Input `my_settings` (dict) must contain only strings or lists of strings.
        """
        # Function to get the VIP-Girder standard from 1 input path
        def get_files(input_path: str, get_folder=True):
            # Check if the input is a Girder path
            assert input_path.startswith(self._PREFIX_GIRDER_PATH), \
                f"The following parameter should contain only Girder paths: {parameter}"
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
                    raise ValueError(f"Girder type: '{girder_type}' is not permitted in this context.\n\tBad resource: {input_path}")
                new_inputs = []
                # Retrieve all items
                items = [it["_id"] for it in self._girder_client.listItem(folderId=girder_id)]
                for itemId in items:
                    # Retrieve the corresponding files
                    files = [
                        f["_id"] for f in self._girder_client.listFile(itemId=itemId)
                    ]
                    # Check the number of files (1 per item)
                    nFiles = len(files)
                    if nFiles != 1:
                        msg = f"Item : {self._girder_id_to_path(id=itemId, type='item')}"
                        msg += f"contains {nFiles} files : it cannot be handled in VIP input settings."
                        raise AssertionError(msg)
                    # Update the file list with prefixed Girder ID
                    new_inputs.append(self._vip_girder_id(files[0]))
                # Append the list of files
                return new_inputs
            else: 
                # Girder type = collection or other
                raise ValueError(f"Girder type: '{girder_type}' is not permitted in this context.\n\tBad resource: {input_path}")
        # -----------------------------------------------
        # Return if my_settings is empty:
        if not my_settings :
            return {}
        # Check the input type
        assert isinstance(my_settings, dict), \
            "Please provide input parameters in dictionnary shape."
        # Convert local paths into VIP-Girder IDs
        vip_settings = {}
        for parameter in my_settings: 
            input = my_settings[parameter]
            # Check if this parameter (either string or list) contains a Girder path
            if isinstance(input, str) and input.startswith(self._PREFIX_GIRDER_PATH):
                vip_settings[parameter] = get_files(input)
            elif isinstance(input, list) and (len(input) != 0) \
                and isinstance(input[0], str) and input[0].startswith(self._PREFIX_GIRDER_PATH):
                vip_settings[parameter] = [
                    get_files(path) for path in input
                ]                      
            else:
                # No Girder path was found: append the original object
                vip_settings[parameter] = input
        # Return
        return vip_settings
    # ------------------------------------------------
    
    # Check the input settings based on pipeline descriptor
    def _check_input_settings(self, input_settings: dict={}) -> bool:
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
        try :            
            parameters = vip.pipeline_def(self._pipeline_id)["parameters"]
        except RuntimeError as vip_error:
            super()._handle_vip_error(vip_error)
        # PARAMETER NAMES -----------------------------------------------------------
        # Check every required field is there 
        missing_fields = (
            # requested pipeline parameters
            {param["name"] for param in parameters 
                if not param["isOptional"] and (param["defaultValue"] == "$input.getDefaultValue()")} 
            # current parameters in self 
            - set(input_settings.keys()) 
        )
        assert not missing_fields, "Missing input parameters :\n" + ", ".join(missing_fields) 
        # Check every input parameter is a valid field
        unknown_fields = (
            set(input_settings.keys()) # current parameters in self 
            - {param["name"] for param in parameters} # pipeline parameters
        )
        assert not unknown_fields, \
            "The following parameters are not in the pipeline description :\n" \
                + ", ".join(unknown_fields) # "results-directory" should be absent in VipCI
        return True
    # ---------------------------------------------------------
    
    # Method to check existence of a distant or local resource.
    @classmethod
    def _exists(cls, path, location="girder") -> bool:
        """
        Checks existence 
        """
        # Check input type
        if not isinstance(path, str): path = str(path)
        # Check path existence existence
        if location=="local":
            return os.path.exists(path)
        elif location=="girder":
            try: 
                cls._girder_client.resourceLookup(path=path)
                return True
            except girder_client.HttpError: 
                return False
        else: 
            raise NotImplementedError(f"Unknown location: {location}")
    # ------------------------------------------------
    
    # Method to create a distant or local directory
    @classmethod
    def _create_dir(cls, path, location="girder", **kwargs) -> str:
        """
        Creates a directory at `path` :
        - locally if `location` is "local";
        - on Girder if `location` is "girder".

        `kwargs` can be passed as additional arguments to the girder-client method `createFolder()`.
        Returns the Girder ID or local path of the newly created folder.
        """
        if location == "local": 
            # Check input type
            if isinstance(path, str): path=pathlib.PurePath(path)
            # Check the parent is a directory
            assert os.path.isdir(path.parent),\
                f"Cannot create subdirectories in '{str(path.parent)}': not a folder"
            # Create the new directory with additional keyword arguments
            return os.mkdir(path=path, **kwargs)
        elif location == "girder": 
            # Check input type
            if isinstance(path, str): path=pathlib.PurePosixPath(path)
            # Find the parent ID and type
            parentId, parentType = cls._girder_path_to_id(str(path.parent))
            # Check the parent is a directory
            assert (parentType == "folder"),\
                f"Cannot create subdirectories in '{str(path.parent)}': not a Girder folder"
            # Create the new directory with additional keyword arguments
            return cls._girder_client.createFolder(parentId=parentId, name=str(path.name), reuseExisting=True, **kwargs)
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
        if cls._exists(path=path, location=location) :
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
            "workflow_status": self._workflows[workflow_id]["status"]
        }

    # Method to get useful information about a given workflow
    @classmethod
    def _get_exec_infos(cls, workflow_id: str) -> dict:
        """
        Returns succint information on `workflow_id`:
        - Execution status (VIP notations)
        - Starting time (local time, format '%Y/%m/%d %H:%M:%S')
        - List of paths to the output files.
        """
        try :
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
                '%Y/%m/%d %H:%M:%S', time.localtime(infos["startDate"]/1000)
                ),
            # # Returned files
            # "outputs": infos["returnedFiles"]["output_file"]
        }
    # ------------------------------------------------

######################################################
        
if __name__=="__main__":
    pass
