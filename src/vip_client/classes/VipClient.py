from __future__ import annotations
import json
import os
import re
import time
from contextlib import contextmanager
from pathlib import *

from vip_client.utils import vip

class VipClient():
    """
    Python class to run VIP pipelines on datasets located on VIP servers.

    A single instance allows to run 1 pipeline with 1 parameter set (any number of runs).
    Pipeline runs need at least three inputs:
    - `pipeline_id` (str) Name of the pipeline. 
    - `input_settings` (dict) All parameters needed to run the pipeline.
    - `output_dir` (str | os.PathLike) Path to the VIP directory where pipeline outputs will be stored.

    N.B.: all instance methods require that `VipClient.init()` has been called with a valid API key. 
    See GitHub documentation to get your own VIP API key.
    """

                    ##################
    ################ Class Attributes ##################
                    ##################
    
    # Class name
    __name__ = "VipClient"
    # Default verbose state
    _VERBOSE = True
    # Vip portal
    _VIP_PORTAL = "https://vip.creatis.insa-lyon.fr/"
    # Mail address for support
    _VIP_SUPPORT = "vip-support@creatis.insa-lyon.fr"
    # Regular expression for invalid characters
    _INVALID_CHARS = re.compile(r"[^0-9\.,A-Za-z\-+@/_(): \[\]?&=]")

                    ################
    ################ Public Methods ##################
                    ################

    # Login to VIP
    @classmethod
    def init(cls, api_key="VIP_API_KEY", verbose=True) -> VipClient:
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
        # Display success
        cls._printc()
        cls._printc("----------------------------------")
        cls._printc("| You are communicating with VIP |")
        cls._printc("----------------------------------")
        cls._printc()
    # ------------------------------------------------

                    #################
    ################ Private Methods ################
                    #################

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

    # Function to check invalid characters in some input string
    @classmethod
    def _invalid_chars(cls, value) -> list: 
        """
        Returns a list of invalid characters in `value`.
        Value can be a list or any object convertible to string.
        """
        if isinstance(value, list):
            return sorted(list({v for val in value for v in cls._INVALID_CHARS.findall(str(val))}))
        else:
            return sorted(cls._INVALID_CHARS.findall(str(value)))
    # ------------------------------------------------

    # Function to clean HTML text when loaded from VIP portal
    @staticmethod
    def _clean_html(text: str) -> str:
        """Returns `text` without html tags and newline characters."""
        return re.sub(r'<[^>]+>|\n', '', text)

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