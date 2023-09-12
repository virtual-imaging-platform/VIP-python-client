from __future__ import annotations
import os
import tarfile
from pathlib import *

from vip_client.utils import vip
from vip_client.classes.VipClient import VipClient

class VipLoader(VipClient):
    """
    Python class to upload / download files to / from VIP servers.
    WORK IN PROGRESS

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
    # List of known directory contents
    _VIP_TREE = {}

                    ################
    ################ Public Methods ##################
                    ################

    @classmethod
    def list_dir(cls, vip_path: PurePosixPath) -> list[str]:
        """
        Returns a list of directories under `vip_path` [str or os.PathLike].
        """
        return [
            PurePosixPath(element["path"]).name
            for element in cls._list_dir_vip(PurePosixPath(vip_path), update=True)
        ]

    @classmethod
    def download_dir(cls, vip_path, local_path, unzip=True):
        """
        Download all files from `vip_path` to `local_path` (if needed).
        Displays what it does if `cls._VERBOSE` is True.
        Returns a dictionary of failed downloads.
        """
        cls._printc("Recursive download from:", vip_path)
        # Path-ify
        vip_path = PurePosixPath(vip_path)
        local_path = Path(local_path)
        # Assert folder existence on VIP
        if not cls._exists(vip_path, location='vip'):
            raise FileNotFoundError("Folder does not exist on VIP.")
        # Scan the distant and local directories and get a list of files to download
        cls._printc("\nCloning the distant folder tree")
        cls._printc("-------------------------------")
        files_to_download = cls._init_download_dir(vip_path, local_path)
        cls._printc("-------------------------------")
        cls._printc("Done.")
        # Download the files from VIP servers & keep track of the failures
        cls._printc("\nParallel download of the distant files")
        cls._printc("--------------------------------------")
        failures = cls._download_parallel(files_to_download, unzip) 
        cls._printc("--------------------------------------")
        cls._printc("End of parallel downloads\n")
        if not failures :
            return
        # Retry in case of failure
        cls._printc(len(failures), "files could not be downloaded from VIP.")
        cls._printc("\nGiving a second try")
        cls._printc("---------------------")
        failures = cls._download_parallel(failures, unzip)
        cls._printc("---------------------")
        cls._printc("End of the process.")
        if failures :
            cls._printc("The following files could not be downloaded from VIP:", end="\n\t")
            cls._printc("\n\t".join([str(file) for file, _ in failures]))
    # ------------------------------------------------

    
                    #################
    ################ Private Methods ################
                    #################

    @classmethod
    def _list_content_vip(cls, vip_path: PurePosixPath, update=True) -> list[dict]:
        """
        Updates `cls._VIP_TREE` with the content of `vip_path` on VIP servers. 
        """
        if update or (vip_path not in cls._VIP_TREE):
            cls._VIP_TREE[vip_path] = vip.list_content(str(vip_path))
        return cls._VIP_TREE[vip_path]
    # ------------------------------------------------

    @classmethod
    def _list_files_vip(cls, vip_path: PurePosixPath, update=True) -> list[dict]:
        return [
            element
            for element in cls._list_content_vip(vip_path, update)
            if element['exists'] and not element['isDirectory']
        ]
    # ------------------------------------------------
    
    @classmethod
    def _list_dir_vip(cls, vip_path: PurePosixPath, update=True) -> list[dict]:
        return [
            element
            for element in cls._list_content_vip(vip_path, update)
            if element['exists'] and element['isDirectory']
        ]
    # ------------------------------------------------
    
    #########################
    # Methods to be optimized
    #########################

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

    @classmethod
    def _init_download_dir(cls, vip_path: PurePosixPath, local_path: Path) -> dict:
        """
        Copy the folder tree under `vip_path` to `local_path`

        Returns a dictionary of files within `vip_path` that are not in `local_paths`.
        Dictionary keys: (vip_path, local_path).
        Dictionary values: file metadata.
        """ 
        # First display
        cls._printc(f"{local_path} : ", end="")
        # Scan the current VIP directory
        cls._list_content_vip(vip_path)
        # Look for files
        all_files = cls._list_files_vip(vip_path, update=False)
        # Scan the local directory and look for files to download
        if cls._mkdirs(local_path, location="local"):
            # The local directory did not exist before call
            cls._printc("Created.")
            # -> download all the files (no scan to save time)
        else: 
            # The local directory already exists
            cls._printc("Already there.")
            # Scan it to check if there are more files to download
            local_filenames = {
                elem.name for elem in local_path.iterdir() if elem.exists()
            }
            # Get the files to download
            all_files = [ 
                element for element in all_files 
                if PurePosixPath(element["path"]).name not in local_filenames
            ]
        # Return files to download as a dictionary
        files_to_download = {}
        for file in all_files:
            # Dict key: VIP & local paths
            file_vip_path = PurePosixPath(file["path"])
            file_local_path = local_path / file_vip_path.name
            files_to_download[(file_vip_path, file_local_path)] = {
                # Dict value: Metadata
                key: value for key, value in file.items() if key!="path"
            }
        # Recurse this function over sub-directories
        for subdir in cls._list_dir_vip(vip_path, update=False):
            subdir_path = PurePosixPath(subdir["path"])
            # Scan the subdirectory
            new_files = cls._init_download_dir(
                vip_path = subdir_path,
                local_path = local_path / subdir_path.name,
            )
            # Update the list of files to download
            files_to_download.update(new_files)
        return files_to_download
    # ------------------------------------------------

    # Method do download files using parallel threads
    @classmethod
    def _download_parallel(cls, files_to_download: dict, unzip: bool):
        """
        Downloads files from VIP using parallel threads.
        - `files_to_download`: Dictionnary with key: (vip_path, local_path) and value: metadata.
        - `unzip`: if True, extracts the tarballs inplace after the download.

        Returns a list of failed downloads.
        """
        # Copy the input
        files_to_download = files_to_download.copy()
        # Return if there is no file to download
        if not files_to_download:
            cls._printc("No file to download.")
            return files_to_download
        # Check the amount of data
        try:    total_size = "%.1fMB" % sum([file['size']/(1<<20) for file in files_to_download.values()])
        except: total_size = "unknown"
        # Display
        cls._printc(f"Downloading {len(files_to_download)} file(s) (total size: {total_size})...")
        # Sort the files to download by size
        try:
            file_list = sorted(files_to_download.keys(), key=lambda file: files_to_download[file]["size"])
        except: 
            file_list = list(files_to_download)
        # Download the files from VIP servers
        nFile = 0 
        nb_files = len(files_to_download)
        for file, done in vip.download_parallel(file_list):
            nFile += 1
            # Get informations about the new file 
            vip_path, local_path = file
            file_info = files_to_download[file]
            file_size = "[%.1fMB]" % (file_info["size"]/(1<<20)) if "size" in file_info else ""
            if done: 
                # Remove file from the list
                file_info = files_to_download.pop(file)
                # Display success
                cls._printc(f"- [{nFile}/{nb_files}] DONE:", local_path, file_size, flush=True)
                # If the output is a tarball, extract the files and delete the tarball
                if unzip and tarfile.is_tarfile(local_path):
                    cls._printc("\tExtracting archive ...", end=" ")
                    if cls._extract_tarball(local_path):
                        cls._printc("Done.") # Display success
                    else:
                        cls._printc("Extraction failed.") # Display failure
            else: 
                # Display failure
                cls._printc(f"- [{nFile}/{nb_files}] FAILED:", vip_path, file_size, flush=True)
        # Return failed downloads
        return files_to_download
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


#######################################################

if __name__=="__main__":
    pass
    