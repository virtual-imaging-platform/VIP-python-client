# Built-in libraries
from concurrent.futures import ThreadPoolExecutor
from os.path import exists
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
session = requests.Session()

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

# Parallel uploads / downloads are implemented with a multithreading 
# strategy for IO-bound operations. (Multiprocessing would be overkilled
# and involve multiple CPUs from and unknown local machine)

# Maximum number of threads to parallelize
MAX_THREADS = 10
    
# The `request` Session is not thread-safe: 
# must be local to each thread when parallelized. 

# Local object to gather thread-safe variables
thread_local = threading.local()

# Function to create a new Session object when initializing the current thread
def init_thread()  -> requests.Session:
    """Creates a new thread-safe version of the `requests` Session"""
    assert not hasattr(thread_local, "session")
    thread_local.session = new_session()

def download_thread(file: tuple) -> dict :
    """
    Downloads a single file from VIP with a thread-safe session.
    `file` must be in format: (`vip_filename`, `local_filename`).

    Returns True if done, False otherwise.
    """
    # Parameters
    path, where_to_save = file
    url = __PREFIX + 'path' + path + '?action=content'
    # 
    with (
        thread_local.session.get(url, headers=__headers, stream=True) as rq,
        open(where_to_save, 'wb') as out_file
    ):
        # manage_errors(rq)
        try: manage_errors(rq)
        except RuntimeError:
            return path, False
        out_file.write(rq.content)
    return path, True

def download_parallel(files):
    """
    Generator yielding VIP filenames and their success flag as they are downloaded from VIP.

    `files`: iterable of tuples in format (`vip_file`, `local_file`).
    """
    # Threads are run in a context manager to secure their closing
    with ThreadPoolExecutor(
        max_workers = min(MAX_THREADS, len(files)), # Number of threads
        thread_name_prefix = "vip_requests",
        initializer = init_thread  # Method to create a thread-safe `requests` Session
        ) as executor:
        # Transparent connexion between executor.map() and the caller of download_parallel()
        yield from executor.map(download_thread, files)

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
        global __apikey, __headers, session
        # Set the API key
        __apikey = value
        __headers['apikey'] = __apikey
        session = new_session()
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
    rq = session.put(url, headers=__headers)
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
    rq = session.get(url, headers=__headers)
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
    rq = session.delete(url, headers=__headers)
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
    rq = session.put(url, headers=headers, data=data)
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
    rq = session.get(url, headers=__headers, stream=True)
    try:
        manage_errors(rq)
    except RuntimeError:
        return False
    else:
        with open(where_to_save, 'wb') as out_file:
            out_file.write(rq.content)
        return True

################################ EXECUTIONS ###################################
# -----------------------------------------------------------------------------
def list_executions()->list:
    url = __PREFIX + 'executions'
    rq = session.get(url, headers=__headers)
    manage_errors(rq)
    return rq.json()

# -----------------------------------------------------------------------------
def count_executions()->int:
    url = __PREFIX + 'executions/count'
    rq = session.get(url, headers=__headers)
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
    rq = session.post(url, headers=headers, json=data_)
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
    rq = session.get(url, headers=__headers)
    manage_errors(rq)
    return rq.json()

# -----------------------------------------------------------------------------
def is_running(id_exec)->bool:
    info = execution_info(id_exec)
    return info['status'] == 'Running'

# -----------------------------------------------------------------------------
def get_exec_stderr(exec_id) -> str:
    url = __PREFIX + 'executions/' + exec_id + '/stderr'
    rq = session.get(url, headers=__headers)
    manage_errors(rq)
    return rq.text

# -----------------------------------------------------------------------------
def get_exec_stdout(exec_id) -> str:
    url = __PREFIX + 'executions/' + exec_id + '/stdout'
    rq = session.get(url, headers=__headers)
    manage_errors(rq)
    return rq.text

# -----------------------------------------------------------------------------
def get_exec_results(exec_id) -> str:
    url = __PREFIX + 'executions/' + exec_id + '/results'
    rq = session.get(url, headers=__headers)
    manage_errors(rq)
    return rq.json()

# -----------------------------------------------------------------------------
def kill_execution(exec_id, deleteFiles=False) -> bool:
    url = __PREFIX + 'executions/' + exec_id
    if deleteFiles:
        url += '?deleteFiles=true'
    rq = session.delete(url, headers=__headers)
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
    rq = session.get(url, headers=__headers)
    manage_errors(rq)
    return rq.json()

# -----------------------------------------------------------------------------
def pipeline_def(pip_id)->dict:
    url = __PREFIX + 'pipelines/' + pip_id
    rq = session.get(url, headers=__headers)
    manage_errors(rq)
    return rq.json()

################################## OTHER ######################################
# -----------------------------------------------------------------------------
def platform_info()->dict:
    url = __PREFIX + 'platform'
    rq = session.get(url, headers=__headers)
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
    rq = session.post(url, headers=headers, json=data_)
    manage_errors(rq)
    return rq.json()['httpHeaderValue']

###############################################################################
if __name__=='__main__':
    pass

