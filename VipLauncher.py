from __future__ import annotations
import json
import os
import re
import time
from pathlib import *

import vip

class VipLauncher():
    """
    Python class to run VIP pipelines on datasets located on VIP servers.

    1 "session" allows to run 1 pipeline with 1 parameter set (any number of runs).
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
    # Verbose state for display
    VERBOSE = True
    # Properties to save / display for this class
    _PROPERTIES = [
        "session_name", 
        "pipeline_id", 
        "vip_output_dir", 
        "input_settings", 
        "workflows"
    ]
    # Default backup location 
    # (set to None to avoid saving and loading backup files)
    _BACKUP_LOCATION = "vip"
    # Default location for VIP inputs/outputs (can be different for subclasses)
    _SERVER_NAME = "vip"
    # Prefix that defines a path from VIP
    _SERVER_PATH_PREFIX = "/vip"
    # Default file name to save session properties 
    _SAVE_FILE = "session_data.json"
    # Vip portal
    _VIP_PORTAL = "https://vip.creatis.insa-lyon.fr/"
    # List of pipelines available to the user
    _AVAILABLE_PIPELINES = []
    # Boolean to lock session properties
    _LOCK_PROPERTIES = True

                    #################
    ################ Main Properties ##################
                    ################# 

    # Session Name
    @property
    def session_name(self) -> str:
        """A name to identify the current Session"""
        return self._session_name if self._is_defined("_session_name") else None
    
    @session_name.setter
    def session_name(self, name: str) -> None:
        # Check type
        if not isinstance(name, str):
            raise TypeError("`session_name` should be a string")
        # Check conflict with instance attributes
        self._check_value("session_name", name)
        # Check the name
        self._check_session_name(name)
        # Assign
        self._session_name = name

    @session_name.deleter
    def session_name(self) -> None:
        del self._session_name
    # ------------------------------------------------

    # Pipeline identifier
    @property
    def pipeline_id(self) -> str:
        """Pipeline identifier for VIP"""
        return self._pipeline_id if self._is_defined("_pipeline_id") else None
    
    @pipeline_id.setter
    def pipeline_id(self, pId: str) -> None:
        # Display
        self._print("New Pipeline ID:", pId, end="")
        # Check type
        if not isinstance(pId, str):
            raise TypeError("`pipeline_id` should be a string")
        # Check for conflict with instance attributes
        self._check_value("pipeline_id", pId)
        # Check the ID (if possible)
        if self._check_pipeline_id(pId):
            self._print("checked")
        # Assign
        self._pipeline_id = pId

    @pipeline_id.deleter
    def pipeline_id(self) -> None:
        del self._pipeline_id
    # ------------------------------------------------

    # Input settings
    @property
    def input_settings(self) -> dict:
        """All parameters needed to run the pipeline 
        Run show_pipeline() for more information"""
        return self._get_input_settings() if self._is_defined("_input_settings") else None
    
    @input_settings.setter
    def input_settings(self, input_settings: dict):
        self._print("New Input Settings -> ", end="")
        # Check type
        if not isinstance(input_settings, dict):
            raise TypeError("`input_settings` should be a dictionary")
        # Parse input settings (old and new)
        new_settings = self._parse_input_settings(input_settings)
        self._print("parsed")
        # Check conflicts with instance attribute
        self._check_value("input_settings", input_settings)
        # Update
        self._input_settings = new_settings

    @input_settings.deleter
    def input_settings(self) -> None:
        del self._input_settings
    # ------------------------------------------------

    # Output directory
    @property
    def vip_output_dir(self) -> str:
        """Path to the VIP directory where pipeline outputs will be stored"""
        return str(self._vip_output_dir) if self._is_defined("_vip_output_dir") else None
    
    @vip_output_dir.setter
    def vip_output_dir(self, new_dir) -> None:
        # Check type
        if not isinstance(new_dir, (str, os.PathLike)):
            raise TypeError("`vip_output_dir` should be a string or os.PathLike object")
        # Check conflict with instance attributes
        self._check_value("vip_output_dir", new_dir)
        # Assign
        self._vip_output_dir = PurePosixPath(new_dir)

    @vip_output_dir.deleter
    def vip_output_dir(self) -> None:
        """Delete the result directory"""
        del self._vip_output_dir
    # ------------------------------------------------

    # Alias for the output directory
    @property
    def output_dir(self) -> str:
        """
        Same as `vip_output_dir`.
        Setting `output_dir` will automatically load backup data if any.
        """
        return self.vip_output_dir
    
    @output_dir.setter
    def output_dir(self, new_dir: str) -> None:
        # Set the VIP output directory
        self.vip_output_dir = new_dir
        # Load backup data from the new output directory
        self._load()

    @output_dir.deleter
    def output_dir(self) -> None:
        del self.vip_output_dir
    # ------------------------------------------------

    # Workflows
    @property
    def workflows(self) -> dict:
        """Workflows inventory"""
        return self._workflows if self._is_defined("_workflows") else None
    
    @workflows.setter
    def workflows(self, workflows: dict) -> None:
        # Check type
        if not isinstance(workflows, dict):
            raise TypeError("`workflows` should be a dictionary")
        # Check conflicts with instance value
        self._check_value("workflows", workflows)
        # Assign
        self._workflows = workflows

    @workflows.deleter
    def workflows(self) -> None:
        del self._workflows
    # ------------------------------------------------

    # Verbose state (not deletable, combined with cls.VERBOSE)
    @property
    def verbose(self) -> bool:
        """
        This session will displays logs if `verbose` is True.
        """
        return self._verbose and self.VERBOSE
    
    @verbose.setter
    def verbose(self, verbose: bool) -> None:
        # Check conflict with class properties
        if verbose and not self.VERBOSE:
            raise ValueError(f"{self.__name__}.VERBOSE must be True to put Session <{self.session_name}> in verbose state.")
        # Set
        self._verbose = verbose
    # -----------------------------------------------

    # Lock Properties to avoid accidental confusion between VIP executions
    @property
    def _lock_properties(self) -> bool:
        """
        Boolean for locking session properties. 
        If True, a property must be deleted before reassignment.
        """
        return self._LOCK_PROPERTIES if not self._is_defined("__lock_properties") else self.__lock_properties
    
    @_lock_properties.setter
    def _lock_properties(self, lock) -> None:
        self.__lock_properties = lock
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
        if not self._is_defined("__pipeline_def"):  
            self.__pipeline_def = self._get_pipeline_def(self._pipeline_id)
        # Return the attribute
        return self.__pipeline_def
    # ------------------------------------------------
    

                    #############
    ################ Constructor ##################
                    #############

    # RAF: 
    # Contrôle des effets de bord
        # backup / verbose class-wise & instance-wise -> Done
    # Gestion de conflits entre paramètres et fichier session -> A tester
        # Variable pour verrouiller les propriétés -> Done 
    # Verbose intégrée à self.print() comme backup intégrée à self.load() -> Done
    # Arguments prennent None en valeur par défaut -> RAF après tests
    # Test pour les 3 classes
        # Vérifier verbose / backup
        # Linux / Windows

    def __init__(
            self, output_dir="", session_name="", pipeline_id="",  
            input_settings:dict={}, verbose=True
        ) -> None:
        """
        Create a VipLauncher instance from keyword arguments. 
        - Displays informations unless `verbose` is False.
        - The session will create backups unless `backup` is False.

        Available keywords:
        - `output_dir` (str | os.PathLike object) Path to the VIP directory where pipeline outputs will be stored 
            (does not need to exist).

        - `session_name` (str) A name to identify this session.
            Default value: 'VipLauncher_[date]-[time]'

        - `pipeline_id` (str) Name of your pipeline in VIP. 
            Usually in format : *application_name*/*version*.

        - `input_settings` (dict) All parameters needed to run the pipeline.
            - Run VipSession.show_pipeline(`pipeline_id`) to display these parameters.
            - The dictionary can contain any object that can be converted to strings, or lists of such objects. 
            - Lists of parameters launch parallel workflows on VIP.
        """
        # Set the verbose state for private methods
        self._verbose = verbose 
        # Set the session name
        self.session_name = (
            session_name if session_name
            # default value
            else self.__name__ + "_" + time.strftime("%y%m%d-%H%M%S", time.localtime())
        )
        # Display the session name
        if any([session_name, output_dir]):
            self._print(f"\n<<< SESSION '{self._session_name}' >>>\n")
        # Set the output directory (/!\ this will load the corresponding backup data if any /!\)
        if output_dir :
            self._print("Output directory:", output_dir)
            self.output_dir = output_dir
        # Set the rest (unlock session properties)
        self._lock_properties = False
        # Pipeline identifier
        if pipeline_id:
            self.pipeline_id = pipeline_id
        # Input settings
        if input_settings:
            self.input_settings = input_settings 
        # Workflows inventory
        if not self.workflows:
            self.workflows = {}
        # Restore default property lock
        self._lock_properties = self._LOCK_PROPERTIES
        # End display if we're in this class
        if any([session_name, output_dir]) and self.__name__ == "VipLauncher": 
            self._print()
    # ------------------------------------------------

                    ################
    ################ Public Methods ##################
                    ################

    #################################################
    # ($A) Manage a session from start to finish
    #################################################

    def _print(self, *args, **kwargs) -> None:
        """
        Behaves as Python built-in `print()` function with two additional conditions:
        1. Does not print anything if `self.verbose is False`
        2. Does not print more than `max_blank` blank lines between several prints, 
            where `max_blank` (default: 2) can be passed as keyword argument.
        """
        # Function to count the number of blank lines at the beginning of a message
        def nb_blank_intro(msg: str) -> int:
            n = 0
            for char in msg:
                if char == '\n':  n += 1
                else: break
            return n
        # Number of blank lines at the end of last message
        if not self._is_defined("_blank_lines"):
            self._blank_lines = 0
        # Get sep and end
        sep = kwargs.pop("sep") if "sep" in kwargs else ' '
        end = kwargs.pop("end") if "end" in kwargs else '\n'
        # Get the maximum number of blank lines
        max_blank = kwargs.pop("max_blank") if "max_blank" in kwargs else 2
        # Get the message
        message = sep.join(map(str, args)) + end
        # Count the blank lines at the beginning of the message
        n_start = nb_blank_intro(message)
        # Trim the number of newlines at the beginning of the message
        message = "\n" * min(n_start, max_blank - self._blank_lines) + message.lstrip("\n")
        # Record the number of newlines at the end of the message
        if not message.strip("\n"): # Blank messaage:
            # Add blank lines to previous count
            self._blank_lines += message.count("\n")
        else: # Regular message : 
            # Count the newlines at the end of the message
            n_end = nb_blank_intro(reversed(message))
            # Trim the number of newlines a the end of the message
            message = message.rstrip("\n") + "\n" * min(n_end, max_blank + 1) # `+1` because the last line is not blank
            # Reset the blank line count
            self._blank_lines = max(n_end-1, 0) 
        # Print the message with the rest of keywords arguments IF self.verbose is True
        if self.verbose:
            print(message, end='', **kwargs)
    # ------------------------------------------------

    def _check_value(self, property: str, new_value) -> None:
        """
        If session properties are locked, raises ValueError if an attempt is made 
        to change `property` with `new_value`.
        """
        # Get current value
        current_value = getattr(self, property)
        # Check conflict
        if (self._lock_properties # Session properties are locked
            and current_value is not None # Property is already set
            and current_value != new_value): # Conflicting values
            self.print()
            raise ValueError(f"'{property}' is already set for session: <{self.session_name}>.")
    # ------------------------------------------------

    # ($A.1) Login to VIP
    @classmethod
    def init(cls, api_key: str, verbose=True, **kwargs) -> VipLauncher:
        """
        Handshakes with VIP using your own `api_key`. 
        If `verbose` is False, any future VipLauncher session will be silenced.
        Returns a VipLauncher instance which properties can be provided as keyword arguments (`kwargs`).

        Input `api_key` can be either:
        A. (unsafe) a string litteral containing your API key, or
        B. (safer) a path to some local file containing your API key, or
        C. (safer) the name of some environment variable containing your API key.

        In cases B or C, the API key will be loaded from the local file or the environment variable.        
        """
        # Update the verbose state for all sessions
        cls.VERBOSE = verbose
        # Check if `api_key` is in a local file or environment variable
        if os.path.exists(api_key): # local file
            with open(api_key, "r") as kfile:
                true_key = kfile.read().strip()
        elif api_key in os.environ: # environment variable
            true_key = os.environ[api_key]
        else: # string litteral
            true_key = api_key
        # Set User API key
        try:
            # setApiKey() may return False
            assert vip.setApiKey(true_key), \
                f"(!) Unable to set the VIP API key: {true_key}.\nPlease check the key or retry later."
        except RuntimeError as vip_error:
            # setApiKey() may throw RuntimeError in case of bad key
            print(f"(!) Unable to set the VIP API key: {true_key}.\n    Original error message:")
            raise vip_error
        except(json.decoder.JSONDecodeError) as json_error:
            # setApiKey() may throw JSONDecodeError in special cases
            print(f"(!) Unable to set the VIP API key: {true_key}.\n    Original error message:")
            raise json_error
        # Update the list of available pipelines
        try:
            cls._get_available_pipelines() # RunTimeError is handled downstream
        except(json.decoder.JSONDecodeError) as json_error:
            # The user still cannot communicate with VIP
            print(f"(!) Unable to communicate with VIP.")
            print(f"    Original error messsage:")
            raise json_error
        if verbose:
            print()
            print("----------------------------------")
            print("| You are communicating with VIP |")
            print("----------------------------------")
            print()
        # Double check user can access pipelines
        if not cls._AVAILABLE_PIPELINES and verbose: 
            print("(!) Your API key does not allow you to execute pipelines on VIP.")
            print(f"    Please join some research group(s) on the Web portal: {cls._VIP_PORTAL}")  
        # Return a VipLauncher instance for method cascading
        return VipLauncher(verbose=(verbose and kwargs), **kwargs)
    # ------------------------------------------------

    # Launch executions on VIP 
    def launch_pipeline(
            self, pipeline_id="", input_settings:dict={}, output_dir="", nb_runs=1, verbose=True
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
        - Set `verbose` to False to run silently.
        
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
        # Update the verbose state for private methods
        self._verbose = verbose
        self._print("\n<<< LAUNCH PIPELINE >>>\n")
        # Parameter checks
        self._print("Parameter checks")
        self._print("----------------")
        # Check & Update the pipeline identifier
        self._print("Pipeline identifier: ", end="")
        if pipeline_id:
            self.pipeline_id = pipeline_id
        if not self._check_pipeline_id():
            raise TypeError("(!) Pipeline identifier could not be checked without call to init().")
        self._print("OK")
        # Update the result directory
        if output_dir: 
            self.vip_output_dir = output_dir
        # Check existence
        if not self._is_defined("_vip_output_dir"):
            raise TypeError("Please provide an output directory for Session: %s" %self._session_name)
        else: self._print("Output directory: ", end="")
        # Ensure the directory exists
        if self._mkdirs(path=self._vip_output_dir, location=self._SERVER_NAME):
            self._print(f"Created on {self._SERVER_NAME.upper()}")
        else:
            self._print("OK")
        # Update the input parameters
        if input_settings:
            self.input_settings = input_settings
        self._print("Input settings: ", end="")
        # Check existence
        if not self._is_defined("_input_settings"):
            raise TypeError("Please provide input parameters for Session: %s" %self._session_name)  
        # Check content
        self._check_input_settings(location=self._SERVER_NAME)
        self._print("OK")
        # End of parameters checks
        self._print("----------------\n")
        # Display the launch
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
        # Display success
        self._print("\n-------------------------------------")
        self._print("Done.")
        # Save the session
        self._save()
        # Return for method cascading
        return self
    # ------------------------------------------------

    # ($A.4) Monitor worflow executions on VIP 
    def monitor_workflows(self, refresh_time=30, verbose=True) -> VipLauncher:
        """
        Updates and displays status for each execution launched in the current session.
        - If an execution is still running, updates status every `refresh_time` (seconds) until all runs are done.
        - Set `verbose` to False to run silently.

        Error profile:
        - Raises RuntimeError if the client fails to communicate with VIP.
        """
        # Update the verbose state for private methods
        self._verbose = verbose
        self._print("\n<<< MONITOR WORKFLOW >>>\n")
        # Check if current session has existing workflows
        if not self._workflows:
            self._print("This session has not launched any execution.")
            self._print("Run launch_pipeline() to launch workflows on VIP.")
            return self
        # Update existing workflows
        self._print("Updating worflow inventory ... ", end="")
        self._update_workflows()
        self._print("Done.")
        # Check if workflows are still running
        if self._still_running():
            # First execution report
            self._execution_report(display=verbose)
            # Display standby
            self._print("\n-------------------------------------------------------------")
            self._print("The current proccess will wait until all executions are over.")
            self._print("Their progress can be monitored on VIP portal:")
            self._print(f"\t{self._VIP_PORTAL}")
            self._print("-------------------------------------------------------------")
            # Standby until all executions are over
            while self._still_running():
                time.sleep(refresh_time)
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
            # End of monitoring time
            # Display the end of executions
            self._print("All executions are over.")
        # Last execution report
        self._execution_report(display=verbose)
        # Save the session
        self._save()
        # Return for method cascading
        return self
    # ------------------------------------------------

    def run_session(
            self, nb_runs=1, refresh_time=30, verbose=True
        ) -> VipLauncher:
        """
        Runs a full session from data on VIP servers:
        1. Launches pipeline executions on VIP;
        2. Monitors pipeline executions until they are all over.

        /!\ This function assumes that all session properties are already set.
        Optional arguments can be provided:
        - Increase `nb_runs` to run more than 1 execution at once;
        - Set `refresh_time` to modify the default refresh time;
        - Set `verbose` to False to run silently.
        """
        # Update the verbose state for private methods
        self._verbose = verbose
        # Run the pipeline
        return (
            # 1. Launch `nb_runs` pipeline executions on VIP
            self.launch_pipeline(nb_runs=nb_runs)
            # 2. Monitor pipeline executions until they are over
            .monitor_workflows(refresh_time=refresh_time)
        )
    # ------------------------------------------------

    # ($A.6) Clean session data on VIP
    def finish(self, timeout=300, verbose=True) -> VipLauncher:
        """
        Removes session's output data from VIP servers. 

        Detailed behaviour:
        - This process checks for actual deletion on VPI servers until `timeout` (seconds) is reached.
            If deletion could not be verified, the procedure ends with a warning message.
        - Workflows status are set to "Removed" when the corresponding outputs have been removed.
        
        Set `verbose` to False to run silently. 
        """
        # Update the verbose state for private methods
        self._verbose = verbose
        # Initial display
        self._print("\n<<< FINISH >>>\n")
        # Check if workflows are still running (without call to VIP)
        if self._still_running():
            # Update the workflow inventory
            self._print("Updating worflow inventory ... ", end="")
            self._update_workflows()
            self._print("Done.")
            # Return is workflows are still running
            if self._still_running():
                self._print("\n(!) This session cannot be finished since the pipeline might still generate data.\n")
                self._execution_report(display=verbose)
                return self
        # Initial display
        self._print("Ending Session:", self._session_name)
        self._print("Removing session data")
        self._print("---------------------")
        # Browse paths to delete
        success = True
        for path, location in self._path_to_delete().items():
            # Display progression
            self._print(f"[{location}] {path} ... ", end="")
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
            self._print(f"{wid}: ", end="")
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
                self._print(f"Session <{self._session_name}> is now over.")
        else:
            self._print("(!) There may still be temporary data on VIP.")
            self._print(f"Please run finish() again or check the following path(s) on the VIP portal ({self._VIP_PORTAL}):")
            self._print('\n\t'.join(self._path_to_delete().keys()))
            # Finish display
            self._print()
        # Return 
        return self
    # ------------------------------------------------

    ###########################################
    # ($B) Additional Features for Advanced Use
    ###########################################

    @classmethod
    def show_pipeline(cls, pipeline_id="") -> None:
        """
        Displays useful informations about VIP pipelines.

        This method can be used to browse among available pipelines, 
        or as a brief guide to build valid `input_settings` for a given pipeline.

        Detailed behaviour:
        - If `pipeline_id` is not provided, shows the list of all available pipelines.
        - If `pipeline_id` is not exact, shows pipelines with a *partial*, *case-insensitive* match.
        - If `pipeline_id` is exact, shows the list of parameters required to run `pipeline_id`.
        """
        # Return if VERBOSE is False
        if not cls.VERBOSE: return
        # Check init() was called first
        if not cls._AVAILABLE_PIPELINES:
            raise TypeError(
                f"No pipeline found. Run {cls.__name__}.init() with a valid API key to access pipeline definitions."
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
            print(f"(!) No pipeline found for pattern '{pipeline_id}'.")
        elif len(pipelines) > 1: # Case multiple matches
            # Print the list of matching pipelines
            print()
            print("Available pipelines")
            print("-------------------")
            print("\n".join(pipelines))
            print("-------------------")
        else: # Case single match
            # Get pipeline_definition
            pipeline_def = cls._get_pipeline_def(pipelines[0])
            # Display name and version
            pipe_str = f"name: {pipeline_def['name']} | version: {pipeline_def['version']}"
            print('-'*len(pipe_str))
            print(pipe_str)
            print('-'*len(pipe_str))
            # Display ID
            print(f"pipeline_id: {pipelines[0]}")
            print('-'*len(pipe_str))
            # Create a description for each "input_setting"
            settings = {}
            for param in pipeline_def["parameters"]:
                # Name
                name = param["name"]
                # Begin description
                description = ""
                # isOptional
                if param["isOptional"]:
                    description += "[Optional]"
                # Type
                description += f"[{param['type']}]"
                # End description
                description += " " + param['description']
                # Append
                settings[name] = cls._clean_html(description)
            # Display input settings
            print("input_settings: ", end="")
            print(json.dumps(settings, indent=2))
            print('-'*len(pipe_str))
            # End the display
            print()
    # ------------------------------------------------

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
                msg += "Please retry later. Contact VIP support (vip-support@creatis.insa-lyon.fr) if this cannot be fixed."
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
        timeout = 300 # max time in seconds
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
        Sets multiple session properties based on keywords arguments.
        Erases previous values.
        Ignores keyword when value is None.
        """
        for property, value in kwargs.items():
            # Ignores property if value is None
            if value is not None:
                # Delete attribute if defined  
                if getattr(self, property) is not None:
                    delattr(self, property)
                # Set attribute
                setattr(self, property, value)
    # ------------------------------------------------

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

    # (A.3) Launch pipeline executions on VIP servers
    ##################################################
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
        try :
            # Get execution infos
            infos = vip.execution_info(workflow_id)
            # Secure way to get execution results
            files = vip.get_exec_results(workflow_id)
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
            "outputs": [
                {
                    key: elem[key] 
                    for key in ["path", "isDirectory", "size", "mimeType"]
                    if key in elem
                }
                for elem in files
            ]
        }
    # ------------------------------------------------

    ##################################################
    # Save / load Session Metadata
    ##################################################

    def _data_to_save(self) -> dict:
        """Returns the data to save as a dictionnary"""
        return self._get(*self._PROPERTIES)
    # ------------------------------------------------

    def _save(self) -> bool:
        """
        Generic method to save session properties.
        - Compares both session data and data from the backup file;
        - Raises ValueError if the session names do not match;
        - Saves backup properties that are not included in the session data;
        - Returns a success flag;
        - Displays information unless `VERBOSE` is False.
        """
        # Return if no-backup mode is activated
        if self._BACKUP_LOCATION is None:
            return False
        # Get session properties
        session_data = self._data_to_save()
        # Get backup data from the output directory
        backup_data = self._load_session(location=self._BACKUP_LOCATION, display=False)
        # If there is no backup data, save immediately
        if backup_data is None:
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

    # Load session properties from metadata
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
        # Case: no backup data
        if backup_data is None:
            return False
        # Get current session properties
        session_data = self._data_to_save()
        # If session properties are undefined, set them immediately
        if session_data["session_name"] is None:
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
        # If differences are found, print a warning and do not load the backup.
        diff = [ prop 
                for prop in session_data 
                    if ((prop not in ["session_name", "workflows"]) 
                    and (backup_data[prop] is not None )
                    and (session_data[prop] is not None )
                    and (session_data[prop] != backup_data[prop])) ]
        if diff:
            self._print(f"(!) The following properties will be overwritten during the next session backup:\n\t{', '.join(diff)}\n")
            return False
        # After all checkpoints are passed, overwrite all instance properties and return True
        self._set(**backup_data)
        return True
    # ------------------------------------------------

    # ($C.1) Save session properties in a JSON file
    def _save_session(self, session_data: dict, location="vip") -> bool:
        """
        Saves dictionary `session_data` to a JSON file, in the output directory at `location`.
        Returns a success flag.
        Displays success / failure unless `VERBOSE` is False.
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
        if done and is_new: self._print(f">> Session was saved in: {vip_file}\n")
        elif done:  self._print(f">> Session saved\n")
        else: self._print(f"\n(!) Session backup failed\n")
        return done
    # ------------------------------------------------

    def _load_session(self, location="vip", display=True) -> dict:
        """
        Loads backup data from the output directory.
        If the backup file could not be read, returns None.
        Otherwise, returns session properties as a dictionary. 
        Displays success / failure unless `display` is False.
        """
        # Thow error if location is unknown
        if location != "vip":
            return NotImplementedError(f"Location '{location}' is unknown for {self.__name__}")
        # Display
        if display:
            self._print(f"Loading session properties ...")
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
        if display:
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

    # ($D.2) Prevent common mistakes in session / pipeline settings 
    ###############################################################

    # Check if an attribute has been correctly defined
    def _is_defined(self, attribute) -> bool :
        """Returns True if `attribute` has already been set, False otherwise."""
        return (attribute in self.__dict__)

    # Check the session name to avoid name errors in VIP
    def _check_session_name(self, name="") -> None:
        """
        Session name characters must be only aphanumeric or hyphens.
        Raises ValueError otherwise.
        """
        # Input
        if not name:
            name = self._session_name
        # Green Flag
        ok_name = True
        # Criterion
        for letter in name:
            ok_name &= letter.isalnum() or (letter in "_- ")
        # Error message
        if not ok_name:
            raise ValueError("Session name must contain only alphanumeric characters, spaces and hyphens: '-', '_'")
    # ------------------------------------------------    

    # Check the pipeline identifier based on the list of available pipelines
    def _check_pipeline_id(self, pipeline_id: str="") -> bool:
        """
        Checks if the pipeline identifier `pipeline_id` is available for this session.
        Raises ValueError otherwise.
        If `pipeline_id` is not provided, checks instance attribute.
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

    # Store the VIP paths as PathLib objects.
    # This is mainly useful for subclasses
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
            # Case: single input, string or path-like
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
        # Function to get a string for each parameter
        def get_input(value) -> str:
            """
            If `value` is a path, returns the corresponding string.
            Value can be a single input or a list of inputs.
            """
            # Case: multiple inputs
            if isinstance(value, list):
                return [ get_input(element) for element in value ]
            # Case : path to file
            elif isinstance(value, PurePath): return str(value)
            # Case: other parameter
            else: return str(value)
        # -- End of get_input() --
        # Raise an error if location cannot be parsed
        if location != "vip":
            raise NotImplementedError(location)
        # Browse input settings
        return {
            key: get_input(value)
            for key, value in self._input_settings.items()
        }
    # ------------------------------------------------

    # Check the input settings based on the pipeline descriptor
    def _check_input_settings(self, input_settings: dict={}, location="") -> None:
        """
        Checks `input_settings` with respect to pipeline descriptor. If not provided, checks the instance property.
        Prerequisite: input_settings contains only strings or lists of strings.
        
        `location` refers to the storage infrastructure where input files should be found (e.g., VIP).
        Use the same nomenclature as defined in self._exists() (e.g., `location="vip"`).
        
        Detailed output:
            - Prints warnings if VERBOSE is True.
            - Raises AttributeError if the input settings or pipeline identifier were not found.
            - Raises TypeError if some input parameter is missing.
            - Raises ValueError if some input value does not the fit with the pipeline definition.
            - Raises FileNotFoundError some input file does not exist. 
            - Raises RuntimeError if communication failed with VIP servers.
        """
        # If location is not provided, default to server
        if not location:
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
            # pipeline parameters
            {param["name"] for param in self._pipeline_def['parameters'] 
                if not param["isOptional"] and (param["defaultValue"] == "$input.getDefaultValue()")} 
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
            # Request will send only strings
            assert self._isinstance(value, str), \
                f"Parameter '{name}' should have been converted to strings ({type(value)} instead)"
            # If input is a File, check file(s) existence 
            if param["type"] == "File":
                # Ensure every file exists at `location`
                missing_file = self._first_missing_file(value, location)
                if missing_file:
                    raise FileNotFoundError(f"(!) The following file is missing in the {location.upper()} file system:\n\t{missing_file}")
            # Check other input formats ?
            else: pass # TODO
    # ------------------------------------------------
        
    # Function to assert the input contains a certain type
    @staticmethod
    def _isinstance(value, type: type) -> bool: 
        """
        Returns True if `value` is instance of `type` or a list of `type`.
        """
        if isinstance(value, list):
            return all([isinstance(v, type) for v in value])
        else:
            return isinstance(value, type)
    # ------------------------------------------------
    
    # Function to assert file existence in the input settings
    @classmethod
    def _first_missing_file(cls, value: str, location: str) -> str: 
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

    # Function to clean HTML text when loaded from VIP portal
    @staticmethod
    def _clean_html(text: str) -> str:
        """Returns `text` without html tags and newline characters."""
        return re.sub(r'<[^>]+>|\n', '', text)

    # ($D.3) Interpret common API exceptions
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
                + f"\nRun {cls.__name__}.init() with a valid API key to handshake with VIP servers."
                + f"\n({message})"
            )
        elif message.startswith("Error 8000"):
            #  Probably wrong values were fed in `vip.init_exec()`
            interpret = (
                f"\n\t'{message}'"
                + "\nPlease carefully check that session_name / pipeline_id / input_parameters "
                + "are valid and do not contain any forbidden character."
                + "\nIf this cannot be fixed, contact VIP support (vip-support@creatis.insa-lyon.fr)."
            )
        elif message.startswith("Error 2000") or message.startswith("Error 2001"):
            #  Maximum number of executions
            interpret = (
                f"\n\t'{message}'"
                + "\nPlease wait until current executions are over, "
                + "or contact VIP support (vip-support@creatis.insa-lyon.fr) to increase this limit."
            )
        else:
            # Unhandled runtime error
            interpret=(
                f"\n\t{message}"
                + "\nIf this cannot be fixed, contact VIP support (vip-support@creatis.insa-lyon.fr)."
            )
        # Display the error message
        raise RuntimeError(interpret) from None
    # ------------------------------------------------

#######################################################

if __name__=="__main__":
    from VipLauncher  import VipLauncher
    sess = VipLauncher()
    sess._print(3*"\n", max_blank=2)