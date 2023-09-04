from __future__ import annotations
import json
import os
import re
import textwrap
import time
from contextlib import contextmanager, nullcontext
from pathlib import *

from vip_client.utils import vip

class VipLauncher():
    """
    Python class to run VIP pipelines on datasets located on VIP servers.

    A single instance allows to run 1 pipeline with 1 parameter set (any number of runs).
    Pipeline runs need at least three inputs:
    - `pipeline_id` (str) Name of the pipeline. 
    - `input_settings` (dict) All parameters needed to run the pipeline.
    - `output_dir` (str | os.PathLike) Path to the VIP directory where pipeline outputs will be stored.

    N.B.: all instance methods require that `VipLauncher.init()` has been called with a valid API key. 
    See GitHub documentation to get your own VIP API key.
    """

                    ##################
    ################ Class Attributes ##################
                    ##################
    
    # Class name
    __name__ = "VipLauncher"
    # Properties to save / display for this class
    _PROPERTIES = [
        "session_name", 
        "pipeline_id", 
        "vip_output_dir", 
        "input_settings", 
        "workflows"
    ]
    # Default verbose state
    _VERBOSE = True
    # Default backup location 
    # (set to None to avoid saving and loading backup files)
    _BACKUP_LOCATION = None
    # Default location for VIP inputs/outputs (can be different for subclasses)
    _SERVER_NAME = "vip"
    # Prefix that defines a path from VIP
    _SERVER_PATH_PREFIX = "/vip"
    # Default file name to save session properties 
    _SAVE_FILE = "session_data.json"
    # Vip portal
    _VIP_PORTAL = "https://vip.creatis.insa-lyon.fr/"
    # Mail address for support
    _VIP_SUPPORT = "vip-support@creatis.insa-lyon.fr"
    # Regular expression for invalid characters (i.e. all except valid characters)
    _INVALID_CHARS_FOR_VIP = re.compile(r"[^0-9\.,A-Za-z\-+@/_(): \[\]?&=]")
    # List of pipelines available to the user (will evolve after init())
    _AVAILABLE_PIPELINES = []

                    #####################
    ################ Instance Properties ##################
                    ##################### 

    # Session Name
    @property
    def session_name(self) -> str:
        """A name to identify the current Session"""
        # Return None if the private attribute is unset
        return self._session_name if self._is_defined("_session_name") else None
    
    @session_name.setter
    def session_name(self, name: str) -> None:
        # Call deleter if agument is None
        if name is None: 
            del self.session_name
            return
        # Check type
        if not isinstance(name, str):
            raise TypeError("`session_name` should be a string")
        # Check the name for invalid characters
        if re.search(r"[^0-9A-Za-z\-_]+", name):
            raise ValueError("Session name must contain only alphanumeric characters and hyphens '-', '_'")
        # Check conflict with private attribute
        if self._is_defined("_session_name"):
            self._check_value("_session_name", name)
        # Assign
        self._session_name = name

    @session_name.deleter
    def session_name(self) -> None:
        # Delete only if the private attribute is defined
        if self._is_defined("_session_name"): 
            del self._session_name
    # ------------------------------------------------

    # Pipeline identifier
    @property
    def pipeline_id(self) -> str:
        """Pipeline identifier for VIP"""
        # Return None if the private attribute is unset
        return self._pipeline_id if self._is_defined("_pipeline_id") else None
    
    @pipeline_id.setter
    def pipeline_id(self, pId: str) -> None:
        # Display
        self._print("Pipeline ID: '%s'" %pId, end="", flush=True)
        # Call deleter if agument is None
        if pId is None: 
            del self.pipeline_id
            return
        # Check type
        if not isinstance(pId, str):
            raise TypeError("`pipeline_id` should be a string")
        # Check the ID (if possible)
        if self._check_pipeline_id(pId):
            self._print(" --> checked")
        else: self._print(" --> unchecked")
        # Check for conflict with private attribute
        self._check_value("_pipeline_id", pId)
        # Set
        self._pipeline_id = pId

    @pipeline_id.deleter
    def pipeline_id(self) -> None:
        # Delete only if the private attribute is defined
        if self._is_defined("_pipeline_id"): 
            del self._pipeline_id
    # ------------------------------------------------

    # Input settings
    @property
    def input_settings(self) -> dict:
        """All parameters needed to run the pipeline 
        Run show_pipeline() for more information"""
        # Return None if the private attribute is unset
        return self._get_input_settings() if self._is_defined("_input_settings") else None
    
    @input_settings.setter
    def input_settings(self, input_settings: dict):
        # Call deleter if agument is None
        if input_settings is None: 
            del self.input_settings
            return
        # Display
        self._print("Input Settings --> ", end="", flush=True)
        # Check type
        if not isinstance(input_settings, dict):
            raise TypeError("`input_settings` should be a dictionary")
        # Check if each input can be converted to a string with valid characters for VIP
        for param, value in input_settings.items():
            invalid = self._invalid_chars_for_vip(value)
            # if not (set(invalid) <= {'\\'}): # '\\' is OK for Windows paths #EDIT: Corrected in _invalid_chars_for_vip
            if invalid:
                raise ValueError(
                    f"Parameter '{param}' contains some invalid character(s): {', '.join(invalid)}"
                )
        # Parse the input settings
        new_settings = self._parse_input_settings(input_settings)
        self._print("parsed")
        # Check conflicts with private attribute
        self._check_value("_input_settings", new_settings)
        # Update
        self._input_settings = new_settings

    @input_settings.deleter
    def input_settings(self) -> None:
        # Delete only if the private attribute is defined
        if self._is_defined("_input_settings"): 
            del self._input_settings
    # ------------------------------------------------

    # Output directory
    @property
    def vip_output_dir(self) -> str:
        """Path to the VIP directory where pipeline outputs will be stored"""
        # Return None if the private attribute is unset
        return str(self._vip_output_dir) if self._is_defined("_vip_output_dir") else None
    
    @vip_output_dir.setter
    def vip_output_dir(self, new_dir) -> None:
        # Call deleter if agument is None
        if new_dir is None: 
            del self.vip_output_dir
            return
        # Check type
        if not isinstance(new_dir, (str, os.PathLike)):
            raise TypeError("`vip_output_dir` should be a string or os.PathLike object")
        # Path-ify
        new_path = PurePosixPath(new_dir)
        # Check if the path contains invalid characters for VIP
        invalid = self._invalid_chars_for_vip(new_path)
        if invalid:
            raise ValueError(
                f"VIP output directory contains some invalid character(s): {', '.join(invalid)}"
            )
        # Check conflict with private attribute
        self._check_value("_vip_output_dir", new_path)
        # Assign
        self._vip_output_dir = new_path

    @vip_output_dir.deleter
    def vip_output_dir(self) -> None:
        # Delete only if the private attribute is defined
        if self._is_defined("_vip_output_dir"): 
            del self._vip_output_dir
    # ------------------------------------------------

    # Interface for the output directory
    @property
    def output_dir(self) -> str:
        """
        Safe interface for `vip_output_dir`.
        Setting `output_dir` will automatically load backup data if any.
        """
        return self.vip_output_dir
    
    @output_dir.setter
    def output_dir(self, new_dir: str) -> None:
        # Call deleter if agument is None
        if new_dir is None: 
            del self.vip_output_dir
            return
        # Display
        self._print("Output directory: '%s'" %new_dir)
        # Set the VIP output directory
        self.vip_output_dir = new_dir
        # Load backup data from the new output directory
        self._load()

    @output_dir.deleter
    def output_dir(self) -> None:
        # Delete only if the private attribute is defined
        if self._is_defined("vip_output_dir"): 
            del self.vip_output_dir
    # ------------------------------------------------

    # Workflows
    @property
    def workflows(self) -> dict:
        """Workflows inventory"""
        # Return empty dict if the private attribute is unset
        return self._workflows if self._is_defined("_workflows") else {}
    
    @workflows.setter
    def workflows(self, workflows: dict) -> None:
        # Check type
        if not isinstance(workflows, dict):
            raise TypeError("`workflows` should be a dictionary")
        # Check conflicts with instance value
        self._check_value("_workflows", workflows)
        # Assign
        self._workflows = workflows

    @workflows.deleter
    def workflows(self) -> None:
        # Delete only if the private attribute is defined
        if self._is_defined("_workflows"): 
            del self._workflows
    # ------------------------------------------------

    # Verbose state (not deletable)
    @property
    def verbose(self) -> bool:
        """
        This session will displays logs if `verbose` is True.
        """
        return self._verbose if self._is_defined("_verbose") else self._VERBOSE
    
    @verbose.setter
    def verbose(self, verbose: bool) -> None:
        self._verbose = verbose
    # -----------------------------------------------

    # Lock Properties to avoid accidental confusion between VIP executions
    @property
    def _locked(self) -> bool:
        """
        Boolean for locking session properties. 
        If True, a property must be deleted before reassignment.
        Default value: True
        """
        return self._locked_ if self._is_defined("_locked_") else True
    
    @_locked.setter
    def _locked(self, new_lock: bool) -> None:
        # Set
        self._locked_ = new_lock
    # -----------------------------------------------

    # Pipeline definition (read_only)
    @property
    def _pipeline_def(self) -> dict:
        """
        Gets the full definition of `pipeline_id` from VIP.
        Raises TypeError if `pipeline_id` unset.
        """
        # Check if the pipeline identifier is set
        if not self._is_defined("_pipeline_id"):
            raise TypeError("Pipeline identifier is unset")
        # Check if the pipeline definition is set
        if not self._is_defined("_pipeline_def_"):  
            self._pipeline_def_ = self._get_pipeline_def(self._pipeline_id)
        # Return the attribute
        return self._pipeline_def_
    # ------------------------------------------------
    

                    #############
    ################ Constructor ##################
                    #############

    def __init__(
            self, output_dir=None, pipeline_id: str=None,  
            input_settings: dict=None, session_name: str=None, verbose: bool=None
        ) -> None:
        """
        Create a VipLauncher instance and sets properties from keyword arguments. 

        ## Parameters
        - `output_dir` (str | os.PathLike object) Path to the VIP directory where pipeline outputs will be stored 
            (does not need to exist).
        
        - `pipeline_id` (str) Name of your pipeline in VIP. 
            - Usually in format : *application_name*/*version*.
            - Run VipLauncher.show_pipeline() to display available pipelines.

        - `input_settings` (dict) All parameters needed to run the pipeline.
            - Run VipLauncher.show_pipeline(`pipeline_id`) to display these parameters.
            - The dictionary can contain any object that can be converted to strings, or lists of such objects. 
            - Lists of parameters launch parallel workflows on VIP.

        - `session_name` [Recommended] (str) A name to identify this session.
            Default value: 'VipLauncher-[date]-[time]-[id]'

        - `verbose` [Optional] (bool) Verbose mode for this instance.
            - If True, instance methods will display logs;
            - If False, instance methods will run silently.

        `session_name` is only set at instantiation; other properties can be set later in function calls.
        If `output_dir` leads to data from a previous session, properties will be loaded from the backup file on VIP.
        """
        # Set the verbose mode
        self.verbose = verbose if verbose is not None else self._VERBOSE
        # Default value for session name
        self.session_name = session_name if session_name else self._new_session_name()
        # Display the session name only if arguments are given
        if any([session_name, output_dir, pipeline_id, input_settings]):
            self._print(f"\n=== SESSION '{self._session_name}' ===\n", max_space=2)
        # Set the output directory (/!\ this will load the corresponding backup data if any /!\)
        if output_dir :
            self.output_dir = output_dir
        # Unlock session properties
        with self._unlocked_properties():
            # Set Pipeline identifier
            if pipeline_id:
                self.pipeline_id = pipeline_id
            # Set Input settings
            if input_settings:
                self.input_settings = input_settings 
        # Set Workflows inventory
        if not self.workflows:
            self.workflows = {}
        # End display if we're in this class
        if any([session_name, output_dir, pipeline_id, input_settings]) and self.__name__ == "VipLauncher": 
            self._print()
    # ------------------------------------------------

                    ################
    ################ Public Methods ##################
                    ################

    #################################################
    # ($A) Manage a session from start to finish
    #################################################

    # ($A.1) Login to VIP
    @classmethod
    def init(cls, api_key="VIP_API_KEY", verbose=True, **kwargs) -> VipLauncher:
        """
        Handshakes with VIP using your own API key. 
        Returns a class instance which properties can be provided as keyword arguments.
        
        ## Parameters
        - `api_key` (str): VIP API key. This can be either:
            A. [unsafe] A **string litteral** containing your API key,
            B. [safer] A **path to some local file** containing your API key,
            C. [safer] The **name of some environment variable** containing your API key (default: "VIP_API_KEY").
        In cases B or C, the API key will be loaded from the local file or the environment variable. 
        
        - `verbose` (bool): default verbose mode for all instances.
            - If True, all instances will display logs by default;
            - If False, all instance methods will run silently by default.

        - `kwargs` [Optional] (dict): keyword arguments or dictionnary setting properties of the returned instance.     
        """
        # Set the default verbose mode for all sessions
        cls._VERBOSE = verbose
        # Check if `api_key` is in a local file or environment variable
        true_key = cls._get_api_key(api_key)
        # Set User API key
        try:
            # setApiKey() may return False
            assert vip.setApiKey(true_key), \
                f"(!) Unable to set the VIP API key: {true_key}.\nPlease check the key or retry later."
        except RuntimeError as vip_error:
            # setApiKey() may throw RuntimeError in case of bad key
            cls._printc(f"(!) Unable to set the VIP API key: {true_key}.\n    Original error message:")
            raise vip_error
        except(json.decoder.JSONDecodeError) as json_error:
            # setApiKey() may throw JSONDecodeError in special cases
            cls._printc(f"(!) Unable to set the VIP API key: {true_key}.\n    Original error message:")
            raise json_error
        # Update the list of available pipelines
        try:
            cls._get_available_pipelines() # RunTimeError is handled downstream
        except(json.decoder.JSONDecodeError) as json_error:
            # The user still cannot communicate with VIP
            cls._printc(f"(!) Unable to communicate with VIP.")
            cls._printc(f"    Original error messsage:")
            raise json_error
        cls._printc()
        cls._printc("----------------------------------")
        cls._printc("| You are communicating with VIP |")
        cls._printc("----------------------------------")
        cls._printc()
        # Double check user can access pipelines
        if not cls._AVAILABLE_PIPELINES: 
            cls._printc("(!) Your API key does not allow you to execute pipelines on VIP.")
            cls._printc(f"    Please join some research group(s) on the Web portal: {cls._VIP_PORTAL}")  
        # Return a VipLauncher instance for method cascading
        return cls(verbose=(verbose and kwargs), **kwargs)
    # ------------------------------------------------

    # Launch executions on VIP 
    def launch_pipeline(
            self, pipeline_id: str=None, input_settings: dict=None, output_dir=None, nb_runs=1,
        ) -> VipLauncher:
        """
        Launches pipeline executions on VIP.

        Input parameters :
        - `pipeline_id` (str) Name of your pipeline in VIP. 
            Usually in format : *application_name*/*version*.
        - `input_settings` (dict) All parameters needed to run the pipeline.
            - Run VipSession.show_pipeline(`pipeline_id`) to display these parameters.
            - The dictionary can contain any object that can be converted to strings, or lists of such objects.
            - Lists of parameters launch parallel workflows on VIP.
        - `output_dir` (str) Path to the VIP folder where execution results will be stored.
            (Does not need to exist)
        - `nb_runs` (int) Number of parallel workflows to launch with the same `pipeline_id`/`input_settings`.

        Error profile:
        - Raises TypeError:
            - if some argmuent could not be checked;
            - if some argument is missing; 
            - if some parameter is missing in `input_settings`.
        - Raises ValueError:
            - if some argument conflicts with session properties;
            - if some parameter in `input_settings` does not the fit the pipeline definition.
        - Raises FilenotFoundError if an input file is missing on VIP servers.
        - Raises RuntimeError in case of failure from the VIP API.
        """
        # First display
        self._print("\n=== LAUNCH PIPELINE ===\n")
        # Update the parameters
        if pipeline_id:
            self.pipeline_id = pipeline_id
        if output_dir: 
            self.vip_output_dir = output_dir
        if input_settings:
            self.input_settings = input_settings
        # Start parameter checks
        self._print(min_space=1, max_space=1)
        self._print("Parameter checks")
        self._print("----------------")
        # Check the pipeline identifier
        self._print("Pipeline identifier: ", end="", flush=True)
        if not self._check_pipeline_id():
            raise TypeError(f"(!) Pipeline identifier could not be checked. Please call {self.__name__}.init()")
        self._print("OK")
        # Check the result directory
        if not self._is_defined("_vip_output_dir"):
            raise TypeError("Please provide an output directory for Session: %s" %self._session_name)
        else: self._print("Output directory: ", end="", flush=True)
            # Ensure the directory exists
        if self._mkdirs(path=self._vip_output_dir, location=self._SERVER_NAME):
            self._print(f"Created on {self._SERVER_NAME.upper()}")
        else:
            self._print("OK")
        # Check the input parameters
        self._print("Input settings: ", end="", flush=True)
            # Check existence
        if not self._is_defined("_input_settings"):
            raise TypeError("Please provide input parameters for Session: %s" %self._session_name)  
            # Check content
        self._check_input_settings(location=self._SERVER_NAME)
        self._print("OK")
        # End parameters checks
        self._print("----------------\n")
        # Start pipeline launch
        self._print("Launching %d new execution(s) on VIP" % nb_runs)
        self._print("-------------------------------------")
        self._print("Execution Name:", self._session_name)
        self._print("Started Workflows:", end="\n\t")
        # Launch all executions in parallel
        for nEx in range(nb_runs):
            # Initiate execution
            try:
                workflow_id = self._init_exec()
            # This part may fail for a number of reasons
            except Exception as e: 
                self._print("\n-------------------------------------")
                self._print(f"(!) Stopped after {nEx} execution(s).\n")
                self._save()
                raise e from None
            # Display
            self._print(workflow_id, end=", ")
            # Get workflow informations
            try: 
                exec_infos = self._get_exec_infos(workflow_id)
            except Exception as e: 
                self._save()
                raise e from None
            # Create or update workflow entry (depends on init_exec())
            if workflow_id in self._workflows: 
                self._workflows[workflow_id].update(exec_infos)
            else: 
                self._workflows[workflow_id] = exec_infos
        # End the application launch
        self._print("\n-------------------------------------")
        self._print("Done.")
        # Save the session
        self._save()
        # Return
        return self
    # ------------------------------------------------

    # Monitor worflow executions on VIP 
    def monitor_workflows(self, refresh_time=30) -> VipLauncher:
        """
        Updates and displays status for each execution launched in the current session.
        - If an execution is still running, updates status every `refresh_time` (seconds) until all runs are done.
        - Displays a full report when all executions are done.

        Error profile:
        - Raises RuntimeError if the client fails to communicate with VIP.
        """
        self._print("\n=== MONITOR WORKFLOWS ===\n")
        # Check if current session has existing workflows
        if not self._workflows:
            self._print("This session has not launched any execution.")
            self._print("Run launch_pipeline() to launch workflows on VIP.")
            return self
        # Update existing workflows
        self._print("Updating worflow inventory ... ", end="", flush=True)
        self._update_workflows()
        self._print("Done.")
        # Check if workflows are still running
        if self._still_running():
            # First execution report
            self._execution_report()
            # Display standby
            self._print("\n-------------------------------------------------------------")
            self._print("The current proccess will wait until all executions are over.")
            self._print("Their progress can be monitored on VIP portal:")
            self._print(f"\t{self._VIP_PORTAL}")
            self._print("-------------------------------------------------------------")
            # Standby until all executions are over
            time.sleep(refresh_time)
            while self._still_running():
                # Keep track of time
                start = time.time()
                # Update the workflow status & discard connection errors
                try:
                    self._update_workflows()
                except Exception as e:
                    # Print warning message
                    self._print("(!) Connection with VIP was interrupted following an unexpected error (see below).")
                    self._print("    This does not affect your executions on VIP servers.")
                    self._print("    Relaunch monitor_workflows() or visit the VIP portal to see their current status.\n")
                    # Save the session
                    self._save()
                    # Raise the error
                    raise e
                # Sleep until next itertation
                elapsed_time = time.time() - start
                time.sleep(max(refresh_time - elapsed_time, 0))
            # Display the end of executions
            self._print("All executions are over.")
        # Last execution report
        self._execution_report()
        # Save the session
        self._save()
        # Return
        return self
    # ------------------------------------------------

    # Run a full VipLauncher session
    def run_session( self, nb_runs=1, refresh_time=30) -> VipLauncher:
        """
        Runs a full session from data on VIP servers:
        1. Launches pipeline executions on VIP;
        2. Monitors pipeline executions until they are all over.

        /!\ This function assumes that all session properties are already set.
        Optional arguments can be provided:
        - Increase `nb_runs` to run more than 1 execution at once;
        - Set `refresh_time` to modify the default refresh time;
        """
        # Run the pipeline
        return (
            # 1. Launch `nb_runs` pipeline executions on VIP
            self.launch_pipeline(nb_runs=nb_runs)
            # 2. Monitor pipeline executions until they are over
            .monitor_workflows(refresh_time=refresh_time)
        )
    # ------------------------------------------------

    # Clean session data on VIP
    def finish(self, timeout=300) -> VipLauncher:
        """
        Removes session's output data from VIP servers. 

        Detailed behaviour:
        - This process checks folder deletion on VIP servers until `timeout` (seconds) is reached.
        - Workflows status are set to "Removed" when the corresponding outputs have been removed.
        """
        # Initial display
        self._print("\n=== FINISH ===\n")
        self._print("Ending Session:", self._session_name)
        # Check if workflows are still running (without call to VIP)
        if self._still_running():
            # Update the workflow inventory
            self._print("Updating worflow inventory ... ", end="", flush=True)
            self._update_workflows()
            self._print("Done.")
            # Return is workflows are still running
            if self._still_running():
                self._print("\n(!) This session cannot be finished since the pipeline might still generate data.\n")
                self._execution_report()
                return self
        # Enter removal phase
        self._print("Removing session data")
        self._print("---------------------")
        # Browse paths to delete
        success = True
        for path, location in self._path_to_delete().items():
            # Display progression
            self._print(f"[{location}] {path} ... ", end="", flush=True)
            # Check data existence
            if not self._exists(path, location):
                # Session may be already over
                self._print("Already removed.")
            else:
                # Erase the path
                done = self._delete_and_check(
                    path=path, location=location, timeout=timeout
                    )
                # Display 
                if done:
                    self._print("Done.")
                else:
                    self._print(f"\n\t(!) Timeout reached ({timeout} seconds).")
                # Update success
                success = success and done
        # End of loop
        self._print("---------------------\n")
        self._print("Updating workflows status")
        self._print("-------------------------")
        # Set the workflow status to "removed" to avoid dead links in future downloads
        if not self._workflows:
            self._print(f"No registered workflow")
            removed_outputs = success
        else:
            removed_outputs = True
        for wid in self._workflows:
            self._print(f"{wid}: ", end="", flush=True)
            if (
                # The output list is empty
                not self._workflows[wid]["outputs"] 
                # Workflow's output directory does not exist anymore
                or not self._exists(PurePosixPath(self._workflows[wid]["outputs"][0]["path"]).parent, location="vip")
            ):
                # Set the workflow status to "Removed"
                self._workflows[wid]["status"] = "Removed"
                self._print("Removed")
            else:
                # Workflow's outputs still exist on VIP
                removed_outputs = False
                self._print("Still on VIP")
        # Last display
        self._print("-------------------------")
        if removed_outputs:
            self._print("All output data have been removed from VIP.")
            if success:
                self._print(f"Session '{self._session_name}' is now over.")
        else:
            self._print("(!) There may still be temporary data on VIP.")
            self._print(f"Please run finish() again or check the following path(s) on the VIP portal ({self._VIP_PORTAL}):")
            self._print('\n\t'.join([str(path) for path in self._path_to_delete()]))
            # Finish display
            self._print()
        # Return 
        return self
    # ------------------------------------------------

    ###########################################
    # Additional Features
    ###########################################

    @classmethod
    def show_pipeline(cls, pipeline_id: str=None) -> None:
        """
        Displays useful informations about VIP pipelines.

        This method can be used to browse among available pipelines, 
        or as a brief guide to build valid `input_settings` for a given pipeline.

        Detailed behaviour:
        - If `pipeline_id` is None, shows the list of all available pipelines.
        - If `pipeline_id` is not exact, shows a list of pipelines with a *partial*, *case-insensitive* match.
        - If `pipeline_id` is exact, shows the list of parameters required to run `pipeline_id`.
        """
        # Return if _VERBOSE is False
        if not cls._VERBOSE: return
        # Check init() was called first
        if not cls._AVAILABLE_PIPELINES:
            raise TypeError(
                f"No pipeline found. Run {cls.__name__}.init() to access pipeline descriptions."
            )
        # Find all case-insensitive partial matches between `pipeline_id` and cls._AVAILABLE_PIPELINES
        if pipeline_id:            
            pipelines = [
                pipe for pipe in cls._AVAILABLE_PIPELINES
                if pipeline_id.lower() in pipe.lower()
            ]
        else: # In case no argument is given
            pipelines = cls._AVAILABLE_PIPELINES
        # Display depending on the number of pipelines found
        if not pipelines: # Case no match
            cls._printc(f"(!) No pipeline found for pattern '{pipeline_id}'.")
            cls._printc(f"    You may need to register with the correct group.")
        elif len(pipelines) > 1: # Case multiple matches
            # Print the list of matching pipelines
            cls._printc()
            cls._printc("Available pipelines")
            cls._printc("-------------------")
            cls._printc("\n".join(pipelines))
            cls._printc("-------------------")
        else: # Case single match
            pipeline_id = pipelines[0]
            # Display pipeline ID
            cls._printc('='*len(pipeline_id))
            cls._printc(pipeline_id)
            cls._printc('='*len(pipeline_id), end="")
            # Get pipeline_definition
            pipeline_def = cls._get_pipeline_def(pipeline_id)
            # Get header
            pipe_header = f"NAME: {pipeline_def['name']} | VERSION: {pipeline_def['version']}"
            # Define text width & wrapper
            text_width = max(70, len(pipe_header))
            wrapper = textwrap.TextWrapper(
                width = text_width,
                initial_indent = '    ',
                subsequent_indent = '    ',
                max_lines = 10,
                drop_whitespace=False,
                replace_whitespace = False,
                break_on_hyphens = False,
                break_long_words = False
            )
            # Display header
            cls._printc('='*(text_width-len(pipeline_id)))
            cls._printc(pipe_header)
            cls._printc('-'*text_width)
            # Display pipeline description
            pipe_description = cls._clean_html(pipeline_def['description'])
            cls._printc(f"DESCRIPTION:")
            cls._printc(pipe_description, wrapper=wrapper)
            cls._printc('-'*text_width)
            # Print a description for each pipeline parameter
            cls._printc("INPUT_SETTINGS:")
                # Function to display one paramter
            def display_parameter(param: dict) -> None:
                """Prints name, type & description"""
                cls._printc(f"- {param['name']}")
                cls._printc(f"[{param['type'].upper()}]", cls._clean_html(param['description']), 
                            wrapper=wrapper)
                # Non-Optional parameters sorted by name
            cls._printc("REQUIRED" + "." * (text_width-len("REQUIRED")))
            for param in sorted( 
                    [param for param in pipeline_def['parameters'] if not param["isOptional"]],
                    key = lambda param: param["name"]
                ): display_parameter(param)
                # Optional parameters sorted by name
            cls._printc("OPTIONAL" + "." * (text_width-len("OPTIONAL")))
            for param in sorted(
                [param for param in pipeline_def['parameters'] if param["isOptional"]],
                key = lambda param: param["name"]
                ): display_parameter(param)
            # End the display
            cls._printc('='*text_width)
            cls._printc()
    # ------------------------------------------------

    # Display current session state
    def display(self) -> VipLauncher:
        """
        Displays useful properties in JSON format.
        - `session_name` : current session name
        - `pipeline_id`: pipeline identifier
        - `output_dir` : path to the pipeline outputs
        - `input_settings` : input parameters sent to VIP 
        - `workflows`: workflow inventory, identifying all pipeline runs in this session.
        """
        # Get properties
        session_data = self._data_to_save()
        # Print session name
        name_str = f'Session: "{session_data["session_name"]}"'
        self._print("-"*len(name_str))
        self._print(name_str)
        self._print("-"*len(name_str))
        del session_data["session_name"]
        # Print the rest
        for prop in session_data:
            self._print(f"{prop}: {json.dumps(session_data[prop], indent=3)}")
        self._print("-"*len(name_str))
        # End the display 
        self._print()
        # Return for method cascading
        return self
    # ------------------------------------------------

                    #################
    ################ Private Methods ################
                    #################

    ###################################################################
    # Methods that must be overwritten to adapt VipLauncher methods to
    # new locations
    ###################################################################

    # Path to delete during session finish
    def _path_to_delete(self) -> dict:
        """Returns the folders to delete during session finish, with appropriate location."""
        return {
            self._vip_output_dir: "vip"
        }
    # ------------------------------------------------

    # Method to check existence of a distant resource.
    @classmethod
    def _exists(cls, path, location="vip") -> bool:
        """
        Checks existence of a distant resource (`location`="vip").
        `path` can be a string or Pathlib object.
        """
        # Check `location`
        if location != "vip":
            raise NotImplementedError(f"Unknown location: {location}")
        # Check path existence
        try: 
            return vip.exists(str(path))
        except RuntimeError as vip_error:
            # Connection error with VIP
            cls._handle_vip_error(vip_error)
        except json.decoder.JSONDecodeError:
            raise ValueError(
                f"The following path generated an error on VIP:\n\t{path}\n"
                + "Please check this path or retry later."
                )
    # ------------------------------------------------
    
    # Method to create a distant directory
    @classmethod
    def _create_dir(cls, path: PurePath, location="vip") -> None:
        """
        Creates a directory at `path`, on VIP servers if `location` is "vip".

        `path`can be a string or PathLib object.
        Returns the VIP path of the newly created folder.
        """
        # Check `location`
        if location != "vip": 
            raise NotImplementedError(f"Unknown location: {location}")
        # Create directory
        try: 
            if not vip.create_dir(str(path)):
                msg = f"The following directoy could not be created on VIP:\n\t{path}\n"
                msg += f"Please retry later. Contact VIP support ({cls._VIP_SUPPORT}) if this cannot be fixed."
                raise AssertionError(msg)
        except RuntimeError as vip_error:
            cls._handle_vip_error(vip_error)  
        except json.decoder.JSONDecodeError as json_error:
            raise ValueError(
                f"The following path generated an error on VIP:\n\t{path}\n"
                + "Please check this path is valid and/or consistent with your other inputs."
                )
    # ------------------------------------------------

    # Function to delete a path
    @classmethod
    def _delete_path(cls, path: PurePath, location="vip") -> None:
        """
        Deletes `path` on `location`. Raises an error if the file exists and could not be removed.
        """
        # Check `location`
        if location != "vip":
            raise NotImplementedError(f"Unknown location: {location}")
        # Try path deletion
        done = vip.delete_path(str(path))
        # VIP Errors are handled by returning False in `vip.delete_path()`.
        if not done and vip.exists(str(path)):
            # Raise a generic error if deletion did not work
            msg = f"\n'{path}' could not be removed from VIP servers.\n"
            msg += "Check your connection with VIP and path existence on the VIP portal.\n"
            raise RuntimeError(msg)
    # ------------------------------------------------
    
    # Function to delete a path on VIP with warning
    @classmethod
    def _delete_and_check(cls, path: PurePath, location="vip", timeout=300) -> bool:
        """
        Deletes `path` on `location` and waits until `path` is actually removed.
        After `timeout` (seconds), displays a warning if `path` still exist.
        """
        # Delete the path
        cls._delete_path(path, location)
        # Standby until path is indeed removed (give up after some time)
        start = time.time()
        t = time.time() - start
        while (t < timeout) and cls._exists(path, location):
            time.sleep(2)
            t = time.time() - start
        # Check if the data have indeed been removed
        return (t < timeout)
    # ------------------------------------------------
    
    ##########################################################
    # Generic private methods than should work in any subclass
    ##########################################################
    
    # Method to create a directory leaf on the top of any path, at any location
    @classmethod
    def _mkdirs(cls, path: PurePath, location: str, **kwargs) -> str:
        """
        Creates each non-existent directory in `path` (like os.mkdirs()), 
        in the file system pointed by `location`.
        - Directories are created using: cls._create_dir(`path`, `location`, **`kwargs`)
        - Existence is checked using: cls._exists(`path`, `location`).

        Returns the newly created part of `path` (empty string if `path` already exists).
        """
        # Case : the current path exists
        if cls._exists(path=path, location=location) :
            return ""
        # Find the 1rst non-existent node in the arborescence
        first_node = path
        while not cls._exists(first_node.parent, location=location):
            first_node = first_node.parent
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
    
    # Generic method to get session properties
    def _get(self, *args):
        """
        Get multiple session properties such as: "session_name", "pipeline_id", "input_settings".
        - If a single property is provided, returns its value.
        - If this property is undefined, returns None.
        - If multiple properties are provided, returns a dictionary with (property, value) as items.
        """
        # Case: no argument
        if not args: return None
        # Case: single argument
        elif len(args) == 1:
            return getattr(self, args[0])
        # Case: multiple arguments
        else: 
            return {prop: self._get(prop) for prop in args}
    # ------------------------------------------------
    
    # Generic method to set session properties
    def _set(self, **kwargs) -> None:
        """
        Sets multiple session properties based on keywords arguments or mapping object `kwargs`.
        Deletes property when value is None.
        """
        # Browse keyword arguments
        for property, value in kwargs.items():
            # Set attribute
            setattr(self, property, value)
    # ------------------------------------------------

    ##################################################
    # Context managers
    ##################################################

    # Simple context manager to unlock session properties while executing code
    @contextmanager
    def _unlocked_properties(self) -> None:
        """
        Under this context, session properties can be modified without raising an error.
        """
        saved_lock = self._locked # save lock mode
        self._locked = False # unlock properties
        yield
        self._locked = saved_lock # restore lock mode
    # ------------------------------------------------

    # Simple context manager to silence session logs while executing code
    @contextmanager
    def _silent_session(self) -> None:
        """
        Under this context, the session will not print anything.
        """
        verbose = self._verbose # save verbose mode
        self._verbose = False # silence instance logs
        yield
        self._verbose = verbose # restore verbose mode
    # ------------------------------------------------

    # Simple context manager to silence logs from class methods while executing code
    @classmethod
    @contextmanager
    def _silent_class(cls) -> None:
        """
        Under this context, the session will not print anything.
        """
        verbose = cls._VERBOSE # save verbose mode
        cls._VERBOSE = False # silence instance logs
        yield
        cls._VERBOSE = verbose # restore verbose mode
    # ------------------------------------------------

    # init
    #################################################
    @classmethod
    def _get_api_key(cls, api_key: str) -> str:
        """
        - `api_key` (str): VIP API key. This can be either:
            A. [unsafe] A **string litteral** containing your API key,
            B. [safer] A **path to some local file** containing your API key,
            C. [safer] The **name of some environment variable** containing your API key (default: "VIP_API_KEY").
        In cases B or C, the API key will be loaded from the local file or the environment variable. 
        """
        # Check if `api_key` is in a local file or environment variable
        if os.path.isfile(api_key): # local file
            with open(api_key, "r") as kfile:
                true_key = kfile.read().strip()
        elif api_key in os.environ: # environment variable
            true_key = os.environ[api_key]
        else: # string litteral
            true_key = api_key
        # Return
        return true_key
    # ------------------------------------------------

    # (A.3) Launch pipeline executions on VIP servers
    ##################################################
    @classmethod
    def _new_session_name(cls) -> str:
        """Returns a new session name in format: [class]-[date]-[time]-[id]"""
        from random import randint
        return "-".join([cls.__name__, time.strftime("%y%m%d-%H%M%S", time.localtime()), "%03x" % randint(0, 16**3)])

    def _init_exec(self) -> str:
        """
        Initiates one VIP workflow with local properties `pipeline_id`, `session_name`, `input_settings`, `output_dir`.
        - Returns the workflow identifier.
        - Raises RuntimeError in case of error from VIP
        """
        try:
            return vip.init_exec(
                pipeline = self.pipeline_id, 
                name = self.session_name, 
                inputValues = self.input_settings,
                resultsLocation = self.vip_output_dir
            )
        except RuntimeError as vip_error:
            self._handle_vip_error(vip_error)
    # ------------------------------------------------

    # (A.4) Monitor pipeline executions on VIP servers
    ##################################################
    # Get and display a report over all executions in the current session
    def _execution_report(self, display=True) -> dict:
        """
        Sorts workflows by status. Returns the result in dictionnary shape.
        If `display` is True, interprets the result to the user.
        """
        # Initiate status report
        report={}
        # Browse workflows
        for wid in self._workflows:
            # Get status
            status = self._workflows[wid]["status"]
            # Update the report
            if status in report:
                report[status].append(wid) # update status
            else:
                report[status] = [wid] # create status
        # Interpret the report to the user
        if display:
            # Function to print a detailed worfklow list
            def detail(worfklows: list): 
                for wid in worfklows:
                    self._print("\t", wid, ", started on:", self._workflows[wid]["start"])
            # Browse status
            for status in report:
                # Display running executions
                if status == 'Running':
                    # check if every workflow is running
                    if len(report[status])==len(self._workflows):
                        self._print(f"All executions are currently running on VIP.")
                    else: # show details
                        self._print(f"{len(report[status])} execution(s) is/are currently running on VIP:")
                        detail(report[status])
                # Display successful executions
                elif status == 'Finished':
                    # check if every run was successful
                    if len(report[status])==len(self._workflows):
                        self._print(f"All executions ({len(report[status])}) ended with success.")
                    else: # show details
                        self._print(f"{len(report[status])} execution(s) ended with success:")
                        detail(report[status])
                # Display executions with removed data
                elif status == 'Removed':
                    # check if every run was removed
                    if len(report[status])==len(self._workflows):
                        self._print("This session is over.")
                        self._print("All output data were removed from VIP servers.")
                    else: # show details
                        self._print(f"Outputs from {len(report[status])} execution(s) were removed from VIP servers:")
                        detail(report[status])
                # Display failed executions
                else:
                    # check if every run had the same cause of failure:
                    if len(report[status])==len(self._workflows):
                        self._print(f"All executions ({len(report[status])}) ended with status:", status)
                    else: # show details
                        self._print(f"{len(report[status])} execution(s) ended with status:", status)
                        detail(report[status])
            # End of display loop
        # Return the report
        return report
    # ------------------------------------------------

    def _still_running(self) -> int:
        """
        Returns the number of workflows which are still running on VIP.
        (!) Requires prior call to self._update_workflows to avoid unnecessary connexions to VIP
        """
        # Workflow count
        count = 0
        for wid in self._workflows:
            # Update count
            count += int(self._workflows[wid]["status"]=="Running")
        # Return count
        return count   
    # ------------------------------------------------

    # Update all worflow information at once
    def _update_workflows(self) -> None:
        """
        Updates the status of each workflow in the inventory. 
        """
        for wid in self._workflows:
            # Check if workflow data have been removed
            if self._workflows[wid]["status"] != "Removed":
                # Recall execution info & update the workflow status
                self._workflows[wid].update(self._get_exec_infos(wid))
    # ------------------------------------------------

    # Method to get useful information about a given workflow
    @classmethod
    def _get_exec_infos(cls, workflow_id: str) -> dict:
        """
        Returns succint information on `workflow_id`:
        - Execution status (VIP notations)
        - Starting time (local time, format '%Y/%m/%d %H:%M:%S')
        - List of paths to the output files.
        """
        # Get execution infos
        try :
            infos = vip.execution_info(workflow_id)
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
            # Returned files (filtered information)
            "outputs": [] if not infos["returnedFiles"] else [
                {"path": value} for value in infos["returnedFiles"]["output_file"] 
            ]
        }
    # ------------------------------------------------

    ##################################################
    # Save / load Session Metadata
    ##################################################

    # Data to save
    def _data_to_save(self) -> dict:
        """Returns the data to save as a dictionnary"""
        return self._get(*self._PROPERTIES)
    # ------------------------------------------------

    # Generic method to save (should work on child classes)
    def _save(self) -> bool:
        """
        Generic method to save session properties.
        - Compares both session data and data from the backup file;
        - Raises ValueError if the session names do not match;
        - Saves backup properties that are not included in the session data;
        - Returns a success flag;
        - Displays information unless `_VERBOSE` is False.
        """
        # Return if no-backup mode is activated
        if self._BACKUP_LOCATION is None:
            return False
        # Get session properties
        session_data = self._data_to_save()
        # Get backup data from the output directory
        with self._silent_session():
            backup_data = self._load_session(location=self._BACKUP_LOCATION)
        # If there is no backup data (i.e. None or empty dict), save immediately
        if not backup_data:
            return self._save_session(session_data, location=self._BACKUP_LOCATION)
        # If the session name is different from backup, raise an error
        if backup_data["session_name"] != session_data["session_name"]:
            raise ValueError(
                f"The backup data have a different session name ('{backup_data['session_name']}').\n"
                +"Please change the session name or provide another output directory."
            )
        # If the backup data have more properties than current session, save them along with session properties
        new_props = set(backup_data.keys()) - set(session_data.keys())
        if new_props:
            # Update the data to save
            session_data.update({prop: backup_data[prop] for prop in new_props})
        # Save to target
        return self._save_session(session_data, location=self._BACKUP_LOCATION)
    # ------------------------------------------------

    # Generic method to load (should work on child classes)
    def _load(self) -> bool:
        """
        Loads backup data as defined in load_session() and compares both session and backup data.
        - Raises ValueError if the session names do not match;
        - Prints warnings and reject the backup if other properties are defined and do not match ;
        - Returns a success flag.
        """
        # Return if no-backup mode is activated
        if not self._BACKUP_LOCATION:
            return False
        # Get backup data from the output directory
        backup_data = self._load_session(location=self._BACKUP_LOCATION)
        # Case: no backup data (None or empty dict)
        if not backup_data:
            return False
        # Get current session properties
        session_data = self._data_to_save()
        # If session properties are undefined, set them silently and return
        if session_data["session_name"] is None:
            with self._unlocked_properties(), self._silent_session():
                self._set(**backup_data)
            return True
        # If the backup data do not have the right properties, raise TypeError
        missing_props = set(session_data.keys()) - set(backup_data.keys())
        if missing_props:
            raise TypeError(f"The following properties are missing in the backup data:\n\t{', '.join(missing_props)}")
        # If the backup data have more properties than current session, do not load them
        new_props = set(backup_data.keys()) - set(session_data.keys())
        for prop in new_props: 
            del backup_data[prop]
        # If the session name is not default and different from backup, raise ValueError
        if (not session_data["session_name"].startswith(self.__name__) 
            and (backup_data["session_name"] != session_data["session_name"]) ):
            raise ValueError(
                f"The backup data have a different session name: \n\t'{backup_data['session_name']}' VS '{self.session_name}'.\n"
                +"Please change the session name or provide another output directory."
            )
        # Compare every other session properties, except the workflow inventory.
        diff = [ prop 
                for prop in session_data 
                    if ((prop not in ["session_name", "workflows"]) 
                    and (backup_data[prop] is not None )
                    and (session_data[prop] is not None )
                    and (session_data[prop] != backup_data[prop])) ]
        # If differences are found, print a warning an do not silence the setter methods.
        if diff:
            self._print(f"(!) The following properties will be overwritten by session backup:\n\t{', '.join(diff)}\n")
            silent_context = nullcontext
        else: 
            silent_context = self._silent_session
        # Overwrite all instance properties and return True
        with self._unlocked_properties(), silent_context():
            self._set(**backup_data)
        return True
    # ------------------------------------------------

    # Save session properties to a JSON file on VIP
    def _save_session(self, session_data: dict, location="vip") -> bool:
        """
        Saves dictionary `session_data` to a JSON file, in the output directory at `location`.
        Returns a success flag.
        Displays success / failure unless `_VERBOSE` is False.
        """
        # Thow error if location is unknown
        if location != "vip":
            return NotImplementedError(f"Location '{location}' is unknown for {self.__name__}")
        # Display
        self._print(f"\nSaving session properties ...")
        # Temporary file to save session data
        tmp_file = Path("tmp_save.json")
        # Save the data in JSON format
        with tmp_file.open("w") as outfile:
            json.dump(session_data, outfile, indent=4)
        # Path to the backup file on VIP
        vip_file = self._vip_output_dir / self._SAVE_FILE
        # Make the output directory if it does not exist
        is_new = self._mkdirs(vip_file.parent, location=location)
        # Delete the previous file if it exists
        if not is_new:
            self._delete_and_check(vip_file, location=location, timeout=30)
        # Send the temportary file on VIP (no error raised)
        done = self._upload_file(tmp_file, vip_file)
        # Delete the temporary file
        tmp_file.unlink()
        # Display
        self._print()
        if done and is_new: self._print(f">> Session was saved in: {vip_file}\n")
        elif done:  self._print(f">> Session saved\n")
        else: self._print(f"(!) Session backup failed\n")
        return done
    # ------------------------------------------------

    # Load session properties from a JSON file on VIP
    def _load_session(self, location="vip") -> dict:
        """
        Loads backup data from the output directory.
        If the backup file could not be read, returns None.
        Otherwise, returns session properties as a dictionary. 
        """
        # Thow error if location is unknown
        if location != "vip":
            return NotImplementedError(f"Location '{location}' is unknown for {self.__name__}")
        # Display
        self._print(f"\nLoading session properties ...", )
        # Return if the VIP input directory is not defined
        if not self._is_defined("_vip_output_dir"):
            return None
        # Check existence of data from a previous session
        vip_file = self._vip_output_dir / self._SAVE_FILE
        if not self._exists(vip_file, location=location):
            return None
        # Temporary file for download
        tmp_file = Path("tmp_load.json")
        # Download the file
        done = self._download_file(vip_file, tmp_file)
        if not (done and tmp_file.exists()):
            self._print("\n(!) Unable to load backup data from session's output directory\n")
            return None
        # Load the JSON file
        with tmp_file.open() as fid:
            session_data = json.load(fid)
        # Delete the temporary file
        tmp_file.unlink()
        # Display success
        self._print("<< Session restored from its output directory\n")
        # Return
        return session_data
    # ------------------------------------------------
    
    # Function to download a single file from VIP
    @classmethod
    def _download_file(cls, vip_path: PurePosixPath, local_path: Path) -> bool:
        """
        Downloads a single file in `vip_path` to `local_path`.
        Returns a success flag.
        """
        # Download (file existence is not checked to save time)
        try:
            return vip.download(str(vip_path), str(local_path))
        except RuntimeError as vip_error:
            return False
    # ------------------------------------------------    
    
    # Function to upload a single file on VIP
    @classmethod
    def _upload_file(cls, local_path: Path, vip_path: PurePosixPath) -> bool:
        """
        Uploads a single file in `local_path` to `vip_path`.
        Returns a success flag.
        """
        # Upload
        try:
            return vip.upload(str(local_path), str(vip_path))
        except RuntimeError as vip_error:
            return False
    # ------------------------------------------------   

    ###############################################################
    # Prevent common mistakes in session / pipeline settings 
    ###############################################################

    # Check if an attribute has been correctly defined
    def _is_defined(self, attribute) -> bool :
        """Returns True if `attribute` has already been set, False otherwise."""
        return (attribute in self.__dict__)
    # ------------------------------------------------
    
    # Check conflicts with instance value
    def _check_value(self, attribute: str, new_value) -> None:
        """
        If session properties are locked, raises ValueError if an attempt is made 
        to change the PRIVATE `attribute` with `new_value`.
        """
        # Check if attribute is already set and session properties are locked
        if not self._is_defined(attribute) or not self._locked: 
            return
        # Check conflict with the new value
        if getattr(self, attribute) != new_value:
            self._print()
            raise ValueError(f"'{attribute.lstrip('_')}' is already set for session: {self.session_name}.")
    # ------------------------------------------------

    # Check the pipeline identifier based on the list of available pipelines
    def _check_pipeline_id(self, pipeline_id: str="") -> bool:
        """
        Checks if the pipeline identifier `pipeline_id` is available for this session.
        Raises ValueError otherwise.
        If `pipeline_id` is not provided, checks instance property.
        (!) Requires prior call to init() to avoid useless connexion. Returns False otherwise.
        """
        # Check argument
        if not pipeline_id:
            if not self._is_defined("_pipeline_id"):
                raise TypeError("Please provide a pipeline identifier for Session: %s" %self._session_name)
            pipeline_id = self._pipeline_id
        # Available pipelines
        if not self._AVAILABLE_PIPELINES:
            return False
        # Check pipeline identifier
        if  pipeline_id not in self._AVAILABLE_PIPELINES:
            raise ValueError(
                f"'{pipeline_id}' is not a valid pipeline identifier.\n" 
                + f"Run {self.__name__}.show_pipeline() to show available pipelines."
            )
        # Return
        return True
    # ------------------------------------------------

    # Function that lists available pipeline identifiers for a given VIP accout
    @classmethod
    def _get_available_pipelines(cls) -> list:
        """
        Updates the list of available pipelines (`cls._AVAILABLE_PIPELINES`) for current VIP account 
        (defined by user API key). Returns the same list.
        """
        try:
            all_pipelines = vip.list_pipeline()
        except RuntimeError as vip_error:
            cls._handle_vip_error(vip_error)
        cls._AVAILABLE_PIPELINES = [ 
            pipeline["identifier"] for pipeline in all_pipelines 
            if pipeline["canExecute"] is True 
        ]
        return cls._AVAILABLE_PIPELINES
    # ------------------------------------------------

    # Get pipeline definition 
    @classmethod
    def _get_pipeline_def(cls, pipeline_id) -> dict:
        """
        Gets the full definition of `pipeline_id` from VIP.
        Raises RuntimeError if fails to communicate with VIP.
        """
        try :            
            return vip.pipeline_def(pipeline_id)
        except RuntimeError as vip_error:
            cls._handle_vip_error(vip_error)
    # ------------------------------------------------

    # Store the VIP paths as PathLib objects
    # (This is mainly useful for subclasses)
    def _parse_input_settings(self, input_settings) -> dict:
        """
        Parses the input settings, i.e.:
        - Converts all input paths to PathLib objects 
        - Leave the other parameters untouched.
        """
        # Function to convert VIP paths to PurePath objects
        def parse_value(input):
            # Case: multiple inputs
            if isinstance(input, list):
                return [ parse_value(element) for element in input ]
            # Case: single input
            if isinstance(input, (str, os.PathLike)):
                # Case: VIP path
                if str(input).startswith(self._SERVER_PATH_PREFIX):
                    return PurePosixPath(input)
                # Case: any other input
                else: return input
           # Case not string or path-like: return as is
            else: return input
        # -- End of parse_value() --
        # Return the parsed value of each input
        return {
            key: parse_value(value)
            for key, value in input_settings.items()
        }
    
    # Get the input settings after files are parsed as PathLib objects
    def _get_input_settings(self, location="vip") -> dict:
        """
        Returns the input settings with their orignal values in string format.
        `location` is destined to subclasses.
        """
        return {
            key: [str(v) for v in value] if isinstance(value, list) else str(value)
            for key, value in self._input_settings.items()
        }
    # ------------------------------------------------

    # Check the input settings based on the pipeline descriptor
    def _check_input_settings(self, input_settings: dict=None, location: str=None) -> None:
        """
        Checks `input_settings` with respect to pipeline descriptor. If not provided, checks the instance property.
        Prerequisite: input_settings contains only strings or lists of strings.
        
        `location` refers to the storage infrastructure where input files should be found (e.g., VIP).
        Use the same nomenclature as defined in self._exists() (e.g., `location="vip"`).
        
        Detailed output:
            - Prints warnings if _VERBOSE is True.
            - Raises AttributeError if the input settings or pipeline identifier were not found.
            - Raises TypeError if some input parameter is missing.
            - Raises ValueError if some input value does not the fit with the pipeline definition.
            - Raises FileNotFoundError some input file does not exist. 
            - Raises RuntimeError if communication failed with VIP servers.
        """
        # If location is not provided, default to server
        if location is None:
            location = self._SERVER_NAME
        # If input_settings are not provided, get instance attribute instead
        if not input_settings:
            if self._is_defined("_input_settings"):
                input_settings = self._get_input_settings(location)
            else:
                raise AttributeError("Input settings are missing")
        # Check the pipeline identifier
        if not self._is_defined("_pipeline_id"): 
            raise AttributeError("Input settings could not be checked without a pipeline identifier.")
        # Parameter names
        self._check_input_keys(input_settings)
        # Parameter values
        self._check_input_values(input_settings, location=location)
        # Return True when all checks are complete
        return True
    # ------------------------------------------------      

    # Check the parameter names according to pipeline descriptor
    def _check_input_keys(self, input_settings: dict) -> None:
        """
        Looks for mismatches in keys between `input_settings` and `_pipeline_def`.
        """
        # Check every required field is there 
        missing_fields = (
            # required parameters without a default value
            {
                param["name"] for param in self._pipeline_def['parameters'] 
                if not param["isOptional"] and (param["defaultValue"] == '$input.getDefaultValue()')
            } 
            # current parameters
            - set(input_settings.keys()) 
        )
        # Raise an error if a field is missing
        if missing_fields:
            raise TypeError("Missing input parameter(s) :\n" + ", ".join(missing_fields))
        # Check every input parameter is a valid field
        unknown_fields = (
            set(input_settings.keys()) # current parameters
            - {param["name"] for param in self._pipeline_def['parameters']} # pipeline parameters
        )
        # Display a warning in case of useless inputs
        if unknown_fields :
            self._print("(!) The following input parameters: ['" + "', '".join(unknown_fields) \
             + f"'] are useless for pipeline '{self._pipeline_id}'. This may throw RuntimeError later.")
    # ------------------------------------------------
    
    # Check the parameter values according to pipeline descriptor
    def _check_input_values(self, input_settings: dict, location: str) -> None:
        """
        Checks if each parameter value in `input_settings` matches its pipeline description in `parameters`.
        `location` refers to the storage infrastructure (e.g., VIP) to scan for missing files.

        Prerequisite: input_settings is defined and contains only strings, or lists of strings.
        """
        # Browse the input parameters
        for param in self._pipeline_def['parameters'] :
            # Get parameter name
            name = param['name']
            # Skip irrelevant inputs (this should not happen after self._check_input_keys())
            if name not in input_settings:
                continue
            # Get input value
            value = input_settings[name]
            # `request` will send only strings
            if not self._isinstance(value, str): # This should not happen
                raise ValueError( # Parameter could not be parsed correctly
                    f"Parameter: '{name}' \n\twith value: '{value}' \n\twith type: '{type(value)}')\ncould not be parsed."\
                        +"Please double check the value; if correct, try converting it to `str` in the `input_settings`."
                )
            # Check the input has no empty values
            if not self._is_input_full(value):
                raise ValueError(
                    f"Parameter '{name}' contains an empty value"
                )
            # Check invalid characters for VIP
            invalid = self._invalid_chars_for_vip(value)
            if invalid:
                raise ValueError(
                    f"Parameter '{name}' contains some invalid character(s): {', '.join(invalid)}"
                )
            # If input is a File, check file(s) existence 
            if param["type"] == "File":
                # Ensure every file exists at `location`
                missing_file = self._first_missing_file(value, location)
                if missing_file:
                    raise FileNotFoundError(
                        f"Parameter '{name}': The following file is missing in the {location.upper()} file system:\n\t{missing_file}"
                    )
            # Check other input formats ?
            else: pass # TODO
    # ------------------------------------------------
    
    # Function to look for empty values
    @classmethod
    def _is_input_full(cls, value):
        """
        Returns False if `value` contains an empty string or list.
        """
        if isinstance(value, list) and cls._isinstance(value, str): # Case: list of strings
            return all([(len(v) > 0) for v in value])
        elif isinstance(value, (str, list)): # Case: list or string
            return (len(value) > 0)
        else: # Case: other
            return True
    # ------------------------------------------------

    # Function to assert the input contains only a certain Python type
    @classmethod
    def _isinstance(cls, value, type: type) -> bool: 
        """
        Returns True if `value` is instance of `type` or a list of `type`.
        """
        if isinstance(value, list):
            return all([isinstance(v, type) for v in value])
        else:
            return isinstance(value, type)
    # ------------------------------------------------

    # Function to check invalid characters in some input string
    @classmethod
    def _invalid_chars_for_vip(cls, value) -> list: 
        """
        Returns a list of invalid characters in `value`.
        """
        # Get a set of invalid characters
        if isinstance(value, list):
            characters = {v for val in value for v in cls._INVALID_CHARS_FOR_VIP.findall(str(val))}
        else:
            characters = set(cls._INVALID_CHARS_FOR_VIP.findall(str(value)))
        # Special correction for Windows paths
        if os.name == "nt":
            characters -= {"\\"}
        # Return a sorted list
        return sorted(list(characters))
    # ------------------------------------------------
    
    # Function to assert file existence in the input settings
    @classmethod
    def _first_missing_file(cls, value, location: str) -> str: 
        """
        Returns the path the first non-existent file in `value` (None by default).
        - `value` can contain a single file path or a list of paths.
        - `location` refers to the storage infrastructure (e.g., "vip") to feed in cls._exists().
        """
        # Case : list of files
        if isinstance(value, list):
            for file in value : 
                if cls._first_missing_file(value=file, location=location) is not None:
                    return file
            return None
        # Case: single file
        else:
            return value if not cls._exists(path=value, location=location) else None 
    # ------------------------------------------------

    ########################################
    # SESSION LOGS & USER VIEW
    ########################################

    # Function to clean HTML text when loaded from VIP portal
    @staticmethod
    def _clean_html(text: str) -> str:
        """Returns `text` without html tags and newline characters."""
        return re.sub(r'<[^>]+>|\n', '', text)

    # Interface for printing logs at instance level
    def _print(self, *args, min_space=-1, max_space=1, **kwargs) -> None:
        """
        Prints session logs.
        Behaves as Python built-in `print()` function with two additional conditions:
        1. Does not print anything if `self.verbose` or `self._VERBOSE` is False,
        2. The number of blank lines before and after the log is framed between `min_space` and `max_space`
            (`min_space`=-1 means the log may end without newline).
        """
        # Return if verbose mode is False
        if not self.verbose:
            return
        # Ensure min_space and max_space are correctly ordered
        assert -1 <= min_space <= max_space, f"Wrong min_space ({min_space}) or max_space ({max_space})"
        # Get the message from arguments
        sep = kwargs.pop("sep") if "sep" in kwargs else ' '
        end = kwargs.pop("end") if "end" in kwargs else '\n'
        message = sep.join(map(str, args)) + end
        # Get the number of blank lines at the end of last message
        if not self._is_defined("_blank_lines"):
            self._blank_lines = 0
        # Function to count the number of newlines at the beginning of the message
        def nb_nl(msg: str) -> int:
            n = 0
            for char in msg:
                if char == '\n':  n += 1
                else: break
            return n
        # Function to get the desired number of newlines at the beginning of the message
        def nb_nl_start() -> int:
            # Newlines count
            n_start = nb_nl(message)
            # Lower an upper bounds for newlines count (accounting for self._blanklines)
            lower, upper = min_space - self._blank_lines, max_space - self._blank_lines
            # Return the framed value
            return n_start if (lower <= n_start <= upper) else upper if (n_start > upper) else lower
        # Trim the newlines at the beginning of the message
        message = "\n" * nb_nl_start() + message.lstrip("\n")
        # Case blank message: print now
        if not message.strip("\n"): 
            self._blank_lines += message.count("\n") # Add blank lines to previous count
            print(message, end='', **kwargs) # Print the message with the rest of keywords arguments
            return
        # Function to get the desired number of newlines at the end of the message
        def nb_nl_end() -> int:
            # Newlines count
            n_end = nb_nl(reversed(message))
            # Lower an upper bounds for newlines count 
            lower, upper = min_space + 1, max_space + 1 # `+1` because the first newline is not a blank line
            # Return the framed value
            return n_end if (lower <= n_end <= upper) else upper if (n_end > upper) else lower
        # Reset the blank line count
        self._blank_lines = nb_nl_end() - 1 
        # Trim the newlines a the end of the message
        message = message.rstrip("\n") + "\n" * nb_nl_end()
        # Print the message with the rest of keywords arguments
        self._printc(message, end='', **kwargs)
    # ------------------------------------------------

    # Interface for printing logs at class level
    @classmethod
    def _printc(cls, *args, wrapper:textwrap.TextWrapper=None, **kwargs) -> None:
        """
        Print logs from class methods only when cls._VERBOSE is True.
        Takes the same arguments a Python built-in function `print()',
        with one additional argument:
        - `wrapper` (textwrapper.TextWrapper) : TextWrapper object defining 
            how to wrap the text with TextWrapper method "fill".
        """
        if not cls._VERBOSE:
            return None
        # Get the message from arguments
        sep = kwargs.pop("sep") if "sep" in kwargs else ' '
        end = kwargs.pop("end") if "end" in kwargs else '\n'
        message = sep.join(map(str, args)) + end
        # Wrap the message according to `wrapper`
        if wrapper is not None:
            message = wrapper.fill(text=message)
        # Print the message with the rest of keywords arguments
        print(message, end='', **kwargs)
    # ------------------------------------------------

    ########################################
    # Interpret common API exceptions
    ########################################

    # Function to handle VIP runtime errors and provide interpretation to the user
    @classmethod
    def _handle_vip_error(cls, vip_error: RuntimeError) -> None:
        """
        Rethrows a RuntimeError `vip_error` which occured in the VIP API,
        with interpretation depending on the error code.
        """
        # Enumerate error cases
        message = vip_error.args[0]
        if message.startswith("Error 8002") or message.startswith("Error 8003") \
            or message.startswith("Error 8004"):
            # "Bad credentials"  / "Full authentication required" / "Authentication error"
            interpret = (
                "Unable to communicate with VIP."
                + f"\nRun {cls.__name__}.init() with a valid API key to handshake with VIP servers"
                + f"\n({message})"
            )
        elif message.startswith("Error 8000"):
            #  Probably wrong values were fed in `vip.init_exec()`
            interpret = (
                f"\n\t'{message}'"
                + "\nPlease carefully check that session_name / pipeline_id / input_parameters "
                + "are valid and do not contain any forbidden character"
                + "\nIf this cannot be fixed, contact VIP support ()"
            )
        elif message.startswith("Error 2000") or message.startswith("Error 2001"):
            #  Maximum number of executions
            interpret = (
                f"\n\t'{message}'"
                + "\nPlease wait until current executions are over, "
                + f"or contact VIP support ({cls._VIP_SUPPORT}) to increase this limit"
            )
        else:
            # Unhandled runtime error
            interpret=(
                f"\n\t{message}"
                + f"\nIf this cannot be fixed, contact VIP support ({cls._VIP_SUPPORT})"
            )
        # Display the error message
        raise RuntimeError(interpret) from None
    # ------------------------------------------------

#######################################################

if __name__=="__main__":
    pass