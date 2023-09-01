from __future__ import annotations
import os
import time
from pathlib import *

import girder_client
from vip_client.utils import vip
from vip_client.classes.VipLauncher import VipLauncher

class VipCI(VipLauncher):
    """
    Python class to run VIP pipelines on datasets located on Girder.

    A single instance allows to run 1 pipeline with 1 parameter set (any number of runs).
    Pipeline runs need at least three inputs:
    - `pipeline_id` (str) Name of the pipeline. 
    - `input_settings` (dict) All parameters needed to run the pipeline.
    - `output_dir` (str) Path to a Girder folder where execution results will be stored.

    N.B.: all instance methods require that `VipCI.init()` has been called with:
    - a valid VIP API key;
    - a valid Girder API key.
    """

                    ##################
    ################ Class Attributes ##################
                    ##################

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

                    #############
    ################ Constructor ##################
                    #############
    def __init__(
        self, output_dir=None, pipeline_id: str=None, input_settings: dict=None, 
        session_name: str=None, verbose: bool=None
    ) -> None:
        """
        Creates a VipCI instance and sets its properties from keyword arguments.

        ## Parameters
        - `output_dir` (str | os.PathLike) Path to a Girder folder where execution results will be stored.
            - Does not need to exist
            - Usually in format : "/collection/[collection_name]/[path_to_folder]"
            - User must have read/write permissions on the Girder collection/folder.

        - `pipeline_id` (str) Name of your pipeline in VIP. 
            - Usually in format : *application_name*/*version*.
            - Run VipLauncher.show_pipeline() to display available pipelines.

        - `input_settings` (dict) All parameters needed to run the pipeline.
            - Run VipSession.show_pipeline(`pipeline_id`) to display these parameters.
            - The dictionary can contain any object that can be converted to strings, or lists of such objects.
            - Lists of parameters launch parallel workflows on VIP.

        - `session_name` [Optional/Recommended] (str) A name to identify this session.
            - Default value: 'VipCI-[date]-[time]-[id]'
        
        - `verbose` [Optional] (bool) Verbose mode for this instance.
            - If True, instance methods will display logs;
            - If False, instance methods will run silently.

        `session_name` is only set at instantiation; other properties can be set later in function calls.
        If `output_dir` leads to data from a previous session, properties will be loaded from the metadata on Girder.
        """
        # Initialize with the name, pipeline and input settings
        super().__init__(
            output_dir = output_dir,
            session_name = session_name, 
            pipeline_id = pipeline_id, 
            input_settings = input_settings,
            verbose = verbose
        )
        # End display
        if any([session_name, output_dir]) and (self.__name__ == "VipCI"): 
            self._print()
    # ------------------------------------------------

                    ################
    ################ Public Methods ##################
                    ################

    #################################################
    # Manage a session from start to finish
    #################################################

    # Login to VIP and Girder
    @classmethod
    def init(cls, vip_key="VIP_API_KEY", girder_key="GIRDER_API_KEY", verbose=True, **kwargs) -> VipCI:
        """
        Handshakes with VIP using your own API key. 
        Returns a class instance which properties can be provided as keyword arguments.
        
        ## Parameters
        - `vip_key` (str): VIP API key. This can be either:
            A. [unsafe] A **string litteral** containing your API key,
            B. [safer] A **path to some local file** containing your API key,
            C. [safer] The **name of some environment variable** containing your API key (default: "VIP_API_KEY").
        In cases B or C, the API key will be loaded from the local file or the environment variable. 

        - `girder_key` (str): Girder API key. Can take the same values as `vip_key`.
        
        - `verbose` (bool): default verbose mode for all instances.
            - If True, all instances will display logs by default;
            - If False, all instance methods will run silently by default.

        - `kwargs` [Optional] (dict): keyword arguments or dictionnary setting properties of the returned instance.     
        """
        # Initiate a Vip Session silently
        super().init(api_key=vip_key, verbose=False)
        # Restore the verbose state
        cls._VERBOSE = verbose
        # Instantiate a Girder client
        cls._girder_client = girder_client.GirderClient(apiUrl=cls._GIRDER_PORTAL)
        # Check if `girder_key` is in a local file or environment variable
        true_key = cls._get_api_key(girder_key)
        # Authenticate with Girder API key
        cls._girder_client.authenticate(apiKey=true_key)
        # Diplay success
        cls._printc()
        cls._printc("---------------------------------------------")
        cls._printc("| You are communicating with VIP and Girder |")
        cls._printc("---------------------------------------------")
        cls._printc()
        # Return a VipCI instance for method cascading
        return cls(verbose=(verbose and kwargs), **kwargs)
    # ------------------------------------------------

    # Launch the pipeline on VIP
    def launch_pipeline(
            self, pipeline_id: str=None, input_settings: dict=None, output_dir=None, nb_runs=1, 
            verbose: bool=None
        ) -> VipCI:
        """
        Launches pipeline executions on VIP.

        Input parameters :
        - `pipeline_id` (str) The name of your pipeline in VIP, 
            usually in format : *application_name*/*version*.
        - `input_settings` (dict) All parameters needed to run the pipeline.
            - Run VipSession.show_pipeline(`pipeline_id`) to display these parameters.
            - The dictionary can contain any object that can be converted to strings, or lists of such objects.
            - Lists of parameters launch parallel workflows on VIP.
        - `output_dir` (str) Path to the VIP folder where execution results will be stored.
        - `nb_runs` (int) Number of parallel workflows to launch with the same settings.
        
        Default behaviour:
        - Raises AssertionError in case of wrong inputs 
        - Raises RuntimeError in case of failure on VIP servers.
        - In any case, session is backed up after pipeline launch
        """
        return super().launch_pipeline(
            pipeline_id = pipeline_id, # default
            input_settings = input_settings, # default
            output_dir = output_dir, # default
            nb_runs = nb_runs, # default
        )
    # ------------------------------------------------

    # Monitor worflow executions on VIP 
    def monitor_workflows(self, refresh_time=30) -> VipCI:
        """
        Updates and displays the status of each execution launched in the current session.
        - If an execution is still runnig, updates status every `refresh_time` (seconds) until all runs are done.
        - Displays a full report when all executions are done.
        """
        return super().monitor_workflows(refresh_time=refresh_time)
    # ------------------------------------------------

    # Run a full VipCI session 
    def run_session(self, nb_runs=1, refresh_time=30) -> VipCI:
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
        return super().run_session(nb_runs=nb_runs, refresh_time=refresh_time)
    # ------------------------------------------------

    # Display session properties in their current state
    def display(self) -> VipCI:
        """
        Displays useful properties in JSON format.
        - `session_name` : current session name
        - `pipeline_id`: pipeline identifier
        - `output_dir` : path to the pipeline outputs
        - `input_settings` : input parameters sent to VIP
        - `workflows`: workflow inventory, identifying all pipeline runs in this session.
        """
        # Return for method cascading
        return super().display()
    # ------------------------------------------------

    # Return error in case of call to finish()
    def finish(self, verbose: bool=None) -> None:
        """
        This function does not work in VipCI.
        """
        # Update the verbose state and display
        self._verbose = verbose
        self._print("\n=== FINISH ===\n", max_space=2)
        # Raise error message
        raise NotImplementedError(f"Class {self.__name__} cannot delete the distant data.")
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
    
    ####################################################
    # Launch & Monitor pipeline executions from Girder #
    ####################################################

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

    ###################################################
    # Save (/load) Session to (/from) Girder metadata #
    ###################################################

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
    
    ##################################
    # Manipulate Resources on Girder #
    ##################################

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
                cls._printc("    %s" % path)
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

    ###################################################################
    # Adapt `input_settings` to the Vip-Girder communication protocol #
    ###################################################################

    # Store the VIP paths as PathLib objects.
    def _parse_input_settings(self, input_settings) -> dict:
        """
        Parses the input settings, i.e.:
        - Resolves any reference to a Girder collection and turns a folder name 
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

######################################################
        
if __name__=="__main__":
    pass
