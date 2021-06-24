import requests
from os.path import join, dirname, exists


########################### VARIABLES & ERRORS ################################
# -----------------------------------------------------------------------------
__PREFIX = "https://vip.creatis.insa-lyon.fr/rest/"
__apikey = None
__headers = {'apikey': __apikey}

path = join(dirname(__file__), 'certif.crt')
if not exists(path):
    __certif = None
else:
    __certif = path
del path

# -----------------------------------------------------------------------------
def setApiKey(value)->bool:
    """
    Return True is correct apikey, False otherwise.
    Raise an error if an other problems occured 
    """
    url = __PREFIX + 'plateform'
    head_test = {
                 'apikey': value,
                }
    rq = requests.put(url, headers=head_test, verify=__certif)
    res = detect_errors(rq)
    if res[0]:
        if res[1] == 40101:
            return False
        else:
            raise RuntimeError("Error {} from VIP : {}".format(res[1], res[2]))
    else:
        global __apikey
        __apikey = value
        __headers['apikey'] = value
        return True

# -----------------------------------------------------------------------------
def setCertifPath(path)->bool:
    """
    TODO : verify if the certif work
    """
    __certif = path
    return True

# -----------------------------------------------------------------------------
def detect_errors(req)->tuple:
    """
    [0]True if an error, [0]False otherwise
    If True, [1] and [2] are error details.
    """
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
    rq = requests.put(url, headers=__headers, verify=__certif)
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
    rq = requests.get(url, headers=__headers, verify=__certif)
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
    rq = requests.delete(url, headers=__headers, verify=__certif)
    try:
        manage_errors(rq)
    except RuntimeError:
        return False
    else:
        return True

# -----------------------------------------------------------------------------
def upload(path, where_to_save)->bool:
    """
    Input:
        - path : on local computer, the file to upload
        - where_to_save : on VIP, something like "/vip/Home/RandomName.ext"

    Return True if done, False otherwise
    """
    url = __PREFIX + 'path' + where_to_save
    headers = {
                'apikey': __apikey,
                'Content-Type': 'application/octet-stream',
              }
    data = open(path, 'rb').read()
    rq = requests.put(url, headers=headers, data=data, verify=__certif)
    try:
        manage_errors(rq)
    except RuntimeError:
        return False
    else:
        return True

# -----------------------------------------------------------------------------
def download(path, where_to_save):
    """
    Input:
        - path: on VIP, something like "/vip/Home/RandomName.ext", content to dl
        - where_to_save : on local computer
    """
    url = __PREFIX + 'path' + path + '?action=content'
    rq = requests.get(url, headers=__headers, stream=True, verify=__certif)
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
    rq = requests.get(url, headers=__headers, verify=__certif)
    manage_errors(rq)
    return rq.json()

# -----------------------------------------------------------------------------
def count_executions()->int:
    url = __PREFIX + 'executions/count'
    rq = requests.get(url, headers=__headers, verify=__certif)
    manage_errors(rq)
    return int(rq.text)

# -----------------------------------------------------------------------------
def init_exec(pipeline, name="default", inputValues={}) -> str:
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
    rq = requests.post(url, headers=headers, json=data_, verify=__certif)
    manage_errors(rq)
    return rq.json()["identifier"]

# -----------------------------------------------------------------------------
def execution_info(id_exec)->dict:
    url = __PREFIX + 'executions/' + id_exec
    rq = requests.get(url, headers=__headers, verify=__certif)
    manage_errors(rq)
    return rq.json()

# -----------------------------------------------------------------------------
def is_running(id_exec)->bool:
    info = execution_info(id_exec)
    return info['status'] == 'Running'

# -----------------------------------------------------------------------------
def get_exec_stderr(exec_id) -> str:
    url = __PREFIX + 'executions/' + exec_id + '/stderr'
    rq = requests.get(url, headers=__headers, verify=__certif)
    manage_errors(rq)
    return rq.text

# -----------------------------------------------------------------------------
def get_exec_stdout(exec_id) -> str:
    url = __PREFIX + 'executions/' + exec_id + '/stdout'
    rq = requests.get(url, headers=__headers, verify=__certif)
    manage_errors(rq)
    return rq.text

# -----------------------------------------------------------------------------
def get_exec_results(exec_id) -> str:
    url = __PREFIX + 'executions/' + exec_id + '/results'
    rq = requests.get(url, headers=__headers, verify=__certif)
    manage_errors(rq)
    return rq.json()

# -----------------------------------------------------------------------------
def kill_execution(exec_id, deleteFiles=False) -> bool:
    url = __PREFIX + 'executions/' + exec_id
    if deleteFiles:
        url += '?deleteFiles=true'
    rq = requests.delete(url, headers=__headers, verify=__certif)
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
    rq = requests.get(url, headers=__headers, verify=__certif)
    manage_errors(rq)
    return rq.json()

# -----------------------------------------------------------------------------
def pipeline_def(pip_id)->dict:
    url = __PREFIX + 'pipelines/' + pip_id
    rq = requests.get(url, headers=__headers, verify=__certif)
    manage_errors(rq)
    return rq.json()

################################## OTHER ######################################
# -----------------------------------------------------------------------------
def platform_info()->dict:
    url = __PREFIX + 'platform'
    rq = requests.get(url, headers=__headers, verify=__certif)
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
    rq = requests.post(url, headers=headers, json=data_, verify=__certif)
    manage_errors(rq)
    return rq.json()['httpHeaderValue']

###############################################################################
if __name__=='__main__':
    pass
