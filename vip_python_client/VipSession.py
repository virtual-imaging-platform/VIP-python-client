from __future__ import annotations
import os
import json
import tarfile
import re
from pathlib import *

import src.vip as vip
from src.VipLauncher import VipLauncher

class VipSession(VipLauncher):
    """
    Python class to run VIP pipelines on local datasets.

    A single instance allows to run 1 pipeline on 1 dataset with 1 parameter set (any number of runs).
    Pipeline runs need at least three inputs:
    - `input_dir` (str | os.PathLike) Path to the local dataset.
    - `pipeline_id` (str) Name of the pipeline. 
    - `input_settings` (dict) All parameters required to run the pipeline.

    N.B.: all instance methods require that `VipSession.init()` has been called with a valid API key. 
    See GitHub documentation to get your own VIP API key.
    """

                    ##################
    ################ Class Attributes ##################
                    ##################

    # --- Overriden from the parent class ---

    # Class name
    __name__ = "VipSession"
    # Properties to save / display for this class
    _PROPERTIES = [
        "session_name", 
        "pipeline_id",
        "local_input_dir",
        "local_output_dir", 
        "vip_input_dir",
        "vip_output_dir",
        "input_settings", 
        "workflows"
    ]
    # Default backup behaviour 
    _BACKUP_LOCATION = "local"

    # --- New Attributes ---

    # Default path to upload and download data on VIP servers
    _SERVER_DEFAULT_PATH = PurePosixPath("/vip/Home/API/")
    # Default path to save session outputs on the current machine
    _LOCAL_DEFAULT_PATH = Path("./vip_outputs")

                    #################
    ################ Main Properties ##################
                    ################# 

    # --- Overriden from the parent class ---

    # Interface `output_dir` refers to the *local* output directory
    @property
    def output_dir(self) -> str:
        """
        Safe interface for `local_output_dir`.
        Setting `output_dir` will automatically load backup data if any.
        """
        return self.local_output_dir
    
    @output_dir.setter
    def output_dir(self, new_dir: str) -> None:
        # Display 
        self._print("Output directory:", new_dir)
        # Set the new output directory
        self.local_output_dir = new_dir
        # Load backup data from the new output directory
        self._load()

    @output_dir.deleter
    def output_dir(self) -> None:
        del self.local_output_dir
    # ------------------------------------------------

    # --- New Properties ---

    # Local output directory (contains backup data)
    @property
    def local_output_dir(self) -> str:
        """Local path to the output data"""
        # Return None if the private attribute is unset
        return str(self._local_output_dir) if self._is_defined("_local_output_dir") else None
    
    @local_output_dir.setter
    def local_output_dir(self, new_dir) -> None:
        # Call deleter if agument is None
        if new_dir is None: 
            del self.local_output_dir
            return
        # Check type
        if not isinstance(new_dir, (str, os.PathLike)):
            raise TypeError("Property `local_output_dir` should be a string or os.PathLike object")
        # Path-ify to account for relative paths
        new_path = Path(new_dir)
        # Check conflicts with private attribute
        self._check_value("_local_output_dir", new_path)
        # Set
        self._local_output_dir = new_path

    @local_output_dir.deleter
    def local_output_dir(self) -> None:
        # Delete only if the private attribute is defined
        if self._is_defined("_local_input_dir"): 
            del self._local_output_dir
    # ------------------------------------------------

    # Local input directory
    @property
    def local_input_dir(self):
        """Local path to the input data"""
        # Return None if the private attribute is unset
        return str(self._local_input_dir) if self._is_defined("_local_input_dir") else None
    
    @local_input_dir.setter
    def local_input_dir(self, new_dir) -> None:
        # Call deleter if agument is None
        if new_dir is None: 
            del self.local_input_dir
            return
        # Check type
        if not isinstance(new_dir, (str, os.PathLike)):
            raise TypeError("`local_input_dir` should be a string or os.PathLike object")
        # Path-ify to account for relative paths
        new_path = Path(new_dir)
        # Check conflicts with private attribute
        self._check_value("_local_input_dir", new_path)
        # Set
        self._local_input_dir = new_path
        # Update the `input_settings` with this new input directory
        self._update_input_settings()

    @local_input_dir.deleter
    def local_input_dir(self) -> None:
        # Delete only if the private attribute is defined
        if self._is_defined("_local_input_dir"): 
            del self._local_input_dir
    # ------------------------------------------------

    # Interface for the local input directory
    @property
    def input_dir(self) -> str:
        """Safe interface for `local_input_dir`"""
        return self.local_input_dir
    
    @input_dir.setter
    def input_dir(self, new_dir: str) -> None:
        # Display
        self._print("Input Directory: '%s'" %new_dir, end="")
        # Set
        self.local_input_dir = new_dir
        # Resolve the path if possible
        if self._exists(self._local_input_dir, "local"):
            self._print(" --> checked")
        else:
            self._print(f"\n(!) `input_dir` does not exist in the local file system. This may throw an error later.")

    @input_dir.deleter
    def input_dir(self) -> None:
        del self.local_input_dir
    # ------------------------------------------------

    # Input directory on VIP
    @property
    def vip_input_dir(self) -> str:
        """VIP path to the input data"""
        # Return None if the private attribute is unset
        return str(self._vip_input_dir) if self._is_defined("_vip_input_dir") else None

    @vip_input_dir.setter
    def vip_input_dir(self, new_dir) -> None:
        # Call deleter if agument is None
        if new_dir is None: 
            del self.vip_input_dir
            return
        # Check type
        if not isinstance(new_dir, (str, os.PathLike)):
            raise TypeError("Property `vip_input_dir` should be a string or os.PathLike object")
        # Path-ify
        new_path = PurePosixPath(new_dir)
        # Check if the path contains invalid characters for VIP
        invalid = self._invalid_chars_for_vip(new_path)
        if invalid:
            raise ValueError(
                f"VIP output directory contains some invalid character(s): {', '.join(invalid)}"
            )
        # Check conflicts with private attribute
        self._check_value("_vip_input_dir", new_path)
        # Set
        self._vip_input_dir = new_path
        # Update the `input_settings` with this new input directory
        self._update_input_settings()

    @vip_input_dir.deleter
    def vip_input_dir(self) -> None:
        # Delete only if the private attribute is defined
        if self._is_defined("_vip_input_dir"): 
            del self._vip_input_dir
    # ------------------------------------------------
    
    # VIP path to all session data (read only)
    @property
    def _vip_dir(self) -> str:
        """Default VIP path containing all session data"""
        return self._SERVER_DEFAULT_PATH / self._session_name
    # ------------------------------------------------

                    #############
    ################ Constructor ##################
                    #############
    def __init__(
            self, session_name: str=None,  input_dir=None, pipeline_id: str=None,  
            input_settings: dict=None, output_dir=None, verbose: bool=None
        ) -> None:
        """
        Create a VipSession instance and sets its properties from keyword arguments.
        
        ## Parameters
        - `session_name` [Recommended] (str) A name to identify this session.
            - Default value: 'VipSession-[date]-[time]-[id]'
            
        - `input_dir` (str | os.PathLike) Local path to your full dataset.
            - This directory must be uploaded on VIP servers before pipeline runs.

        - `pipeline_id` (str) Name of your pipeline in VIP. 
            - Usually in format : *application_name*/*version*.
            - Run VipSession.show_pipeline() to display available pipelines.

        - `input_settings` (dict) All parameters needed to run the pipeline.
            - Run VipSession.show_pipeline(`pipeline_id`) to display these parameters.
            - The dictionary can contain any object that can be converted to strings, or lists of such objects.
            - Lists of parameters launch parallel workflows on VIP.

        - `output_dir` [Optional] (str | os.PathLike) Local path to the directory where: 
            - session properties will be saved; 
            - pipeline outputs will be downloaded from VIP servers.
            - *Default value*: './vip_outputs/[`session_name`]'

        - `verbose` [Optional] (bool) Verbose mode for this instance.
            - If True, instance methods will display logs;
            - If False, instance methods will run silently.
        
        `session_name` and `output_dir` are only set at instantiation; other properties can be set later in function calls.
        If `session_name` or `output_dir` refer to a saved session, properties will be loaded from the backup file.
        """
        # Default values for the session name output directory and verbose state
        if not session_name:
            session_name = self._new_session_name()
        if not output_dir:
            output_dir = self._LOCAL_DEFAULT_PATH / session_name
        if verbose is None:
            verbose = self._VERBOSE
        # Initiate parameters from the parent class
        super().__init__(
            output_dir = output_dir,
            session_name = session_name,
            pipeline_id = pipeline_id,
            input_settings = input_settings,
            verbose = verbose and any([output_dir, session_name, pipeline_id, input_settings])
        )
        # Reset the verbose state
        self.verbose = verbose
        # Set the VIP input directory to default if still unset
        if not self.vip_input_dir:
            self.vip_input_dir = self._vip_dir / "INPUTS"
        # Set the VIP output directory to default if still unset
        if not self.vip_output_dir:
            self.vip_output_dir = self._vip_dir / "OUTPUTS"
        # Unlock session properties
        with self._unlocked_properties():
            # Set the local input directory
            if input_dir:
                self.input_dir = input_dir
        # End display if we're in this class
        if any([session_name, output_dir]) and (self.__name__ == "VipSession"): 
            self._print()
    # ------------------------------------------------

                    ################
    ################ Public Methods ##################
                    ################

    #################################################
    # Manage a session from start to finish
    #################################################

    # Overwrite VipLauncher.init() to be compatible with new kwargs
    @classmethod
    def init(cls, api_key="VIP_API_KEY", verbose=True, **kwargs) -> VipSession:
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
        return super().init(api_key=api_key, verbose=verbose, **kwargs)
    # ------------------------------------------------
   
    # Upload a dataset on VIP servers
    def upload_inputs(self, input_dir=None, update_files=True) -> VipSession:
        """
        Uploads a local dataset to VIP servers.
        - `input_dir` (str | os.PathLike): local directory containing the dataset. 
            If not provided, `self.input_dir` is be used.
        - If `update_files` (bool) is True, the input directory on VIP will be checked in depth for missing files.

        Error profile:
        - Raises TypeError is `input_dir` is missing and was not declared at instanciation;
        - Raises ValueError if `input_dir` conflicts with session properties;
        - Raises FilenotFoundError if `input_dir` could not be found on this machine;
        - Raises RuntimeError if the client fails to communicate with VIP;

        Session is backed up at the end of the procedure.
        """
        # First Display
        self._print("\n=== UPLOAD INPUTS ===\n")
        # Check the distant (VIP) input directory        
        try: 
            # Check connection with VIP 
            exists = self._exists(self._vip_input_dir, location="vip")
        except RuntimeError as vip_error:
            self._handle_vip_error(vip_error)
        # Return if `update_files` is False and input data are already on VIP
        if exists and not update_files:
            self._print("Skipped : There are already input data on VIP.")
            # Return 
            return self
        # Set local input directory
        if input_dir:
            self.input_dir = input_dir
        elif not self._is_defined("_local_input_dir"): 
            raise TypeError(f"Session '{self._session_name}': Please provide an input directory.")
        # Check local input directory
        if not self._exists(self._local_input_dir, location="local"): 
            raise FileNotFoundError(f"Session '{self._session_name}': Input directory does not exist.")
        # Check the local values of `input_settings` before uploading
        if self._is_defined("_input_settings"):
            self._print("Checking references to the dataset within Input Settings ... ", end="", flush=True)
            try: 
                self._check_input_settings(location="local")
                self._print("OK.")
            except FileNotFoundError as fe:
                raise fe from None
            except AttributeError:
                self._print("Skipped (missing properties).")
            except(TypeError, ValueError, RuntimeError) as e:
                self._print("\n(!) The following exception was raised:\n\t", e)
                self._print("    This may throw an error later")
        # Initial display
        self._print(min_space=1, max_space=1)
        self._print("Uploading the dataset on VIP")
        self._print("----------------------------")
        # Upload the input repository
        try:
            failures = self._upload_dir(self._local_input_dir, self._vip_input_dir)
            # Display report
            self._print("-----------------------------")
            if not failures :
                self._print( "Everything is on VIP.")
            else: 
                self._print("End of the process.") 
                self._print( "The following files could not be uploaded on VIP:\n\t")
                self._print( "\n\t".join(failures))
        except Exception as e:
            # An unexpected error occurred
            self._print("-----------------------------")
            self._print("\n(!) Upload was stopped following an unexpected error.")
            raise e from None
        finally:
            # In any case, save session properties
            self._save()
        # Return for method cascading
        return self
    # ------------------------------------------------

    # Launch executions on VIP 
    def launch_pipeline(
            self, pipeline_id: str=None, input_settings: dict=None, nb_runs=1
        ) -> VipSession:
        """
        Launches pipeline executions on VIP.

        Input parameters :
        - `pipeline_id` (str) Name of your pipeline in VIP. 
            Usually in format : *application_name*/*version*.
        - `input_settings` (dict) All parameters needed to run the pipeline.
            - Run VipSession.show_pipeline(`pipeline_id`) to display these parameters.
            - The dictionary can contain any object that can be converted to strings, or lists of such objects.
            - Lists of parameters launch parallel workflows on VIP.
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
        
        Session is backed up at the end of the procedure.
        """
        return super().launch_pipeline(
            pipeline_id = pipeline_id, # default
            input_settings = input_settings, # default
            output_dir = self.vip_output_dir, # VIP output directory
            nb_runs = nb_runs, # default
        )
    # ------------------------------------------------

    # Monitor worflow executions on VIP 
    def monitor_workflows(self, refresh_time=30) -> VipSession:
        """
        Updates and displays the status for each execution launched in the current session.
        - If an execution is still running, updates status every `refresh_time` (seconds) until all runs are finished.
        - Displays a full report when all executions are done.

        Session is backed up at the end of the procedure.
        """
        return super().monitor_workflows(refresh_time=refresh_time)
    # ------------------------------------------------

    # Download execution outputs from VIP servers 
    def download_outputs(self, unzip=True, get_status=["Finished"]) -> VipSession:
        """
        Downloads all session outputs from VIP servers.
        - If `unzip` is True, extracts the data if any output is a .tar file.
        - Outputs from unfinished worflows can be downloaded by modifying `get_status`
        """
        # First display
        self._print("\n=== DOWNLOAD OUTPUTS ===\n")
        # Check if current session has existing workflows
        if not self._workflows:
            self._print("This session has not yet launched any execution.")
            self._print("Run launch_pipeline() to launch workflows on VIP.")
            return self
        # Update the worflow inventory
        self._print("Updating workflow status ... ", end="", flush=True)
        self._update_workflows()
        self._print("Done.\n")
        # Initial display
        self._print("Downloading pipeline outputs to:", self._local_output_dir)
        self._print("--------------------------------")
        # Get execution report
        report = self._execution_report(display=False)
        # Count the number of executions to process
        nb_exec = len(report['Removed']) if "Removed" in report else 0
        assert 'Removed' not in get_status, "Cannot download removed data."
        for status in get_status:
            nb_exec += len(report[status]) if status in report else 0
        nExec=0
        # Browse workflows with removed data and check if files are missing
        if "Removed" in report :
            for wid in report["Removed"]:
                nExec+=1
                # Display current execution
                self._print(f"[{nExec}/{nb_exec}] Outputs from:", wid, "-> REMOVED from VIP servers")
                # Get the path of the returned files on VIP
                vip_outputs = self._workflows[wid]["outputs"]
                # If there is no output file, go to the next execution
                if not vip_outputs: 
                    self._print("\tNothing to download.")
                    continue
                # Browse the output files to check if they have already been downloaded
                missing_file = False
                for output in vip_outputs:
                    # Get the output path on VIP
                    vip_file = PurePosixPath(output["path"])
                    # Get the local equivalent path
                    local_file = self._get_local_output_path(vip_file)
                    # Check file existence on the local machine
                    if not local_file.exists(): 
                        missing_file = True
                # After checking all files, update the display
                if not missing_file: 
                    self._print("\tOutput files are already in:", local_file.parent)
                else: 
                    self._print("(!)\tCannot download the missing files.")
        # Check if any workflow with the desired status is available
        if not any([status in report for status in get_status]):
            self._print("--------------------------------")
            self._print("Nothing to download for the current session.") 
            self._print("Run monitor_workflows() for more information.") 
            return self
        # Download each output file for each execution and keep track of failed downloads
        failures = []
        for wid in self._workflows:
            # Check if the workflow should be processed
            if self._workflows[wid]["status"] not in get_status:
                continue
            nExec+=1 
            # Display current execution
            self._print(f"[{nExec}/{nb_exec}] Outputs from: ", wid, 
                " | Started on: ", self._workflows[wid]["start"],
                " | Status: ", self._workflows[wid]["status"], sep='')
            # Get the path of the returned files on VIP
            vip_outputs = self._workflows[wid]["outputs"]
            # If there is no output file, go to the next execution
            if not vip_outputs: 
                self._print("\tNothing to download.")
                continue
            # Browse the output files
            nFile = 0 # File count
            missing_file = False # Will be True if local files are missing
            for output in vip_outputs:
                nFile+=1
                # Get the output path on VIP
                vip_file = PurePosixPath(output["path"])
                # TODO: implement the case in which the output is a directory (mirror _upload_dir ?)
                if output["isDirectory"]:
                    raise NotImplementedError(f"{vip_file} is a directory: cannot be handled for now.")
                # Get the local equivalent path
                local_file = self._get_local_output_path(vip_file)
                # Check file existence on the local machine
                if self._exists(local_file, "local"): 
                    continue
                # If not, update the output data
                missing_file = True
                # Make the parent directory (if needed)
                local_dir = local_file.parent
                if self._mkdirs(local_dir, location= "local"): self._print("\tNew directory:", local_dir)
                # Get the file size in Megabytes
                try: 
                    size = f"{output['size']/(1<<20):,.1f}MB"
                except:
                    size = "size unknown"
                # Display the process
                self._print(f"\t[{nFile}/{len(vip_outputs)}] Downloading file ({size}):", 
                                local_file.name, end=" ... ")
                # Download the file from VIP servers
                if self._download_file(vip_path=vip_file, local_path=local_file):
                    # Display success
                    self._print("Done.")
                    # If the output is a tarball, extract the files and delete the tarball
                    if unzip and output["mimeType"]=="application/gzip" and tarfile.is_tarfile(local_file):
                        self._print("\t\tExtracting archive content ...", end=" ")
                        if self._extract_tarball(local_file):
                            self._print("Done.") # Display success
                        else:
                            self._print("Extraction failed.") # Display failure
                else: # failure while downloading the output file
                    # Update display
                    self._print(f"\n(!)\tSomething went wrong in the process. Please retry later.")
                    # Update missing files
                    failures.append(str(vip_file))
            # End of file loop
            if not missing_file: # All files were already there
                self._print("\tAlready in:", local_file.parent) 
            else:  # Some missing files were succesfully downloaded
                self._print("\tDone for all files.")
        # End of worflow loop    
        self._print("--------------------------------")
        if not failures :
            self._print("Done for all executions.")
        else:
            self._print("End of the procedure.") 
            self._print("The following files could not be downloaded from VIP", end="\n\t")
            self._print("\n\t".join(failures))
        self._print()
        # Return
        return self
    # ------------------------------------------------

    # Run a full VIP session 
    def run_session(
            self, update_files=True, nb_runs=1, refresh_time=30, 
            unzip=True, get_status=["Finished"]
        ) -> VipSession:
        """
        Runs a full session without the finish() step.
        1. Uploads the database on VIP or check the uploaded files;
        2. Launches pipeline executions on VIP;
        3. Monitors pipeline executions until they are all over;
        4. Downloads execution results from VIP.

        /!\ This method assumes that all session properties are already set.
        Optional arguments can still be provided:
        - Set `update_files` to False to avoid checking the input data on VIP;
        - Increase `nb_runs` to run more than 1 execution at once;
        - Set `refresh_time` to modify the default monitoring time;
        - Set `get_status` to download files from workflows with a specific status
        - Set unzip to False to avoid extracting .tgz files during the download. 
        """
        # Upload-run-download procedure
        return (
            # 1. Upload the database on VIP or check the uploaded files
            self.upload_inputs(update_files=update_files)
            # 2. Launche `nb_runs` pipeline executions on VIP
            .launch_pipeline(nb_runs=nb_runs)
            # 3. Monitor pipeline executions until they are all over
            .monitor_workflows(refresh_time=refresh_time)
            # 4. Download execution results from VIP
            .download_outputs(get_status=get_status, unzip=unzip)
        )

    # Clean session data on VIP
    def finish(self, timeout=300) -> VipSession:
        """
        Removes session's data from VIP servers (INPUTS and OUTPUTS). 
        The downloaded outputs and the input dataset are kept on the local machine.

        Detailed behaviour:
        - This process checks for actual deletion on VIP servers until `timeout` (seconds) is reached.
            If deletion could not be verified, the procedure ends with a warning message.
        - Workflows status are set to "Removed" when the corresponding outputs have been removed from VIP servers.
        """
        # Finish the session based on self._path_to_delete()
        super().finish(timeout=timeout)
        # Check if the input data have been erased (this is not the case when get_inputs have been used)
        if (self._vip_input_dir != self._vip_dir / "INPUTS"
                and self._exists(self._vip_input_dir, location="vip")):
            self._print(f"(!) The input data are still on VIP:\n\t{self.vip_input_dir}")
            self._print( "    They belong to another session.")
            self._print( "    Please run finish() from the original session or remove them manually on the VIP portal:")
            self._print(f"\t{self._VIP_PORTAL}")
        # Save the session
        self._save()    
        # Return
        return self
    # ------------------------------------------------

    ###########################################
    # Additional Features
    ###########################################

    # Display session properties in their current state
    def display(self) -> VipSession:
        """
        Displays useful properties in JSON format.
        - `session_name` : current session name
        - `pipeline_id`: pipeline identifier
        - `input_dir`: path to the input data *on your local machine*
        - `output_dir`: path to pipeline outputs *on your local machine*
        - `vip_input_dir`: path to the input data *in your VIP Home directory*
        - `vip_output_dir` : path to the pipeline outputs *in your VIP Home directory*
        - `input_settings` : input parameters sent to VIP (file locations are bound to `vip_input_dir`).
        - `workflows`: workflow inventory, identifying all pipeline runs in this session.
        """
        # Return for method cascading
        return super().display()
    # ------------------------------------------------

    # Get inputs from another session to avoid multiple uploads
    def get_inputs(self, session: VipSession, get_pipeline=False, get_settings=False) -> VipSession:
        """
        Binds the current session to the inputs of another (`session`), to avoid re-uploading the same dataset on VIP servers.
        
        This method can be used to efficiently run different *pipeline_id* or *input_settings* on the same dataset.
        One session is used to 

        Detailed behaviour and inputs:
        - Current session will point to `session`'s input directories locally and on VIP 
            (i.e, `session.local_input_dir` and `session.vip_input_dir`);
        - If `get_pipeline` is True, the current *pipeline_id* is also synchronized with `session`;
        - If `get_settings` is True, the current *input_settings* are also synchronized with `session`.

        Error profile:
        - Raises FileExistsError if the current session has temporary data on VIP ;
        - Raises FileNotFoundError if the other `session` do not have input data on VIP.
        """
        # End the procedure if both sessions already share the same inputs
        if self._vip_input_dir == session._vip_input_dir:
            # Display
            self._print(
                f"\nSessions '{self._session_name}' and '{session._session_name}' already share the same inputs on VIP.\n",
                )
            # Return for method cascading
            return self
        # Check if current session do not have data on VIP
        if self._exists(self._vip_dir, location="vip"):
            msg = f"Session '{self._session_name}' has temporary data on VIP.\n"
            msg += "Please finish this session or start another one."
            raise FileExistsError(msg)
        # Check if the data actually exist on VIP
        if not self._exists(session._vip_input_dir, location="vip"):
            raise FileNotFoundError(f"Input data for session '{session._session_name}' do not exist on VIP.")
        # Modify session properties
        with self._unlocked_properties():
            # Get the VIP inputs from the other session
            self.local_input_dir = session.local_input_dir # Local data
            self.vip_input_dir = session.vip_input_dir # Distant data 
            # Get the pipeline identifier from the other session
            if get_pipeline:
                self.pipeline_id = session.pipeline_id
            # Get the input settings from the other session
            if get_settings:
                self.input_settings = session.input_settings
        # Display success
        self._print(f"\n<< Session '{self._session_name}' now shares its inputs "\
            + f"with session <{session._session_name}>\n", )
        # Save new properties
        self._save()
        # Return for method cascading
        return self
    # -----------------------------------------------

                    #################
    ################ Private Methods ################
                    #################

    ###################################################################
    # Methods that must be overwritten to adapt VipLauncher methods to
    # new location: "local"
    ###################################################################

    # Path to delete during session finish()
    def _path_to_delete(self) -> dict:
        """Returns the folders to delete during session finish, with appropriate location."""
        return {
            self._vip_dir: "vip"
        }

    # Method to check existence of a distant or local resource.
    @classmethod
    def _exists(cls, path: PurePath, location="local") -> bool:
        """
        Checks existence of a distant (`location`="vip") or local (`location`="local") resource.
        `path` can be a string or path-like object.
        """
        # Check path existence in `location`
        if location=="local":
            return os.path.exists(path)
        else: 
            return super()._exists(path=path, location=location)
    # ------------------------------------------------
    
    # Method to create a distant or local directory
    @classmethod
    def _create_dir(cls, path: PurePath, location="local", **kwargs) -> None:
        """
        Creates a directory at `path` :
        - locally if `location` is "local";
        - on VIP if `location` is "vip".

        `kwargs` are passed as keyword arguments to `Path.mkdir()`.
        Returns the VIP or local path of the newly created folder.
        """
        if location == "local": 
            # Check input type
            path=Path(path)
            # Check the parent is a directory
            assert path.parent.is_dir(),\
                f"Cannot create subdirectories in '{path.parent}': not a folder"
            # Create the new directory with additional keyword arguments
            path.mkdir(**kwargs)
        else: 
            return super()._create_dir(path=path, location=location, **kwargs)
    # ------------------------------------------------

    #################################################
    # Upload (/download) data on (/from) VIP Servers
    #################################################

    # Function to upload all files from a local directory
    def _upload_dir(self, local_path: Path, vip_path: PurePosixPath) -> list:
        """
        Uploads all files in `local_path` to `vip_path` (if needed).
        Displays what it does if `self._verbose` is True.
        Returns a list of files which failed to be uploaded on VIP.
        """
        # Scan the local directory
        assert self._exists(local_path, location='local'), f"{local_path} does not exist."
        # First display
        self._print(f"Cloning: {local_path} ", end="... ")
        # Scan the distant directory and look for files to upload
        if self._mkdirs(vip_path, location="vip"):
            # The distant directory did not exist before call
            # -> upload all the data (no scan to save time)
            files_to_upload = [
                elem for elem in local_path.iterdir()
                if elem.is_file()
            ]
            self._print("(Created on VIP)")
            if files_to_upload:
                self._print(f"\t{len(files_to_upload)} files to upload.")
        else: # The distant directory already exists
            # Scan it to check if there are more files to upload
            vip_filenames = {
                PurePosixPath(element["path"]).name
                for element in vip.list_elements(str(vip_path))
            }
            # Get the files to upload
            files_to_upload = [
                elem for elem in local_path.iterdir()
                if elem.is_file() and (elem.name not in vip_filenames)
            ]
            # Update the display
            if files_to_upload: 
                self._print(f"\n\tVIP clone already exists and will be updated with {len(files_to_upload)} files.")
            else:
                self._print("Already on VIP.")
        # Upload the files
        nFile = 0
        failures = []
        for local_file in files_to_upload :
            nFile+=1
            # Get the file size (if possible)
            try: size = f"{local_file.stat().st_size/(1<<20):,.1f}MB"
            except: size = "unknown size"
            # Display the current file
            self._print(f"\t[{nFile}/{len(files_to_upload)}] Uploading file: {local_file.name} ({size}) ...", end=" ")
            # Upload the file on VIP
            vip_file = vip_path/local_file.name # file path on VIP
            if self._upload_file(local_path=local_file, vip_path=vip_file):
                # Upload was successful
                self._print("Done.")
            else:
                # Update display
                self._print(f"\n(!) Something went wrong during the upload.")
                # Update missing files
                failures.append(str(local_file))
        # Look for sub-directories
        subdirs = [
            elem for elem in local_path.iterdir() 
            if elem.is_dir()
        ]
        # Recurse this function over sub-directories
        for subdir in subdirs:
            failures += self._upload_dir(
                local_path=subdir,
                vip_path=vip_path/subdir.name
            )
        # Return the list of failures
        return failures
    # ------------------------------------------------

    # Function to upload a single file on VIP
    @classmethod
    def _upload_file(cls, local_path: Path, vip_path: PurePosixPath) -> bool:
        """
        Uploads a single file in `local_path` to `vip_path`.
        Returns a success flag.
        """
        # Check
        assert local_path.exists(), f"{local_path} does not exist."
        # Upload
        done = vip.upload(str(local_path), str(vip_path))
        # Return
        return done
    # ------------------------------------------------   

    # Function to download a single file from VIP
    @classmethod
    def _download_file(cls, vip_path: PurePosixPath, local_path: Path) -> bool:
        """
        Downloads a single file in `vip_path` to `local_path`.
        Returns a success flag.
        """
        # Download (file existence is not checked to save time)
        return vip.download(str(vip_path), str(local_path))
    # ------------------------------------------------    

    # Method to extract content from a tarball
    @classmethod
    def _extract_tarball(cls, local_file: Path):
        """
        Replaces tarball `local_file` by a directory with the same name 
        and extracted content.
        Returns success flag.
        """
        # Rename current archive
        archive = local_file.parent / "tmp.tgz"
        os.rename(local_file, archive) # pathlib version does not work it in Python 3.7
        # Create a new directory to store archive content
        cls._mkdirs(local_file, location="local")
        # Extract archive content
        try:
            with tarfile.open(archive) as tgz:
                tgz.extractall(path=local_file)
            success = True
        except:
            success = False
        # Deal with the temporary archive
        if success:
            # Remove the archive
            os.remove(archive)
        else:
            # Rename the archive
            os.rename(archive, local_file)
        # Return the flag
        return success
    # ------------------------------------------------
    
    ###################################
    # Backup / Resume Session Data 
    ###################################

    # Save session properties TO a JSON file
    def _save_session(self, session_data: dict, location="local") -> bool:
        """
        Saves dictionary `session_data` to a JSON file in the LOCAL output directory.
        Returns a success flag.
        """
        # Call parent class if location is unknown
        if location != "local":
            return super()._save_session(session_data=session_data, location=location)
        # Return if the local input directory is not defined
        if not self._is_defined("_local_output_dir"):
            return False
        # Default location
        file = self._local_output_dir / self._SAVE_FILE
        # Make the output directory if it does not exist
        is_new = self._mkdirs(file.parent, location="local")
        # Save the data in JSON format
        with file.open("w") as outfile:
            json.dump(session_data, outfile, indent=4)
        # Display
        self._print()
        if is_new: self._print(f">> Session was saved in: {file}\n")
        else: self._print(f">> Session saved\n")
        return True
    # ------------------------------------------------

    # Load session properties from a JSON file
    def _load_session(self, location="local") -> dict:
        """
        Loads backup data from the LOCAL output directory.
        If the backup file could not be read, returns None.
        Otherwise, returns session properties as a dictionary.
        """
        # Call parent class if location is unknown
        if location != "local":
            return super()._load_session(location=location)
        # Return if the local input directory is not defined
        if not self._is_defined("_local_output_dir"):
            return None
        # Check existence of data from a previous session
        file = self._local_output_dir / self._SAVE_FILE
        if not file.is_file():
            return None
        # Load the JSON file
        with file.open() as fid:
            session_data = json.load(fid)
        # Update the local output directory
        session_data["local_output_dir"] = self.local_output_dir
        # Display success & return
        self._print("<< Session restored from its output directory\n")
        return session_data
    # ------------------------------------------------

    ###########################################################################
    # Hide VIP paths to the user and allow multi-OS use (Unix, Windows)
    ###########################################################################

    # Write the VIP and local paths relatively to the input directories.
    # This enables portability between sessions and terminals.
    def _parse_input_settings(self, input_settings) -> dict:
        """
        Parses the input settings, i.e.:
        - Converts all input paths (local or VIP) to PathLib objects 
            and write them relatively to their input directory. For example:
            '/vip/Home/API/INPUTS/my_signals/signal001' becomes: 'my_signals/signal001'
        - Leaves the other parameters untouched.
        """
        # Function to convert local / VIP paths to relative paths
        def parse_value(input):
            """
            When possible, writes `input` relatively to the input directories (local or VIP), *if possible*.
            `input` can be a single string / os.PathLike object or a list of both types.
            """
            # Case: multiple inputs
            if isinstance(input, list):
                return [ parse_value(element) for element in input ]
            # Case: single input, string or path-like
            elif isinstance(input, (str, os.PathLike)):
                # Case: VIP path
                if str(input).startswith(self._SERVER_PATH_PREFIX): # PurePath.is_relative_to() is unavailable for Python <3.9
                    if self._is_defined('_vip_input_dir'): 
                        input_dir = self._vip_input_dir
                        input_path = PurePosixPath(input)
                    else: # Return input if `_vip_input_dir` is unset
                        return input
                # Case: local path or any other string input
                else:     
                    if self._is_defined('_local_input_dir'): 
                        # We must use absolute paths to find the relative parts
                        input_dir = self._local_input_dir.resolve()
                        input_path = Path(input).resolve()
                    else: # Return input if `_local_input_dir` is unset
                        return input
                # Return the part of `input_path` that is relative to `input_dir` (if relevant)
                try: # No condition since PurePath.is_relative_to() is unavailable for Python <3.9
                    return PurePosixPath( # Force Posix flavor to avoid conflicts with Windows paths when checking equality
                        input_path.relative_to(input_dir)) # Relative part of `input_path`
                except ValueError:
                    # This is the case when no relative part could be found
                    return input
            # Case not string or path-like: return as is
            else: return input
        # -- End of parse_value() --
        # Return the parsed value of each parameter
        return {
            key: parse_value(value)
            for key, value in input_settings.items()
        }
    # ------------------------------------------------

    # Get the input settings after they are parsed
    def _get_input_settings(self, location="vip") -> dict:
        """
        Fits `self._input_settings` to `location`, i.e. write the input paths relatively to `location`.
        Returns the modified settings.

        Prerequisite: input directories are defined depending on `location`
        """
        def get_input(value, location) -> str:
            """
            If `value` is a path, binds this path to `location`.
            Otherwise, returns it as a string.
            Value can be a single input or a list of inputs.
            """
            # Case: multiple inputs
            if isinstance(value, list):
                return [ get_input(element, location) for element in value ]
            # Case : not a path
            elif not isinstance(value, PurePath):
                return value
            # Case : Path relative to any `input_dir` => Cannot be distinguished from other parameters when parsing
            # Case : VIP path
            elif (location == "vip") and self._is_defined("_vip_input_dir"):
                return str(self._vip_input_dir / value) 
            # Case: local path
            elif (location == "local") and self._is_defined("_local_input_dir"):
                return str(self._local_input_dir / value)
            # Otherwise, return input as a string
            else: return str(value)
        # -----------------------
        # Raise an error if `location` cannot be parsed
        if location not in ("vip", "local"):
            raise NotImplementedError(f"Unknown location: {location}")
        # Browse input settings
        return {
            key: get_input(value, location)
            for key, value in self._input_settings.items()
        }
    # ------------------------------------------------

    def _update_input_settings(self) -> None:
        """
        Parses self._input_settings relatively to the input directories.
        This method does nothing if `input_settings` is unset.
        """
        if self._is_defined('_input_settings'):
            self._input_settings = self._parse_input_settings(self._input_settings)
    # ------------------------------------------------

    # Function to convert a VIP path to local output directory
    def _get_local_output_path(self, vip_output_path: PurePosixPath) -> Path:
        """
        Converts a VIP path in local format for VIP outputs. 
        `vip_output_path` can be a single string or a list of strings.
        Assumes `vip_output_path` belongs to to self._vip_output_dir.
        """
        # Replace `vip_output_dir`" by `local_output_dir` in the path
        new = self._local_output_dir / vip_output_path.relative_to(self._vip_output_dir)
        # Replace forbidden characters by '-' if current OS is windows
        if isinstance(new, PureWindowsPath):
            new = Path(re.sub(r'[<>:"?* ]', '-', str(new)))
        # Return
        return new
    # ------------------------------------------------

#######################################################

if __name__=="__main__":
    pass
