from __future__ import annotations
import os
import tarfile
from pathlib import *

from vip_client.utils import vip
from vip_client.classes.VipClient import VipClient

class VipLoader(VipClient):
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

                    ################
    ################ Public Methods ##################
                    ################

    @classmethod
    def upload_dir():
        pass

    @staticmethod
    def _list_files(vip_path: PurePosixPath) -> PurePosixPath:
        return [
            PurePosixPath(element["path"])
            for element in vip.list_elements(str(vip_path))
        ]
    
    @staticmethod
    def _list_dir(vip_path: PurePosixPath) -> PurePosixPath:
        return [
            PurePosixPath(element["path"])
            for element in vip.list_directory(str(vip_path))
        ]


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
        cls._printc(f"Cloning: {local_path} ", end="... ")
        # Scan the distant directory and look for files to upload
        if cls._mkdirs(vip_path, location="vip"):
            # The distant directory did not exist before call
            # -> upload all the data (no scan to save time)
            files_to_upload = [
                elem for elem in local_path.iterdir()
                if elem.is_file()
            ]
            cls._printc("(Created on VIP)")
            if files_to_upload:
                cls._printc(f"\t{len(files_to_upload)} file(s) to upload.")
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
                cls._printc(f"\n\tVIP clone already exists and will be updated with {len(files_to_upload)} file(s).")
            else:
                cls._printc("Already on VIP.")
        # Upload the files
        nFile = 0
        failures = []
        for local_file in files_to_upload :
            nFile+=1
            # Get the file size (if possible)
            try: size = f"{local_file.stat().st_size/(1<<20):,.1f}MB"
            except: size = "unknown size"
            # Display the current file
            cls._printc(f"\t[{nFile}/{len(files_to_upload)}] Uploading file: {local_file.name} ({size}) ...", end=" ")
            # Upload the file on VIP
            vip_file = vip_path/local_file.name # file path on VIP
            if cls._upload_file(local_path=local_file, vip_path=vip_file):
                # Upload was successful
                cls._printc("Done.")
            else:
                # Update display
                cls._printc(f"\n(!) Something went wrong during the upload.")
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
            return vip.upload(str(local_path), str(vip_path))
        except RuntimeError as vip_error:
            cls._handle_vip_error(vip_error)
    # ------------------------------------------------   

    # Function to upload all files from a local directory
    @classmethod
    def _download_dir(cls, vip_path: PurePosixPath, local_path: Path, unzip=True) -> list:
        """
        Download all files from `vip_path` to `local_path` (if needed).
        Displays what it does if `cls._VERBOSE` is True.
        Returns a list of files which failed to be downloaded from VIP.
        """
        # First display
        cls._printc(f"Folder: {local_path} ", end="... ")
        # Scan the VIP directory
        assert cls._exists(vip_path, location='vip'), f"{vip_path} does not exist."
        all_content = vip.list_content(str(vip_path))
        # Look for files
        all_files = [ 
            element for element in all_content 
            if not element["isDirectory"] and element["exists"]
        ]
        # Scan the distant directory and look for files to upload
        if cls._mkdirs(local_path, location="local"):
            # The local directory did not exist before call
            # -> download all the data (no scan to save time)
            files_to_download = all_files
            cls._printc("(Created locally)")
            if files_to_download:
                cls._printc(f"\t{len(files_to_download)} file(s) to download.")
        else: # The local directory already exists
            # Scan it to check if there are more files to download
            local_filenames = {
                elem.name for elem in local_path.iterdir() if elem.exists()
            }
            # Get the files to download
            files_to_download = [ 
                element for element in all_files 
                if PurePosixPath(element["path"]).name not in local_filenames
            ]
            # Update the display
            if files_to_download: 
                cls._printc(f"\n\tDirectory already exists and will be updated with {len(files_to_download)} file(s).")
            else:
                cls._printc("Already there.")
        # Upload the files
        nFile = 0
        failures = []
        for vip_file in files_to_download :
            nFile+=1
            # Get the file size (if possible)
            if "size" in vip_file: 
                size = f"{vip_file['size']/(1<<20):,.1f}MB"
            else:
                size = "size unknown"
            # Get the path
            vip_file_path = PurePosixPath(vip_file["path"])
            # Display the current file
            cls._printc(f"\t[{nFile}/{len(files_to_download)}] Downloading file: {vip_file_path.name} ({size}) ...", end=" ")
            # Download the file from VIP
            local_file = local_path / vip_file_path.name # Local file path
            if cls._download_file(vip_path=vip_file_path, local_path=local_file):
                # Upload was successful
                cls._printc("Done.")
                # If the output is a tarball, extract the files and delete the tarball
                if unzip and ("mimeType" in vip_file) and (vip_file["mimeType"]=="application/gzip") and tarfile.is_tarfile(local_file):
                    cls._printc("\t\tExtracting archive content ...", end=" ")
                    if cls._extract_tarball(local_file):
                        cls._printc("Done.") # Display success
                    else:
                        cls._printc("Extraction failed.") # Display failure
            else:
                # Update display
                cls._printc(f"\n(!) Something went wrong during the download.")
                # Update missing files
                failures.append(str(vip_file_path))
        # Look for sub-directories
        subdirs = [ 
            PurePosixPath(element["path"]) for element in all_content 
            if element["isDirectory"] and element["exists"]
        ]
        # Recurse this function over sub-directories
        for subdir in subdirs:
            failures += cls._download_dir(
                vip_path = subdir,
                local_path = local_path / subdir.name
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
        # Download (file existence on VIP is not checked to save time)
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
        if success: # Remove the archive
            os.remove(archive)
        else: # Rename the archive
            os.rename(archive, local_file)
        # Return the flag
        return success
    # ------------------------------------------------


#######################################################

if __name__=="__main__":
    pass
    # from VipLoader import VipLoader
    # from pathlib import *
    # VipLoader.init()
    # VipLoader._download_dir(vip_path=PurePosixPath("/vip/Home/test-VipLauncher"), local_path=Path("Here."))