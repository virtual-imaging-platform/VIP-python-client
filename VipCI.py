from __future__ import annotations
import os
import json
import time
from pathlib import *
from warnings import warn

import girder_client
import vip
from VipLauncher import VipLauncher

class VipCI(VipLauncher):
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

    N.B.: all instance methods require that `VipCI.init()` has been called with:
    - a valid VIP API key. 
    - a valid Girder API key.
    See GitHub documentation to get your VIP API key.
    """

                    ##################
    ################ Class Attributes ##################
                    ##################

    # Girder data
    _GIRDER_URL = 'https://pilot-warehouse.creatis.insa-lyon.fr/api/v1'
    _PREFIX_GIRDER_ID = "pilotGirder"
    _PREFIX_GIRDER_PATH = "/collection"
    # Properties to save for this class
    _PROPERTIES = [
        "session_name", 
        "pipeline_id",
        "vip_output_dir", 
        "input_settings", 
        "workflows"
    ]

                    #################
    ################ Main Properties ##################
                    ################# 
    # See VipLauncher for inherited properties

    # Overwrite `input_settings` (setter function) to write Girder IDs instead of the collection paths
    @property
    def input_settings(self) -> dict:
        """All parameters needed to run the pipeline 
        Run show_pipeline() for more information"""
        return self._input_settings
    
    @input_settings.setter
    def input_settings(self, input_settings: dict):
        new_settings = self._vip_input_settings(input_settings)
        # Check conflicts with instance attribute
        if self._is_defined("_input_settings") and (new_settings != self._input_settings):
            raise ValueError(f"Input settings are already set for session: {self.session_name}.")
        # Update
        self._input_settings = new_settings

    @input_settings.deleter
    def input_settings(self) -> None:
        del self._input_settings
    # ------------------------------------------------

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
        Returns a VipCI instance which properties can be provided as keyword arguments (`kwargs`).

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

    def launch_pipeline(
            self, pipeline_id="", input_settings:dict={}, output_dir="", nb_runs=1, verbose=True
        ) -> VipCI:
        """
        Launches pipeline executions on VIP.

        Input parameters :
        - `pipeline_id` (str) The name of your pipeline in VIP, 
        usually in format : *application_name*/*version*.
        - `input_settings` (dict) All parameters needed to run the pipeline.
        - `output_dir` (str) Path to the VIP folder where execution results will be stored.
        - `nb_runs` (int) Number of parallel workflows to launch with the same settings.
        - Set `verbose` to False to launch silently.
        
        Default behaviour:
        - Raises AssertionError in case of wrong inputs 
        - Raises RuntimeError in case of failure on VIP servers.
        - In any case, session is backed up after pipeline launch
        """

        try :
            super().launch_pipeline(
                pipeline_id = pipeline_id, # default
                input_settings = input_settings, # default
                output_dir = output_dir, # default
                nb_runs = nb_runs, # default
                verbose = verbose # default
            )
        except Exception as e:
            raise e
        finally:
            # In any case, save session properties
            self._save_session(verbose=True)
        # Return for method cascading
        return self
    # ------------------------------------------------

    # (A.3) Launch pipeline executions on VIP servers
    ##################################################
    def _init_exec(
            self, pipeline_id="", session_name="", input_settings="",
            output_dir="") -> str:
        """
        Initiates one VIP workflow with `pipeline_id`, `session_name`, `input_settings`, `output_dir`.
        Returns the workflow identifier.
        """
        # Parse arguments
        if not pipeline_id:
            pipeline_id = self._pipeline_id
        if not session_name:
            session_name = self._session_name
        if not input_settings:
            input_settings = self._input_settings
        if not output_dir:
            output_dir = str(self._vip_output_dir)
        # Girder-specific instructions : create a workflow-specific result directory
        res_path = self._vip_output_dir / time.strftime('%Y-%m-%d_%H:%M:%S', time.localtime()) # no way to rename later with workflow_id
        res_id = self._mkdirs(
            path=res_path, location="girder", 
            description=f"VIP outputs from one workflow in Session '{self._session_name}'"
        )
        # Launch execution
        workflow_id = vip.init_exec(
            pipeline = pipeline_id, 
            name = session_name, 
            inputValues = input_settings,
            resultsLocation = self._vip_girder_id(res_id)
        )
        # Girder-specific instructions : Record the path to output files (create the workflow entry)
        self._workflows[workflow_id] = {"output_path": str(res_path)}
        return workflow_id
    # ------------------------------------------------

    # ($A.4) Monitor worflow executions on VIP 
    def monitor_workflows(self, waiting_time=30, verbose=True) -> VipCI:
        """
        Updates and displays the status of each execution launched in the current session.
        - If an execution is still runnig, updates status every `waiting_time` (seconds) until all runs are done.
        - If `verbose`is True, displays a full report when all executions are done.
        """
        return super().monitor_workflows(waiting_time=waiting_time, verbose=verbose)
    # ------------------------------------------------

    # Mock function for finish()
    def finish(self) -> VipCI:
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
        ) -> VipCI:
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

    # ($B.1) Display session properties in their current state
    def show_properties(self) -> VipCI:
        """
        Displays useful properties in JSON format.
        - `session_name` : current session name
        - `pipeline_id`: pipeline identifier
        - `output_dir` : path to the pipeline outputs
        - `input_settings` : input parameters sent to VIP
        - `workflows`: workflow inventory, identifying all pipeline runs in this session.
        """
        # Return for method cascading
        return super().show_properties()
    # ------------------------------------------------

                    #################
    ################ Private Methods ################
                    #################

    ###################################################################
    # Methods that must be overwritten to adapt VipLauncher methods to
    # new location: "girder"
    ###################################################################

    # Path to delete during session finish
    def _path_to_delete(self) -> dict:
        """Returns the folders to delete during session finish, with appropriate location."""
        return {}
    # ------------------------------------------------

    # Method to check existence of a resource on Girder.
    @classmethod
    def _exists(cls, path: PurePath, location="girder") -> bool:
        """
        Checks existence of a resource on Girder.
        """
        # Check path existence in `location`
        if location=="girder":
            try: 
                cls._girder_client.resourceLookup(path=str(path))
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
    # ------------------------------------------------

    # Function to delete a path
    @classmethod
    def _delete_path(cls, path: PurePath, location="vip") -> None:
        raise NotImplementedError("VipCI cannot delete data.")

    # Function to delete a path on VIP with warning
    @classmethod
    def _delete_and_check(cls, path: PurePath, location="vip", timeout=300) -> bool:
        raise NotImplementedError("VipCI cannot delete data.")

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
        self._mkdirs(path=self._vip_output_dir, location="girder")
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
            girder_id, _ = self._girder_path_to_id(self.vip_output_dir, verbose=False)
            folder = self._girder_client.getFolder(folderId=girder_id)
        except girder_client.HttpError as e:
            if e.status == 400: # Folder was not found
                return False
        # Set all instance properties
        self._set(**folder["meta"])
        # Update the output directory
        self._set(vip_output_dir=self.vip_output_dir)
        # Display
        if verbose:
            print("An existing session was found.")
            print("Session properties were loaded from:\n\t", self.vip_output_dir)
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
        # Convert collection paths into VIP-Girder IDs
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

    # Overwrite _get_exec_infos() to bypass call to vip.get_exec_results() (does not work at this time)
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
