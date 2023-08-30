"""
Historical module implementing all API requests through the `requests` library.
"""

# Author: Timothée Chabat
# Maintainer: Gaël Vila

# Built-in libraries
from concurrent.futures import ThreadPoolExecutor
from os.path import exists
from pathlib import *
import threading
# Third-Party
import requests

########################### VARIABLES & ERRORS ################################
# -----------------------------------------------------------------------------
# API URL
__PREFIX = "https://vip.creatis.insa-lyon.fr/rest/"

# API key
__apikey = None
__headers = {'apikey': __apikey}

# Void `requests` session (inefficient until __api_key is unset)
SESSION = requests.Session() # with retry strategy
SESSION_NO_RETRY = requests.Session() # without retry strategy

# Strategy for retrying requests
retry_strategy = requests.adapters.Retry(
    total = 4, # Retry 3 times at most
    status_forcelist  = [ 
        104,    # ConnectionResetError ?
        500,    # Internal Server Error
        502,    # Bad Gateway or Proxy Error
        503,    # Service Unavailable
        504     # Gateway Time-out
    ],
    backoff_factor = 8 # retries after 0s, 16s, 32s, 64s
)

# Mount a `requests` Session with the API key and retry strategy
def new_session() -> requests.Session:
    """Creates a new `requests` Session with headers and retry strategy"""
    new_session = requests.Session()
    new_session.mount(__PREFIX, requests.adapters.HTTPAdapter(max_retries=retry_strategy))
    new_session.headers.update(__headers)
    return new_session

# Mount a `requests` Session without retry strategy
def new_session_no_retry() -> requests.Session:
    """Creates a new `requests` Session without retry strategy"""
    new_session = requests.Session()
    new_session.headers.update(__headers)
    return new_session

# Parallel downloads are implemented with a multithreading 
# strategy for IO-bound operations.

# Maximum number of threads to parallelize
MAX_THREADS = 10
    
# The `request` Session is not thread-safe: 
# must be local to each thread when parallelized. 

# Local object to gather thread-safe variables
thread_local = threading.local()

# Function to create a new Session object when initializing the current thread
def init_thread()  -> requests.Session:
    """Creates a new thread-safe version of the `requests` Session with a retry strategy"""
    assert not hasattr(thread_local, "session")
    thread_local.session = new_session()

# -----------------------------------------------------------------------------
def setApiKey(value) -> bool:
    """
    Return True is correct apikey, False otherwise.
    Raise an error if an other problems occured 
    """
    url = __PREFIX + 'plateform'
    head_test = {
                 'apikey': value,
                }
    # Send a test request
    rq = requests.put(url, headers=head_test)
    res = detect_errors(rq)
    if res[0]:
        # Error
        if res[1] == 40101:
            return False
        else:
            raise RuntimeError("Error {} from VIP : {}".format(res[1], res[2]))
    else:
        # OK
        global __apikey, __headers, SESSION, SESSION_NO_RETRY
        # Set the API key
        __apikey = value
        __headers['apikey'] = __apikey
        SESSION = new_session()
        SESSION_NO_RETRY = new_session_no_retry()
        return True

# -----------------------------------------------------------------------------
def detect_errors(req)->tuple:
    """
    [0]True if an error, [0]False otherwise
    If True, [1] and [2] are error details.
    """
    if (not 'content-type' in req.headers or
        not req.headers['content-type'].startswith("application/json")):
        return (False,)

    try:
        res = req.json()
    except:
        return (False,)
    else:
        if isinstance(res, dict) and \
        list(res.keys())==['errorCode', 'errorMessage']:
            return (True, res['errorCode'], res['errorMessage'])

    return (False,)

# -----------------------------------------------------------------------------
def manage_errors(req)->None:
    """
    raise an runtime error if the result of a request is an error message

    # TODO: implement better management based on `req.status_code`
    """
    res = detect_errors(req)
    if res[0]:
        raise RuntimeError("Error {} from VIP : {}".format(res[1], res[2]))

################################### PATH ######################################
# -----------------------------------------------------------------------------
def create_dir(path)->bool:
    """
    Return True if done, False otherwise
    """
    url = __PREFIX + 'path' + path
    rq = SESSION.put(url, headers=__headers)
    try:
        manage_errors(rq)
    except RuntimeError:
        return False
    else:
        return True

# -----------------------------------------------------------------------------
def create_dir_smart(path)->str:
    """
    If 'path' already exist, add a number suffix

    'path' should NOT have a '/' at the end
    return a path with the same syntax
    """
    ind = 0
    res_path = path
    while exists(res_path):
        ind += 1
        res_path = path + str(ind)

    create_dir(res_path)
    return res_path

# -----------------------------------------------------------------------------
def _path_action(path, action) -> requests.models.Response:
    """
    Be carefull tho because 'md5' seems to not work.
    Also 'content' is not accepted here, use download() function instead.
    """
    assert action in ['list', 'exists', 'properties', 'md5']
    url = __PREFIX + 'path' + path + '?action=' + action
    rq = SESSION.get(url, headers=__headers)
    manage_errors(rq)
    return rq

# -----------------------------------------------------------------------------
def list_content(path) -> list:
    return _path_action(path, 'list').json()

# -----------------------------------------------------------------------------
def list_directory(path) -> list:
    res = list_content(path)
    return [d for d in res if d['isDirectory'] == True]

# -----------------------------------------------------------------------------
def list_elements(path) -> list:
    res = list_content(path)
    return [e for e in res if e['isDirectory'] != True]

# -----------------------------------------------------------------------------
def exists(path) -> bool:
    return _path_action(path, 'exists').json()['exists']

# -----------------------------------------------------------------------------
def get_path_properties(path) -> dict:
    return _path_action(path, 'properties').json()

# -----------------------------------------------------------------------------
def is_dir(path) -> bool:
    return get_path_properties(path)['isDirectory']

# -----------------------------------------------------------------------------
def delete_path(path)->bool:
    """
    Delete a file or a path (with all its content).
    Return True if done, False otherwise
    """
    url = __PREFIX + 'path' + path
    rq = SESSION.delete(url, headers=__headers)
    try:
        manage_errors(rq)
    except RuntimeError:
        return False
    else:
        return True

# -----------------------------------------------------------------------------
def upload(path, where_to_save) -> bool:
    """
    - `path` : on local computer, the file to upload
    - `where_to_save` : on VIP, something like "/vip/Home/RandomName.ext"

    Return True if done, False otherwise
    """
    url = __PREFIX + 'path' + where_to_save
    headers = {
                'apikey': __apikey,
                'Content-Type': 'application/octet-stream',
              }
    with open(path, 'rb') as fid:
        data = fid.read()
    rq = SESSION.put(url, headers=headers, data=data)
    try:
        manage_errors(rq)
    except RuntimeError:
        return False
    else:
        return True

# -----------------------------------------------------------------------------
def download(path, where_to_save) -> bool :
    """
    Downloads a single file from VIP.
    - `path`: on VIP, something like "/vip/Home/RandomName.ext", content to dl
    - `where_to_save` : on local computer
    """
    # Parse arguments
    url = __PREFIX + 'path' + path + '?action=content'
    rq = SESSION.get(url, headers=__headers, stream=True)
    if rq.status_code != 200:
        return False
    else:
        with open(where_to_save, 'wb') as out_file:
            out_file.write(rq.content)
        return True

# Methods for parallel downloads
    
# Method to downlad data in a thread-safe session
def download_thread(file: tuple) -> tuple :
    """
    Downloads a single file from VIP with a thread-safe session.
    - `file` must be in format: (`vip_filename`, `local_filename`)
    - `vip_filename`, `local_filename` can be strings or os.PathLike objects.

    Returns the Vip path and a success flag.
    """
    # Parameters
    path, where_to_save = map(str, file)
    # URL for request
    url = __PREFIX + 'path' + str(path) + '?action=content'
    # Parallel download
    with (thread_local.session.get(url, headers=__headers, stream=True) as rq,
          open(where_to_save, 'wb') as out_file):
        # TODO: manage HTTP return code
        if rq.status_code != 200:
            return file, False
        else:
            with open(where_to_save, 'wb') as out_file:
                out_file.write(rq.content)
            return file, True
        
def download_parallel(files):
    """
    Downloads files from VIP in parallel.
    - `files`: iterable of tuples in format (`vip_file`, `local_file`) 
    where file paths can be `str` or `os.PathLike` objects; 
    - Yields a filename and a success flag as soon as the file is downloaded from VIP.
    """
    # Threads are run in a context manager to secure their closing
    with ThreadPoolExecutor(
        max_workers = min(MAX_THREADS, len(files)), # Number of threads
        thread_name_prefix = "vip_requests",
        initializer = init_thread  # Method to create a thread-safe `requests` Session
        ) as executor:
        # Transparent connexion between executor.map() and the caller of download_parallel()
        yield from executor.map(download_thread, files)

################################ EXECUTIONS ###################################
# -----------------------------------------------------------------------------
def list_executions()->list:
    url = __PREFIX + 'executions'
    rq = SESSION.get(url, headers=__headers)
    manage_errors(rq)
    return rq.json()

# -----------------------------------------------------------------------------
def count_executions()->int:
    url = __PREFIX + 'executions/count'
    rq = SESSION.get(url, headers=__headers)
    manage_errors(rq)
    return int(rq.text)

# -----------------------------------------------------------------------------
def init_exec(pipeline, name="default", inputValues={}, resultsLocation="/vip/Home") -> str:
    url = __PREFIX + 'executions'
    headers = {
                'apikey': __apikey,
                'Content-Type': 'application/json'
              }
    data_ = {
            "name": name, 
            'pipelineIdentifier': pipeline,
            "inputValues": inputValues,
            "resultsLocation": resultsLocation
           }
    rq = SESSION.post(url, headers=headers, json=data_)
    manage_errors(rq)
    return rq.json()["identifier"]
# -----------------------------------------------------------------------------

def init_exec_without_resultsLocation(pipeline, name="default", inputValues={}) -> str:
    """Initiate executions with "results-directory" in the `inputValues`"""
    url = __PREFIX + 'executions'
    headers = {
                'apikey': __apikey,
                'Content-Type': 'application/json'
              }
    data_ = {
            "name": name, 
            'pipelineIdentifier': pipeline,
            "inputValues": inputValues
           }
    rq = requests.post(url, headers=headers, json=data_)
    manage_errors(rq)
    return rq.json()["identifier"]

# -----------------------------------------------------------------------------
def execution_info(id_exec)->dict:
    url = __PREFIX + 'executions/' + id_exec
    rq = SESSION.get(url, headers=__headers)
    manage_errors(rq)
    return rq.json()

# -----------------------------------------------------------------------------
def is_running(id_exec)->bool:
    info = execution_info(id_exec)
    return info['status'] == 'Running'

# -----------------------------------------------------------------------------
def get_exec_stderr(exec_id) -> str:
    url = __PREFIX + 'executions/' + exec_id + '/stderr'
    rq = SESSION.get(url, headers=__headers)
    manage_errors(rq)
    return rq.text

# -----------------------------------------------------------------------------
def get_exec_stdout(exec_id) -> str:
    url = __PREFIX + 'executions/' + exec_id + '/stdout'
    rq = SESSION.get(url, headers=__headers)
    manage_errors(rq)
    return rq.text

# -----------------------------------------------------------------------------
def get_exec_results(exec_id, timeout: int=None) -> str:
    """
    New version with `timeout` parameter. 
    If `timeout` is set, `requests will make a single try with timeout
    (without the persistent session). 
    """
    url = __PREFIX + 'executions/' + exec_id + '/results'
    try:
        # Use the session without retry strategy
        rq = SESSION_NO_RETRY.get(url, headers=__headers, timeout=timeout)
        # This will throw TimeoutError in case of timeout
    except requests.exceptions.ReadTimeout as e:
        raise TimeoutError(e) # builtin Python error
    manage_errors(rq)
    return rq.json()

# -----------------------------------------------------------------------------
def kill_execution(exec_id, deleteFiles=False) -> bool:
    url = __PREFIX + 'executions/' + exec_id
    if deleteFiles:
        url += '?deleteFiles=true'
    rq = SESSION.delete(url, headers=__headers)
    try:
        manage_errors(rq)
    except RuntimeError:
        return False
    else:
        return True

################################ PIPELINES ####################################
# -----------------------------------------------------------------------------
def list_pipeline()->list:
    url = __PREFIX + 'pipelines'
    rq = SESSION.get(url, headers=__headers)
    manage_errors(rq)
    return rq.json()

# -----------------------------------------------------------------------------
def pipeline_def(pip_id)->dict:
    url = __PREFIX + 'pipelines/' + pip_id
    rq = SESSION.get(url, headers=__headers)
    manage_errors(rq)
    return rq.json()

################################## OTHER ######################################
# -----------------------------------------------------------------------------
def platform_info()->dict:
    url = __PREFIX + 'platform'
    rq = SESSION.get(url, headers=__headers)
    manage_errors(rq)
    return rq.json()

# -----------------------------------------------------------------------------
def get_apikey(username, password)->str:
    """
    username is the email account you used to create your VIP account
    """
    url = __PREFIX + 'authenticate'
    headers = {
                'apikey': __apikey,
                'Content-Type': 'application/json'
              }
    data_ = {
            "username": username, 
            "password": password
           }
    rq = SESSION.post(url, headers=headers, json=data_)
    manage_errors(rq)
    return rq.json()['httpHeaderValue']

###############################################################################
if __name__=='__main__':
    pass

