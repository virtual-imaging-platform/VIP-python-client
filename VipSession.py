from __future__ import annotations
import os
import json
import tarfile
import time
from pathlib import *
from warnings import warn

from VipLauncher import VipLauncher

import vip

"""
Main Features (leading to public methods)
A. Manage a Session from start to finish, *i.e.*:
    A.1. Login to VIP
    A.2. Upload the input data on VIP
    A.3. Launch executions on VIP
    A.4. Monitor executions on VIP
    A.5. Download the results from VIP
    A.6. Clean up the inputs/outputs on VIP.
B. Additional features for avanced use:
    B.1 Display session properties to the user
    B.2 Clone a session to avoid uploading the same dataset twice

Background Specifications:
C. A VIP session should persist in time:
    C.1 Session attributes are backed up at each session step
    C.2 A backup can be resumed at instanciation
D. A VIP session should be user-friendly:
    D.1 Hide VIP paths to the user and allow multi-OS use (Unix, Windows)
    D.2 Prevent common mistakes in session / pipeline settings
    D.3 Interpret common API exceptions ("Error 8000", etc.)
"""

class VipSession(VipLauncher):
    """
    Python class to run VIP pipelines on local datasets.

    1 "session" allows to run 1 pipeline on 1 dataset with 1 parameter set (any number of pipeline runs).
    Minimal inputs:
    - `pipeline_id` (str) Name of the pipeline in VIP nomenclature. 
        Usually in format : *application_name*/*version*.
    - `input_dir` (str) Local path to the dataset.
        This directory will be uploaded on VIP servers before launching the pipeline.
    - `input_settings` (dict) All parameters needed to run the pipeline.
        See pipeline description.

    N.B.: all instance methods require that `VipSession.init()` has been called with a valid API key. 
    See GitHub documentation to get your own VIP API key.
    """

                    ##################
    ################ Class Attributes ##################
                    ##################

    # Default path to save session outputs on the current machine
    _LOCAL_PATH = Path("vip_outputs").resolve()
    # Default path to upload and download data on VIP servers
    _VIP_PATH = PurePosixPath("/vip/Home/API/")
    # Default file name to save session properties 
    _SAVE_FILE = "session_data.json"

                    ####################
    ################ Instance attributes ##################
                    ####################
                    
    # VIP input directory
    @property
    def vip_input_dir(self) -> str:
        """VIP path to the input data"""
        return str(self._vip_input_dir)
    
    # VIP output directory (No setter)
    @property
    def vip_output_dir(self):
        """VIP path to the output data"""
        return str(self._vip_output_dir)
    
    # Local input directory
    @property
    def input_dir(self):
        """Local path to the input data"""
        return str(self._local_input_dir)
    
    @input_dir.setter
    def input_dir(self, new_dir: str) -> None:
        """Set the local input directory"""
        # Check conflicts with instance value
        if self._is_defined("_local_input_dir") and (new_dir != self._local_input_dir):
            raise ValueError(f"Input directory cannot be changed for session: {self.session_name} ('{self._local_input_dir}' -> '{new_dir}').")
        # Check
        if not self._exists(new_dir,"local"): 
            raise FileNotFoundError(f"The input directory does not exist:\n\t{new_dir}")
        # Assign
        self._local_input_dir = Path(new_dir)

    @input_dir.deleter
    def input_dir(self) -> None:
        """Delete the input directory"""
        del self._local_input_dir
    
    # Overwrite output_dir to point towards a local ouput directory
    @property
    def output_dir(self) -> str:
        """Local path to the output data"""
        return str(self._local_output_dir)
    
    @output_dir.setter
    def output_dir(self, new_dir: str) -> None:
        """Set the local output directory"""
        # Check conflicts with instance value
        if self._is_defined("_local_output_dir") and (new_dir != self._local_output_dir):
            raise ValueError(f"Results directory is already set for session: {self.session_name} ('{self._local_output_dir}' -> '{new_dir}').")
        # Assign
        self._local_output_dir = Path(new_dir)

    @output_dir.deleter
    def output_dir(self) -> None:
        """Delete the output directory"""
        del self._local_output_dir

    # Overwrite input_settings setter to write VIP paths instead of the local ones
    @property
    def input_settings(self) -> dict:
        """All parameters needed to run the pipeline."""
        return self._input_settings
    
    @input_settings.setter
    def input_settings(self, input_settings: dict):
        """Set the input settings."""
        new_settings = self._vip_input_settings(input_settings)
        # Check conflicts with instance attribute
        if self._is_defined("_input_settings") and (new_settings != self._input_settings):
            raise ValueError(f"Input settings are already set for session: {self.session_name}.")
        # Update
        self._input_settings = new_settings

    @input_settings.deleter
    def input_settings(self) -> None:
        """Delete the input settings"""
        del self._input_settings
    

                    #############
    ################ Constructor ##################
                    #############
    ## TODO : Change routine for verifying properties are set (_is_defined() / getter-setter things to avoid verfying existence each time)
    def __init__(
            self, session_name="",  input_dir="", pipeline_id="",  
            input_settings:dict={}, output_dir="", verbose=True
        ) -> None:
        """
        Create a VipSession instance from keyword arguments. 
        Displays informations if `verbose` is True.

        Available keywords:
        - `session_name` (str) A name to identify this session.
            Default value: 'session_[date]_[time]'

        - `input_dir` (str) Local path to your full dataset.
            This directory must be uploaded on VIP servers before pipeline runs.

        - `pipeline_id` (str) Name of your pipeline in VIP. 
            Usually in format : *application_name*/*version*.

        - `input_settings` (dict) All parameters needed to run the pipeline.
            See pipeline description for more information.

        - `output_dir` (str) Local path to the directory where: 
            - session properties will be saved; 
            - pipeline outputs will be downloaded from VIP servers.

            Default value: './vip_outputs/[`session_name`]'
        
        If `session_name` or `output_dir` lead to data from a previous session, 
        all properties will be loaded from the session file ('session_data.json').
        """
        # Initiate parameters without the input settings
        super().__init__(
            session_name=session_name,
            pipeline_id=pipeline_id,
            verbose=False
        )
        if verbose:
            print(f"\n<<< SESSION '{self.session_name}' >>>\n")
        # Set the output directory
        if output_dir:
            self.output_dir = output_dir
        else:
            self.output_dir = self._LOCAL_PATH / self.session_name
        # Check existence of data from a previous session
        if not self._load_session(verbose=verbose):
            # Assign all properties
            if verbose: 
                print("New VIP session")
                print("---------------")
            # Check & Assign: Local path to the input data
            if input_dir:
                if verbose: print("Input Directory: ", end="")
                self.input_dir = input_dir
                if verbose: print("Checked.")
            # Assign: VIP path to the input data (default value)
            self._vip_input_dir = self._VIP_PATH / self._session_name / "INPUTS"
            # Assign: VIP path to the output data (default value)
            self._vip_output_dir = self._VIP_PATH / self._session_name / "OUTPUTS"
            # Check & Assign: Input settings 
            if input_settings:
                if verbose: print("Input Settings: ", end="")
                done = self._check_input_settings(input_settings) # check local values
                self._input_settings = self._vip_input_settings(input_settings) # set VIP values
                if verbose: 
                    print("Checked." if done else "Unchecked.")
            # Workflow inventory (default value)
            self._workflows = {}
            # End
            if verbose: 
                print("---------------")
    # ------------------------------------------------

                    ################
    ################ Public Methods ##################
                    ################

    #################################################
    # ($A) Manage a session from start to finish
    #################################################

    # ($A.1) Login to VIP
    @classmethod
    def init(cls, api_key: str, verbose=True, **kwargs) -> VipSession:
        """
        Handshakes with VIP using your API key. 
        Prints a list of pipelines available with the API key, unless `verbose` is False.
        Returns a VipSession instance which properties can be provided as keyword arguments (`kwargs`).

        Input `api_key` can be either:
        A. (unsafe) a string litteral containing your API key, or
        B. (safer) a path to some local file containing your API key, or
        C. (safer) the name of some environment variable containing your API key.

        In cases B or C, the API key will be loaded from the local file or the environment variable.        
        """
        # Handshake with VIP
        super().init(api_key=api_key, verbose=False)
        # Return a VipSession instance for method cascading
        return VipSession(verbose=(verbose and kwargs), **kwargs)
    # ------------------------------------------------
   
    # ($A.2) Upload a dataset on VIP servers
    def upload_inputs(self, input_dir="", update_files=True, verbose=True) -> VipSession:
        """
        Uploads to VIP servers a dataset contained in the local directory `input_dir` (if needed).
        - If `input_dir` is not provided, session properties are used. If provided, session properties are updated.
        - If `update_files` is True, the input directory on VIP will be checked in depth to upload missing files.
        If `update_files` is False and some input directory already exists on VIP, the upload procedure is skipped to save time.
        - Set `verbose` to False to upload silently.

        Session data are saved the end of the upload procedure.

        Raises AssertionError if the input data could not be found on this machine.
        """
        if verbose: print("\n<<< UPLOAD INPUTS >>>\n")
        # Check the distant input directory        
        try: 
            # Check connection with VIP 
            exists = self._exists(self._vip_input_dir, location="vip")
        except RuntimeError as vip_error:
            self._handle_vip_error(vip_error)
        # Return if `update_files` is False and input data are already on VIP
        if exists and not update_files:
            if verbose: 
                print("Skipped : There are already input data on VIP.")
            # Return for method cascading
            return self
        # Set local input directory
        if input_dir:
            self.input_dir = input_dir
        elif not self._is_defined("_local_input_dir"): 
                raise TypeError(f"Session '{self.session_name}': Please provide an input directory.")
        # Check local input directory
        if not self._exists(self._local_input_dir, location="local"): 
            raise ValueError(f"Session '{self.session_name}': Input directory does not exist.")
        # Initial display
        if verbose:
            print("Uploading the dataset on VIP")
            print("-----------------------------")
        # Upload the input repository
        try:
            failures = self._upload_dir(self._local_input_dir, self._vip_input_dir, verbose=verbose)
            # Display report
            if verbose:
                print("-----------------------------")
                if not failures :
                    print( "Everything is on VIP.")
                else: 
                    print("End of the process.") 
                    print( "The following files could not be uploaded on VIP:\n\t")
                    print( "\n\t".join(failures))
        except Exception as e:
            # An unexpected error occurred
            if verbose:
                print("-----------------------------")
                print("\n(!) Upload was stopped following an unexpected error.")
            raise e from None
        finally:
            # In any case, save session properties
            self._save_session(verbose=verbose)
        # Return for method cascading
        return self
    # ------------------------------------------------

    # ($A.3) Launch executions on VIP 
    def launch_pipeline(
            self, pipeline_id="", input_settings:dict={}, nb_runs=1, verbose=True
        ) -> VipSession:
        """
        Launches pipeline executions on VIP.

        Input parameters :
        - `pipeline_id` (str) The name of your pipeline in VIP, 
        usually in format : *application_name*/*version*.
        - `input_settings` (dict) All parameters needed to run the pipeline.
        - `nb_runs` (int) Number of parallel runs of the same pipeline with the same settings.
        - Set `verbose` to False to launch silently.
        
        Default behaviour:
        - Raises AssertionError in case of wrong inputs 
        - Raises RuntimeError in case of failure on VIP servers.
        - In any case, session is backed up after pipeline launch
        """
        try :
            super().launch_pipeline(
                pipeline_id=pipeline_id,
                input_settings=input_settings,
                nb_runs=nb_runs,
                verbose=verbose
            )
        except Exception as e:
            raise e
        finally:
            # In any case, save session properties on Girder
            self._save_session(verbose=True)
        # Return for method cascading
        return self
    # ------------------------------------------------

    # ($A.4) Monitor worflow executions on VIP 
    def monitor_workflows(self, waiting_time=30, verbose=True) -> VipSession:
        """
        Updates and displays status for each execution launched in the current session.
        - If an execution is still runnig, updates status every `waiting_time` (seconds) until all runs are done.
        - If `verbose`is True, displays a full report when all executions are done.
        """
        if verbose: print("\n<<< MONITOR WORKFLOW >>>\n")
        # Check if current session has existing workflows
        if not self._workflows:
            if verbose:
                print("\nThis session has not yet launched any execution.")
                print("Run launch_pipeline() to launch workflows on VIP.")
            return self
        # Update existing workflows
        if verbose: print("Updating workflow status ... ", end="")
        self._update_workflows(save_session=True)
        if verbose: print("Done.")
        # Check if workflows are still running
        if self._still_running():
            # First execution report
            self._execution_report(verbose)
            # Display standby
            if verbose:
                print("\n-------------------------------------------------------------")
                print("The current proccess will wait until all executions are over.")
                print("Their progress can be monitored on the VIP portal:")
                print("\thttps://vip.creatis.insa-lyon.fr/")
                print("-------------------------------------------------------------")
            # Standby until all executions are over
            while self._still_running():
                time.sleep(waiting_time)
                self._update_workflows(save_session=True)
            # Display the end of executions
            if verbose: print("All executions are over.")
        # Last execution report
        self._execution_report(verbose)
        # Display saving data
        if verbose: print(f"\nSession properties were saved.\n")
        # Return for method cascading
        return self
    # ------------------------------------------------

    # ($A.5) Download execution outputs from VIP servers 
    def download_outputs(self, get_status=["Finished"], unzip=True, verbose=True) -> VipSession:
        """
        Downloads all session outputs from VIP servers.
        - If `unzip` is True, extracts the data if any output is a .tar file.
        - Set `verbose` to False to download silently.
        """
        if verbose: print("\n<<< DOWNLOAD OUTPUTS >>>\n")
        # Check if current session has existing workflows
        if not self._workflows:
            if verbose:
                print("This session has not yet launched any execution.")
                print("Run launch_pipeline() to launch workflows on VIP.")
                print("Current session properties are:")
                self.display_properties()
            return self
        # Update the worflow inventory
        if verbose: print("Updating workflow status ... ", end="")
        self._update_workflows(save_session=False)
        if verbose: print("Done.\n")
        # Initial display
        if verbose:
            print("Downloading pipeline outputs to:\n\t", self._local_output_dir)
            print("--------------------------------")
        # Get execution report
        report = self._execution_report(verbose=False)
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
                if verbose: 
                    print(f"[{nExec}/{nb_exec}] Outputs from:", wid, "-> REMOVED from VIP servers")
                # Get the path of the returned files on VIP
                vip_outputs = self._workflows[wid]["outputs"]
                # If there is no output file, go to the next execution
                if not vip_outputs: 
                    if verbose: print("\tNothing to download.")
                    continue
                # Browse the output files to check if they have already been downloaded
                missing_file = False
                for output in vip_outputs:
                    # Get the output path on VIP
                    vip_file = Path(output["path"])
                    # Get the local equivalent path
                    local_file = self._get_local_output_path(vip_file)
                    # Check file existence on the local machine
                    if not local_file.exists(): 
                        missing_file = True
                # After checking all files, update the display
                if verbose: 
                    if not missing_file: 
                        print("\tOutput files are already in:", local_file.parent.resolve())
                    else: 
                        print("(!)\tCannot download the missing files.")
        # Check if any workflow with the desired status is available
        if not any([status in report for status in get_status]):
            if verbose:
                print("--------------------------------")
                print("Nothing to download for the current session.") 
                print("Run monitor_workflows() for more information.") 
            return self
        # Download each output file for each execution and keep track of failed downloads
        failures = []
        for wid in self._workflows:
            # Check if the workflow should be processed
            if self._workflows[wid]["status"] not in get_status:
                continue
            nExec+=1 
            # Display current execution
            if verbose: 
                print(f"[{nExec}/{nb_exec}] Outputs from: ", wid, 
                    " | Started on: ", self._workflows[wid]["start"],
                    " | Status: ", self._workflows[wid]["status"], sep='')
            # Get the path of the returned files on VIP
            vip_outputs = self._workflows[wid]["outputs"]
            # If there is no output file, go to the next execution
            if not vip_outputs: 
                if verbose: print("\tNothing to download.")
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
                if self._make_dir(local_dir) and verbose: print("\tNew directory:", local_dir)
                # Display the process
                size = f"{output['size']/(1<<20):,.1f}MB"
                if verbose: print(f"\t[{nFile}/{len(vip_outputs)}] Downloading file ({size}):", 
                                local_file.name, end=" ... ")
                # Download the file from VIP servers
                if self._download_file(vip_path=vip_file, local_path=local_file):
                    # Display success
                    if verbose: print("Done.")
                    # If the output is a tarball, extract the files and delete the tarball
                    if unzip and output["mimeType"]=="application/gzip" and tarfile.is_tarfile(local_file):
                        if verbose: print("\t\tExtracting archive content ...", end=" ")
                        if self._extract_tarball(local_file):
                            if verbose: print("Done.") # Display success
                        elif verbose: 
                            print("Extraction failed.") # Display failure
                else: # failure while downloading the output file
                    # Update display
                    if verbose: print(f"\n(!)\tSomething went wrong in the process. Please retry later.")
                    # Update missing files
                    failures.append(str(vip_file))
            # End of file loop
            if verbose:
                if not missing_file: # All files were already there
                    print("\tAlready in:", local_file.parent) 
                else:  # Some missing files were succesfully downloaded
                    print("\tDone for all files.")
        # End of worflow loop    
        if verbose:
            print("--------------------------------")
            if not failures :
                print("Done for all executions.")
            else:
                print("End of the procedure.") 
                print("The following files could not be downloaded from VIP: \n\t", end="")
                print("\n\t".join(failures))
            print()
        # Return for method cascading
        return self
    # ------------------------------------------------

    # ($A.2->A.5) Run a full VIP session 
    def run_session(
            self, update_files=True, nb_runs=1, waiting_time=30, 
            get_status=["Finished"], unzip=True, verbose=True
        ) -> VipSession:
        """
        Runs a full session without the finish() step.
        1. Uploads the database on VIP or check the uploaded files;
        2. Launches pipeline executions on VIP;
        3. Monitors pipeline executions until they are all over;
        4. Downloads execution results from VIP.

        /!\ This function assumes that all session properties are already set.
        Optional arguments can still be provided:
        - Set `update_files` to False to avoid checking the input data on VIP;
        - Increase `nb_runs` to run more than 1 execution at once;
        - Set `waiting_time` to modify the default monitoring time;
        - Set `get_status` to download files from workflows with a specific status
        - Set unzip to False to avoid extracting .tgz files during the download. 
        
        Set `verbose` to False to run silently
        """
        return (
            # 1. Upload the database on VIP or check the uploaded files
            self.upload_inputs(update_files=update_files, verbose=verbose)
            # 2. Launche `nb_runs` pipeline executions on VIP
            .launch_pipeline(nb_runs=nb_runs, verbose=verbose)
            # 3. Monitor pipeline executions until they are all over
            .monitor_workflows(waiting_time=waiting_time, verbose=verbose)
            # 4. Download execution results from VIP
            .download_outputs(get_status=get_status, unzip=unzip, verbose=verbose)
        )

    # ($A.6) Clean session data on VIP
    def finish(self, force_remove=False, verbose=True) -> VipSession:
        """
        Removes session data from VIP servers and keeps session data on the current machine.
        - If `verbose` is True, displays information
        - If `force_remove` is True, data which do not belong 

        Displays warning in case of failure. 
        """
        # Initial display
        if verbose: print("\n<<< FINISH >>>\n")
        # Check if workflows are still running (without call to VIP)
        if self._still_running():
            # Update the workflow inventory
            if verbose: print("Updating workflow status ... ", end="")
            self._update_workflows(save_session=False)
            if verbose: print("Done.")
            # Return is workflows are still running
            if self._still_running():
                self._execution_report(verbose)
                if verbose: 
                    print("\n(!) This session cannot be finished since the pipeline might still generate data.\n")
                    return self
        # Initial display
        if verbose:
            print("Ending Session:", self._session_name)
            print("-------------------------")
            print("Removing data from VIP servers ... ", end="")
        # Get the folder of interest
        path = self._VIP_PATH / self._session_name
        # Check data existence on VIP
        try:
            exists = self._exists(path, location="vip")
        except RuntimeError as vip_error:
            self._handle_vip_error(vip_error)
        if not exists:
            # Session may be already over
            print()
            done = True
        else:
            # Erase the session folder on VIP
            done = self._delete_path(path, verbose=verbose)
            # Display success
            if verbose:
                if done: print("Done.\n")
        # End the procedure in case of failure
        if not done:
            if verbose: 
                print("-------------------------")
                print(f"Session <{self._session_name}> is not yet over.")
                print("Run finish() again later to end the process.\n")
            return self
        # Check if the input data have been erased (this is not the case when get_inputs have been used)
        success = True # Will remain True if all data have been removed
        warning_msg = "" # Will grow up in case of failure
        finished = False # Will become True when workflow status are set to "Remove"
        if self._exists(self._vip_input_dir, location="vip"):
            # Removal failed
            if force_remove:
                # Try to force removal
                success = self._delete_path(self._vip_input_dir, verbose=verbose)
                # Remove the parent directory if it is empty
                parent = self._vip_input_dir.parent
                if not vip.list_content(str(parent)):
                    self._delete_path(parent, verbose=verbose)
            else:
                success = False
            # Warning message
            if verbose and not success: 
                warning_msg += ">> The input data were not removed: they may be shared with another session ?"
                warning_msg += f"\n\tRun: finish(force_remove=True) to force their removal.\n"
        # Check if the output data have been erased
        if self._is_defined("_vip_output_dir"):
            if force_remove:
                # Try to force removal
                success = self._delete_path(self._vip_output_dir, verbose=verbose)
                # Remove the parent directory if it is empty
                parent = self._vip_input_dir.parent
                if not vip.list_content(str(parent)):
                    self._delete_path(parent, verbose=verbose)
            else:
                success = False
            # Warning message
            if verbose and not success: 
                warning_msg += ">> The output data were not removed."
                warning_msg += f"\n\tRun: finish(force_remove=True) to force their removal.\n"
        else:
            # Removal was successful: update the worflow inventory to avoid dead links in future downloads
            for wid in self._workflows:
                self._workflows[wid]["status"] = "Removed"
            # Update flag
            finished = True
        # Display success
        if verbose:
            if success: 
                print("Session data were fully removed from VIP servers.")
            else: 
                print("(!) Session data were not fully removed from VIP servers.")
                print(warning_msg)
            print("-------------------------")
        # Save data if workflow status have been updated
        if finished:
            if verbose: print(f"Session <{self._session_name}> is now over.")
            # Save session
            self._save_session(verbose=verbose)
        elif verbose: print(f"Session <{self._session_name}> is not yet over.")
        # Return for method cascading
        return self
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
        - `local_input_dir` : path to the dataset *on your machine*
        - `vip_input_dir` : path to the dataset *in your VIP Home directory*
        - `local_output_dir` : path to the pipeline outputs *on your machine*
        - `vip_output_dir` : path to the pipeline outputs *in your VIP Home directory*
        - `input_settings` : input parameters sent to VIP 
        (note that file locations are bound to `vip_input_dir`).
        - `workflows`: workflow inventory, identifying all pipeline runs in this session.
        """
        # Data to display 
        vip_data={
            "session_name": self._session_name,
            "pipeline_id": self._pipeline_id,
            "local_input_dir": str(self._local_input_dir),
            "local_output_dir": str(self._local_output_dir),
            "vip_input_dir": str(self._vip_input_dir),
            "vip_output_dir": str(self._vip_output_dir),
            "workflows": self._workflows,
            "input_settings": self._input_settings,
        }
        # Display
        print(json.dumps(vip_data, indent=4))
        # Return for method cascading
        return self
    # ------------------------------------------------

    # ($B.2) Get inputs from another session to avoid double uploads
    def get_inputs(self, session: VipSession, get_pipeline=False, get_settings=False, verbose=True) -> VipSession:
        """
        Allows the current session to use the inputs of another one (`session`)
        to avoid re-uploading the same dataset on VIP.
        - Current session will point to `session`'s input directory (*input_dir*) locally and on VIP;
        - If `get_pipeline` is True, the current *pipeline_id* is also synchronized with `session`;
        - If `get_settings` is True, the current *input_settings* are also synchronized with `session`.
        - Displays information if `verbose` is True.

        Raises AssertionError if:
        - The current session already has input or output data on VIP ;
        - The other `session` do not have input data on VIP.
        """
        # End the procedure if both sessions already share the same inputs
        if self._vip_input_dir == session._vip_input_dir:
            # Display
            if verbose: 
                print(f"\nSessions '{self._session_name}' and '{session._session_name}' share the same inputs.")
            # Return for method cascading
            return self
        # Check if current session do not have data on VIP
        try:
            assert not vip.exists(str(self._VIP_PATH/self._session_name)), \
                f"Session '{session._session_name}' already has data on VIP.\n" \
                    + "Please finish this session and start another one."
        except RuntimeError as vip_error:
            self._handle_vip_error(vip_error)
        # Check if the data actually exist on VIP
        try:
            if not self._exists(session._vip_input_dir, location="vip"):
                raise FileNotFoundError(f"Input data for session '{session._session_name}' do not exist on VIP.")
        except RuntimeError as vip_error:
            self._handle_vip_error(vip_error)
        # Get the VIP inputs from the other session
        self._set(
            local_input_dir=session._local_input_dir, # Local data
            vip_input_dir=session._vip_input_dir, # Distant data 
        )
        # Get the pipeline identifier from the other session
        if get_pipeline:
            self._set(pipeline_id=session._pipeline_id)
        # Get the input settings from the other session
        if get_settings:
            self._set(input_settings=session._input_settings)
        # Display success
        if verbose : 
            print(
                f"\nSession '{self._session_name}' now shares its inputs "\
                + f"with session '{session._session_name}'." )
        # Save new properties
        self._save_session(verbose=verbose)
        # Return for method cascading
        return self
    # -----------------------------------------------

                    #################
    ################ Private Methods ################
                    #################

    #################################################
    # ($A) Manage a session from start to finish
    #################################################

    # ($A.2/A.5) Upload (/download) data on (/from) VIP Servers
    ###########################################################

    # Function to upload all files from a local directory
    @classmethod
    def _upload_dir(cls, local_path: Path, vip_path: PurePosixPath, verbose=True) -> list:
        """
        Uploads all files in `local_path` to `vip_path` (if needed).
        Displays what it does if `verbose` is set to True.
        Returns a list of files which failed to be uploaded on VIP.
        """
        # Scan the local directory
        assert cls._exists(local_path), f"{local_path} does not exist."
        # First display
        if verbose: print(f"Cloning: {local_path} ", end="... ")
        # Look for subdirectories
        subdirs = [
            elem for elem in local_path.iterdir() 
            if elem.is_dir()
        ]
        # Scan the distant directory and look for files to upload
        if cls._make_dir(vip_path, location="vip"):
            # The distant directory did not exist before call
            # -> upload all the data (no scan to save time)
            files_to_upload = [
                elem for elem in local_path.iterdir()
                if elem.is_file()
            ]
            if verbose:
                print("(Created on VIP)")
                if files_to_upload:
                    print(f"\t{len(files_to_upload)} files to upload.")
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
            if verbose:
                if files_to_upload: 
                    print(f"\n\tVIP clone already exists and will be updated with {len(files_to_upload)} files.")
                else:
                    print("Already on VIP.")
        # Upload the files
        nFile = 0
        failures = []
        for local_file in files_to_upload :
            nFile+=1
            # Display the current file
            if verbose:
                size = f"{local_file.stat().st_size/(1<<20):,.1f}MB"
                print(f"\t[{nFile}/{len(files_to_upload)}] Uploading file: {local_file.name} ({size}) ...", end=" ")
            # Upload the file on VIP
            vip_file = vip_path/local_file.name # file path on VIP
            if cls._upload_file(local_path=local_file, vip_path=vip_file):
                # Upload was successful
                if verbose: print("Done.")
            else:
                # Update display
                if verbose: print(f"\n(!) Something went wrong during the upload.")
                # Update missing files
                failures.append(str(local_file))
        # Recurse this function over sub-directories
        for subdir in subdirs:
            failures += cls._upload_dir(
                local_path=subdir,
                vip_path=vip_path/subdir.name,
                verbose=verbose
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
        os.rename(local_file, archive) # pathlib version not worth it in Python 3.7
        # Create a new directory to store archive content
        cls._make_dir(local_file)
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

    # (A.4) Monitor pipeline executions on VIP servers
    ##################################################

    # Get and display a report over all executions in the current session
    def _execution_report(self, verbose=True) -> dict:
        """
        Sorts workflows by status. Returns the result in dictionnary shape.
        If `verbose` is True, interprets the result to the user.
        """
        # Initiate status report
        report={}
        # Browse workflows
        for wid in self._workflows:
            # Get status
            status = self._workflows[wid]["status"]
            # Update the report
            if status in report:
                # update status
                report[status].append(wid)
            else:
                # create status
                report[status] = [wid]
        # Interpret the report to the user
        if verbose:
            # Function to print a detailed worfklow list
            def detail(worfklows: list): 
                for wid in worfklows:
                    print("\t", wid, ", started on:", self._workflows[wid]["start"])
            # Browse status
            for status in report:
                # Display running executions
                if status == 'Running':
                    # check if every workflow is running
                    if len(report[status])==len(self._workflows):
                        print(f"All executions are currently running on VIP.")
                    else: # show details
                        print(f"{len(report[status])} execution(s) is/are currently running on VIP:")
                        detail(report[status])
                # Display successful executions
                elif status == 'Finished':
                    # check if every run was successful
                    if len(report[status])==len(self._workflows):
                        print(f"All executions ({len(report[status])}) ended with success.")
                    else: # show details
                        print(f"{len(report[status])} execution(s) ended with success:")
                        detail(report[status])
                # Display executions with removed data
                elif status == 'Removed':
                    # check if every run was removed
                    if len(report[status])==len(self._workflows):
                        print("This session is over.")
                        print("All output data were removed from VIP servers.")
                    else: # show details
                        print(f"Outputs from {len(report[status])} execution(s) were removed from VIP servers:")
                        detail(report[status])
                # Display failed executions
                else:
                    # check if every run had the same cause of failure:
                    if len(report[status])==len(self._workflows):
                        print(f"All executions ({len(report[status])}) ended with status:", status)
                    else: # show details
                        print(f"{len(report[status])} execution(s) ended with status:", status)
                        detail(report[status])
            # End of loop on report
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
    def _update_workflows(self, save_session=True) -> None:
        """
        Updates the status of each workflow in the inventory. 
        Saves the session silently unless `save_session` is False.
        """
        for wid in self._workflows:
            # Check if workflow data have been removed
            if self._workflows[wid]["status"] != "Removed":
                # Recall execution info & update the workflow status
                self._workflows[wid].update(self._get_exec_infos(wid))
        # Save & return
        if save_session:
            self._save_session(verbose=False)
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
    
    ###################################
    # ($C) Backup / Resume Session Data 
    ###################################

    def _force_update(setter_function):
        def inner(*args, **kwargs):
            try:
                setter_function(*args, **kwargs)
            except ValueError:
                pass
        return inner

    # Generic method to set session properties
    @_force_update
    def _set(self, **kwargs) -> VipSession:
        """
        Sets session properties based on keywords arguments.

        Available keywords:
        - `session_name` (str) A name to identify this session on VIP servers.
        - `pipeline_id` (str) The name of your pipeline in VIP, 
        usually in format : *application_name*/*version*.
        - `input_settings` (dict) All parameters needed to run the pipeline.
        - `input_dir` or `local_input_dir` (str) The local path to your full dataset, 
        to be uplodaded with `_upload_inputs` 
        - `output_dir` or `local_output_dir` (str) The local path 
        where pipeline outputs will be downloaded after computation.

        For advanced users:
        - `vip_input_dir` (str) Distant directory where the dataset will be uploaded on VIP. 
            Default value : '`VipSession._VIP_PATH`/`self._session_name`/INPUTS'
            *Caution*: Modifying this value will not automatically update `self._input_settings`.
        - `vip_output_dir` (str) Local directory where pipeline outputs will be downloaded after computation.
            Default value : '`VipSession._VIP_PATH`/`self._session_name`/OUPUTS'
        - `workflows` (dict) Inventory of all worflows launched within the session.
            Each workflow is characterized by a status, a start date and a list of output files.
        """
        # Set session name
        if "session_name" in kwargs:
            # check the session name
            self._check_session_name(kwargs["session_name"])
            # Set the new value
            self._session_name = kwargs.pop("session_name")
        # Set pipeline ID
        if "pipeline_id" in kwargs:
            self._pipeline_id = kwargs.pop("pipeline_id")
        # Set local input path (keywords `input_dir` and `local_input_dir`)
        if "input_dir" in kwargs:
            self._local_input_dir = Path(kwargs.pop("input_dir"))
        elif "local_input_dir" in kwargs:
            self._local_input_dir = Path(kwargs.pop("local_input_dir"))
        # Set local output path (keywords `output_dir` and `local_output_dir`)
        if "output_dir" in kwargs:
            self._local_output_dir = Path(kwargs.pop("output_dir"))
        elif "local_output_dir" in kwargs:
            self._local_output_dir = Path(kwargs.pop("local_output_dir"))
        # Set VIP input path (no check)
        if "vip_input_dir" in kwargs:
            self._vip_input_dir = PurePosixPath(kwargs.pop("vip_input_dir"))
        # Set VIP output path (no check)
        if "vip_output_dir" in kwargs:
            self._vip_output_dir = PurePosixPath(kwargs.pop("vip_output_dir"))
        # Set the Input Settings (depends on the new vip_input_path)
        if "input_settings" in kwargs:
            self._input_settings = self._vip_input_settings(kwargs.pop("input_settings"))
        # Set Worflows Inventory (no check)
        if "workflows" in kwargs:
            self._workflows = kwargs.pop("workflows")
        # Check unknown properties
        if kwargs: raise TypeError(f"Unknown propertie(s) : {', '.join(kwargs.keys())}.")
        # Return for method cascading
        return self
    # ------------------------------------------------

    # ($C.1) Save session properties in a JSON file
    def _save_session(self, file="", verbose=False) -> None:
        """
        Saves useful instance properties in a JSON file. 
        Returns the path of this session file.
        Also displays this path is verbose is True.

        By default, the JSON file is located in `self._local_output_dir`
        and named after: `VipSession._SAVE_FILE`.
        User can provide `file` (str) to save to another location.

        The saved properties are :
        - `session_name`: current session name
        - `pipeline_id`: pipeline identifier
        - `input_directory`: location of the dataset *in your VIP Home directory*
        - `input_settings`: input parameters sent to VIP, 
        where file locations refer to `input_directory`.
        - `workflows`: workflow inventory, 
        identifying all VIP executions launched during this session, with their status
        """
        # Default location
        if not file:
            file = self._local_output_dir / self._SAVE_FILE
        else:
            file=Path(file).resolve()
        # Data to save 
        vip_data={
            "session_name": self._session_name,
            "pipeline_id": self._pipeline_id,
            "local_input_dir": str(self._local_input_dir),
            "local_output_dir": str(self._local_output_dir),
            "vip_input_dir": str(self._vip_input_dir),
            "vip_output_dir": str(self._vip_output_dir),
            "workflows": self._workflows,
            "input_settings": self._input_settings,
            # Soon: hardware information ?
        }
        # Make the output directory if it does not exist
        is_new = self._make_dir(file.parent, "local")
        # Save the data in JSON format
        with file.open("w") as outfile:
            json.dump(vip_data, outfile, indent=4)
        # Display
        if verbose:
            if is_new: 
                print(f"\nSession properties are saved in:\n\t{file}\n")
            else:
                print(f"\nSession properties have been saved.")
    # ------------------------------------------------

    # ($C.2) Load session properties from a JSON file
    def _load_session(self, verbose=True) -> bool:
        """
        Loads session properties from the local output directory.
        If current properties (e.g. `session_name`) are already set, they will be replaced.

        Returns a success flag. Displays success message unless `verbose` is False.
        """
        # Check the local output directory is defined
        if not self._is_defined("_local_output_dir"):
            return False
        # Check existence of data from a previous session
        file = self._local_output_dir / self._SAVE_FILE
        if not file.is_file():
            return False
        # Load the JSON file
        with file.open() as fid:
            vip_data = json.load(fid)
        # Set all instance properties
        self._set(**vip_data)
        # Update the output directory
        self._set(local_output_dir=file.parent)
        # Display
        if verbose:
            print("An existing session was found.")
            print("Session properties were loaded from:\n\t", file)
        # Return
        return True
    # ------------------------------------------------

    ######################################
    # ($D) Make VipSession user-friendly
    ######################################
    
    # ($D.1) Hide VIP paths to the user and allow multi-OS use (Unix, Windows)
    ###########################################################################

    # Insert VIP paths in the pipeline's input settings
    def _vip_input_settings(self, my_settings:dict={}) -> dict:
        """
        Fits `my_settings` to VIP servers, i.e. converts local paths to valid paths on VIP.
        Returns the modified settings.

        Input `my_settings` (dict) must contain only strings or lists of strings.
        """
        # Return if my_settings is empty or the local input path is unset
        if not my_settings or not self._is_defined("_local_input_dir"):
            return {}
        # Check the input type
        assert isinstance(my_settings, dict), \
            "Please provide input parameters in dictionnary shape."
        # Convert local paths into VIP paths
        vip_settings = {
                input: self._get_vip_input_path(my_settings[input])
                for input in my_settings
            }
        # Set the results directory
        vip_settings["results-directory"] = str(self._vip_output_dir)
        # Set Input settings
        return vip_settings
    # ------------------------------------------------

    # Function to convert a local path to VIP standards
    def _get_vip_input_path(self, input_path):
        """
        Converts a local path in VIP format for local inputs. 
        `input_path` can be a single string or a list of strings.
        """
        # If input_path is a string: replace by VIP path (when relevant)
        if isinstance(input_path, str):
            # Return if input_path is already a VIP path
            if input_path.startswith("/vip"):
                return input_path
            # We use absolute path since relative ones are unpredictable
            in_path = Path(input_path).resolve()
            # Check if _local_input_dir has been set
            assert self._is_defined("_local_input_dir"), "Attribute `_local_input_dir` is unset."
            # Replace `local_input_dir` by `vip_input_dir` in the path
            try: # Raises ValueError if `local_input_dir` does not belong to `vip_input_dir`
                new = self._vip_input_dir / in_path.relative_to(self._local_input_dir.resolve())
                # Return the string version
                return str(new)
            except ValueError:
                # This is not a local input path: return the original string
                return input_path
        # If the input_path is a list : use this function recursively
        elif isinstance(input_path, list):
            return [ self._get_vip_input_path(element) for element in input_path ]
        # If input_path is something else: raise an error (this method should be updated)
        else:
            raise NotImplementedError(f"The folllowing object:\n\t{input_path}\nshould be a string or a list of strings.")
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
        invalid_for_windows = '<>:"?* '
        new_str = str(new.resolve())
        if isinstance(new, WindowsPath):
            for char in invalid_for_windows: new_str = new_str.replace(char, '-')
        # Return
        return Path(new_str).resolve()
    # ------------------------------------------------

    # ($D.2) Prevent common mistakes in session / pipeline settings 
    ###############################################################

    # Check the input settings based on pipeline descriptor
    def _check_input_settings(self, input_settings: dict={}) -> bool:
        """
        Checks `input_settings` with respect to pipeline descriptor. 
        If `input_settings` is not provided, checks the instance attribute.
        
        This function uses instance properties like `_local_input_dir`, `_pipeline_id`
        to run assertions.
        Returns True if each assertion could be tested, False otherwise.
        
        Detailed behaviour:
        - If `input_settings` contains paths to files (locally or on VIP), 
        existence of every file will be checked.
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
            self._handle_vip_error(vip_error)
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
        assert unknown_fields <= {"results-directory"}, \
            "Unkown input parameters :\n" + ", ".join(unknown_fields) # "results-directory" is specific to VIP
        # FILE EXISTENCE -----------------------------------------------------------
        # Check if an input directory has been set
        if not self._is_defined("_local_input_dir"):
            warn("Input settings could not be fully checked without the input directory.")
            return False
        # Function to assert file existence
        def assert_exists(file): 
            if file.startswith("/vip"): # VIP path
                # The file must exist on VIP
                if not self._exists(file, location="vip"):
                    raise FileNotFoundError((f"File: '{file}' does not exist on VIP."))
            else: # Local path
                # The file must exist
                if not self._exists(file, location="local"):
                    raise FileNotFoundError((f"File: '{file}' does not exist."))
                _file =  Path(file).resolve(strict=True)
                # The file must belong to _local_input_dir
                try:
                    if not _file.is_relative_to(self._local_input_dir.resolve()):
                        raise ValueError(f"File: '{file}' does not belong to session's input directory.")
                except AttributeError as AE: # Raises AttributeError for Python < 3.9
                    try: # the ugly way
                        _file.relative_to(self._local_input_dir.resolve())
                    except ValueError as VE: # Raises ValueError if `file` does belong to `_local_input_dir`
                        raise ValueError(f"File: '{file}' does not belong to session's input directory.") from None
        # Browse the input parameters
        for param in parameters:
            # Skip irrelevant inputs
            if not param['name'] in input_settings:
                continue
            # Get input value
            value = input_settings[param['name']]
            # Check files existence
            if param["type"] == "File":
                # Case: single file
                if isinstance(value, str):
                    assert_exists(value)
                # Case : list of files
                elif isinstance(value, list):
                    for file in value : assert_exists(file)
                # Case : wrong format
                else:
                    raise TypeError(f"Parameter {param['name']} should be a path or a list of paths.")
            # Check string format
            elif param["type"] == "String":
                # Case: single value
                if isinstance(value, str):
                    assert isinstance(value, str), f"{value} should be a string."
                # Case : list of values
                elif isinstance(value, list):
                    for val in value : 
                        assert isinstance(val, str), f"{val} should be a string."
                # Case : wrong format
                else:
                    raise TypeError(f"Parameter {param['name']} should be a string or a list of strings.")
            # Check other formats ?
            else: 
                # TODO
                pass
        # Ensure parameter "results-directory" is in line with instance attribute (vip_output_dir)
        if "results-directory" in input_settings:
            if input_settings["results-directory"] != str(self._vip_output_dir):
                warn(
                    f"Results directory has been updated according to the input settings.\n\
                    Old path: {self._vip_output_dir}\n\
                    New path: {input_settings['results-directory']}\n"
                )
                self._set(vip_output_dir=input_settings['results-directory'])
        # Return True when all checks are complete
        return True
    # ------------------------------------------------         

    # ($D.3) Interpret common API exceptions
    ########################################

    # Function to handle VIP runtime errors and provide interpretation to the user
    # TODO add the following use cases:
        # - Connection to VIP expired during workflow monitoring
        # - "Error 8000": better interpretation
    @staticmethod
    def _handle_vip_error(vip_error: RuntimeError) -> None:
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
                f"Could not communicate with VIP.\n\t'{message}'"
                + "\nRun VipSession.init() with a valid API key to handshake with VIP servers."
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
        raise RuntimeError(interpret)
    # ------------------------------------------------

#######################################################

if __name__=="__main__":
    pass