from __future__ import annotations
import json
import os
import re
import tarfile
import time
from contextlib import contextmanager
from pathlib import *

import src.vip as vip

class VipLoader():
    """
    Python class to run VIP pipelines on datasets located on VIP servers.

    A single instance allows to run 1 pipeline with 1 parameter set (any number of runs).
    Pipeline runs need at least three inputs:
    - `pipeline_id` (str) Name of the pipeline. 
    - `input_settings` (dict) All parameters needed to run the pipeline.
    - `output_dir` (str | os.PathLike) Path to the VIP directory where pipeline outputs will be stored.

    N.B.: all instance methods require that `VipLoader.init()` has been called with a valid API key. 
    See GitHub documentation to get your own VIP API key.
    """

                    ##################
    ################ Class Attributes ##################
                    ##################
    
    # Class name
    __name__ = "VipLoader"
    # Default verbose state
    _VERBOSE = True
    # Default location for VIP inputs/outputs (can be different for subclasses)
    _SERVER_NAME = "vip"
    # Prefix that defines a path from VIP
    _SERVER_PATH_PREFIX = "/vip"
    # Vip portal
    _VIP_PORTAL = "https://vip.creatis.insa-lyon.fr/"
    # Mail address for support
    _VIP_SUPPORT = "vip-support@creatis.insa-lyon.fr"
    # Regular expression for invalid characters
    _INVALID_CHARS = re.compile(r"[^0-9\.,A-Za-z\-+@/_(): \[\]?&=]")

                    ################
    ################ Public Methods ##################
                    ################

    #################################################
    # ($A) Manage a session from start to finish
    #################################################

    # ($A.1) Login to VIP
    @classmethod
    def init(cls, api_key="VIP_API_KEY", verbose=True, **kwargs) -> VipLoader:
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
        # Return a VipLoader instance for method cascading
        return cls(verbose=(verbose and kwargs), **kwargs)
    # ------------------------------------------------

                    #################
    ################ Private Methods ################
                    #################
    
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
    # ($A) Manage a session from start to finish
    #################################################

    # ($A.2/A.5) Upload (/download) data on (/from) VIP Servers
    ###########################################################

    # Function to upload all files from a local directory
    @classmethod
    def _upload_dir(cls, local_path: Path, vip_path: PurePosixPath) -> list:
        """
        Uploads all files in `local_path` to `vip_path` (if needed).
        Displays what it does if `cls._VERBOSE` is True.
        Returns a list of files which failed to be uploaded on VIP.
        """
        # Scan the local directory
        assert cls._exists(local_path, location='local'), f"{local_path} does not exist."
        # First display
        cls._print(f"Cloning: {local_path} ", end="... ")
        # Scan the distant directory and look for files to upload
        if cls._mkdirs(vip_path, location="vip"):
            # The distant directory did not exist before call
            # -> upload all the data (no scan to save time)
            files_to_upload = [
                elem for elem in local_path.iterdir()
                if elem.is_file()
            ]
            cls._print("(Created on VIP)")
            if files_to_upload:
                cls._print(f"\t{len(files_to_upload)} files to upload.")
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
                cls._print(f"\n\tVIP clone already exists and will be updated with {len(files_to_upload)} files.")
            else:
                cls._print("Already on VIP.")
        # Upload the files
        nFile = 0
        failures = []
        for local_file in files_to_upload :
            nFile+=1
            # Get the file size (if possible)
            try: size = f"{local_file.stat().st_size/(1<<20):,.1f}MB"
            except: size = "unknown size"
            # Display the current file
            cls._print(f"\t[{nFile}/{len(files_to_upload)}] Uploading file: {local_file.name} ({size}) ...", end=" ")
            # Upload the file on VIP
            vip_file = vip_path/local_file.name # file path on VIP
            if cls._upload_file(local_path=local_file, vip_path=vip_file):
                # Upload was successful
                cls._print("Done.")
            else:
                # Update display
                cls._print(f"\n(!) Something went wrong during the upload.")
                # Update missing files
                failures.append(str(local_file))
        # Look for sub-directories
        subdirs = [
            elem for elem in local_path.iterdir() 
            if elem.is_dir()
        ]
        # Recurse this function over sub-directories
        for subdir in subdirs:
            failures += cls._upload_dir(
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
        try:
            done = vip.upload(str(local_path), str(vip_path))
        except RuntimeError as vip_error:
            cls._handle_vip_error(vip_error)
        # Return
        return done
    # ------------------------------------------------   

    # Function to upload all files from a local directory
    @classmethod
    def _download_dir(cls, vip_path: PurePosixPath, local_path: Path) -> list:
        """
        Download all files from `vip_path` to `local_path` (if needed).
        Displays what it does if `cls._VERBOSE` is True.
        Returns a list of files which failed to be downloaded from VIP.
        """
        # Scan the VIP directory
        assert cls._exists(vip_path, location='vip'), f"{vip_path} does not exist."
        # First display
        cls._print(f"Cloning: {local_path} ", end="... ")
        # Scan the distant directory and look for files to upload
        if cls._mkdirs(local_path, location="local"):
            # The local directory did not exist before call
            # -> download all the data (no scan to save time)
            files_to_download = vip.list_elements(str(vip_path))
            cls._print("(Created on VIP)")
            if files_to_download:
                cls._print(f"\t{len(files_to_download)} files to upload.")
        else: # The distant directory already exists
            # Scan it to check if there are more files to upload
            vip_filenames = {
                PurePosixPath(element["path"]).name
                for element in vip.list_elements(str(vip_path))
            }
            # Get the files to upload
            files_to_download = [
                elem for elem in local_path.iterdir()
                if elem.is_file() and (elem.name not in vip_filenames)
            ]
            # Update the display
            if files_to_download: 
                cls._print(f"\n\tVIP clone already exists and will be updated with {len(files_to_download)} files.")
            else:
                cls._print("Already on VIP.")
        # Upload the files
        nFile = 0
        failures = []
        for local_file in files_to_download :
            nFile+=1
            # Get the file size (if possible)
            try: size = f"{local_file.stat().st_size/(1<<20):,.1f}MB"
            except: size = "unknown size"
            # Display the current file
            cls._print(f"\t[{nFile}/{len(files_to_download)}] Uploading file: {local_file.name} ({size}) ...", end=" ")
            # Upload the file on VIP
            vip_file = vip_path/local_file.name # file path on VIP
            if cls._upload_file(local_path=local_file, vip_path=vip_file):
                # Upload was successful
                cls._print("Done.")
            else:
                # Update display
                cls._print(f"\n(!) Something went wrong during the upload.")
                # Update missing files
                failures.append(str(local_file))
        # Look for sub-directories
        subdirs = [
            elem for elem in local_path.iterdir() 
            if elem.is_dir()
        ]
        # Recurse this function over sub-directories
        for subdir in subdirs:
            failures += cls._upload_dir(
                local_path=subdir,
                vip_path=vip_path/subdir.name
            )
        # Return the list of failures
        return failures
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
            cls._handle_vip_error(vip_error)
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

    ##################################################
    # Context managers
    ##################################################

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
   
    # Function to assert the input contains a certain type
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
    def _invalid_chars(cls, value) -> list: 
        """
        Returns a list of invalid characters in `value`.
        """
        if isinstance(value, list):
            return sorted(list({v for val in value for v in cls._INVALID_CHARS.findall(str(val))}))
        else:
            return sorted(cls._INVALID_CHARS.findall(str(value)))
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

    # Function to clean HTML text when loaded from VIP portal
    @staticmethod
    def _clean_html(text: str) -> str:
        """Returns `text` without html tags and newline characters."""
        return re.sub(r'<[^>]+>|\n', '', text)

    # ($D.3) Interpret common API exceptions
    ########################################

    ########################################
    # SESSION LOGS & USER VIEW
    ########################################

    @classmethod
    # Interface to print logs from class methods
    def _printc(cls, *args, **kwargs) -> None:
        """
        Print logs from class methods only when cls._VERBOSE is True.
        """
        if cls._VERBOSE:
            print(*args, **kwargs)
    # ------------------------------------------------

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