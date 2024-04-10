import io
import pytest
from pathlib import *

import pytest_mock
from src.vip_client.utils import vip
from src.vip_client.classes import VipCI


def mock_vip_api(mocker, pipeline_id):
    
    def fake_pathlib_open(mode='r', buffering=-1, encoding=None, errors=None, newline=None):
        return io.open('tmp_data.json', mode, buffering, encoding, errors, newline)
    
    def fake_list_pipeline():
        return [
            {'identifier': 'LCModel/0.1', 'name': 'LCModel', 'description': None, 
            'version': '0.1', 'parameters': [], 'canExecute': True},
            {'identifier': 'CQUEST/0.3', 'name': 'LCModel', 'description': None, 
            'version': '0.1', 'parameters': [], 'canExecute': True}
        ]
    
    def fake_set_api_key(api_key):
        return True if api_key == "FAKE_KEY" else False

    
    def fake_pipeline_def(pipeline):
        return {
            'identifier': pipeline_id, 
                'name': 'LCModel', 
                'description': 'MR spectrosocpy signal quantification software', 
                'version': '0.1', 
                'parameters': [
                    {
                        'name': 'zipped_folder', 
                        'type': 'File', 
                        'defaultValue': '$input.getDefaultValue()', 
                        'description': 'Archive containing all metabolite & macromolecules in .RAW format', 
                        'isOptional': False, 
                        'isReturnedValue': False
                    }, 
                    {
                        'name': 'basis_file', 
                        'type': 'File', 
                        'defaultValue': '$input.getDefaultValue()', 
                        'description': "Text file with extension '.basis' containing information & prior ...", 
                        'isOptional': False, 
                        'isReturnedValue': False
                    }, 
                    {
                        'name': 'signal_file', 
                        'type': 'File', 
                        'defaultValue': '$input.getDefaultValue()', 
                        'description': "Text file with extension '.RAW' containing the signal to quantify", 
                        'isOptional': False, 
                        'isReturnedValue': False
                    }, 
                    {
                        'name': 'control_file', 
                        'type': 'File', 
                        'defaultValue': '$input.getDefaultValue()', 
                        'description': "Text file with extension '.control' setting up constraints, options and prior knowledge used in LCModel algorithm", 
                        'isOptional': False, 
                        'isReturnedValue': False
                    }, 
                    {
                        'name': 'script_file', 
                        'type': 'File', 
                        'defaultValue': '/vip/ReproVIP (group)/LCModel/run-lcmodel.sh', 
                        'description': 'Script lauching lcmodel', 
                        'isOptional': False, 'isReturnedValue': False
                    }
                ], 
                'canExecute': True
            }
    
    def fake_init_exec(pipeline, name, inputValues, resultsLocation):
        return 'workflow-XXXXXX'
    
    def fake_execution_info(workflow_id):
        return {'status': 'Finished', 'returnedFiles': [], 'startDate': 0}
    
    mocker.patch("vip_client.utils.vip.exists").return_value = True
    mocker.patch("pathlib.Path.exists").return_value = True
    mocker.patch("vip_client.utils.vip.upload").return_value = True
    mocker.patch("vip_client.utils.vip.download").return_value = True
    mocker.patch("os.unlink").return_value = True
    mocker.patch("pathlib.Path.unlink").return_value = True
    mocker.patch("pathlib.Path.open").side_effect = fake_pathlib_open
    mocker.patch("vip_client.utils.vip.pipeline_def").side_effect = fake_pipeline_def
    mocker.patch("vip_client.utils.vip.list_pipeline").side_effect = fake_list_pipeline
    mocker.patch("vip_client.utils.vip.setApiKey").side_effect = fake_set_api_key
    mocker.patch("vip_client.utils.vip.init_exec").side_effect = fake_init_exec
    mocker.patch("vip_client.utils.vip.execution_info").side_effect = fake_execution_info

class FakeGirderClient():
    
    pipeline_id = "LCModel/0.1"
    def __init__(self, apiUrl):
        pass
    def authenticate(self, apiKey):
        return True
    
    def resourceLookup(self, path):
        return {'_id': 'fake_id', '_modelType': 'folder'}
    
    def createFolder(self, parentId, name, reuseExisting=True, **kwargs):
        return {'_id': 'fake_id'}
    
    def addMetadataToFolder(self, folderId, metadata):
        return True
    
    def getFolder(cls, folderId):
        print("GUTS: ", cls.pipeline_id)
        metadata = {
            'input_settings': {
            'zipped_folder': 'fake_value', 
            'basis_file': 'fake_value', 
            'signal_file': ['fake_value', 'fake_value'], 
            'control_file': ['fake_value']},
            "pipeline_id": cls.pipeline_id,
            'session_name': 'test-VipLauncher', 
            'workflows': {}, 
            "vip_output_dir": "/vip/Home/test-VipLauncher/OUTPUTS"
        }
        return {'_id': 'fake_id', 'meta': metadata}
    
    def get(self, path):
        return {'_id': 'fake_id'}
    
    def listFiles(self, folderId):
        return [{'_id': 'fake_id'}]
    
    def listItem(self, folderId):
        return {'_id': 'fake_id'}
    
    @classmethod
    def set_pipeline_id(cls, pipeline_id):
        print("GRIFITH: ", pipeline_id)
        cls.pipeline_id = pipeline_id


def mock_girder_client(mocker):
    mocker.patch("girder_client.GirderClient", FakeGirderClient)


def get_properties(obj) -> dict:
    """
    Get session properties as they should be returned by the getter functions
    """
    # Function to parse a single element
    def get_element(element):
        if isinstance(element, dict):
            return {key: get_element(value) for key, value in element.items()}
        elif isinstance(element, list):
            return [get_element(value) for value in element]
        elif element is None:
            return None
        else:
            return str(element)
    # Return
    return {prop: get_element(value) for prop, value in obj.input_properties.items()}

@pytest.fixture(scope="function", autouse=True)
def setup_teardown_vip_launcher(request, mocker):
    # Mock the VIP API
    mock_vip_api(mocker, "LCModel/0.1")
    # Mock the Girder Client
    mock_girder_client(mocker)

    # Create a buffer file for the backup
    with open('tmp_data.json', 'w') as f:
        f.write('{}')
    
    # Setup code before running the tests in the class
    print("Handshake with VIP")
    VipCI.init(vip_key="FAKE_KEY", girder_key="FAKE_KEY")
    print("Setup done")

@pytest.fixture(scope="function", autouse=True)
def cleanup():
    # Teardown code after running each test function
    yield
    # Remove the buffer file
    try:
        Path('tmp_data.json').unlink()
    except FileNotFoundError:
        pass


@pytest.mark.parametrize(
    "nb_runs, pipeline_id",
    [
        (1, "LCModel/0.1"),
        (2, "CQUEST/0.3"),
        (3, "LCModel/0.1")
    ]
)
def test_run_and_finish(mocker, nb_runs, pipeline_id):

    FakeGirderClient.set_pipeline_id(pipeline_id)
    wf_counter = 0
    
    def fake_init_exec(pipeline, name, inputValues, resultsLocation):
        nonlocal wf_counter
        wf_counter += 1
        return f'workflow-{wf_counter}'
    
    # Re patch the init_exec function to update the workflow counter
    mocker.patch("vip_client.utils.vip.init_exec").side_effect = fake_init_exec
    
    # Launch a Full Session Run
    s = VipCI()
    s.pipeline_id = pipeline_id
    s.output_dir = PurePosixPath("/vip/Home/test-VipLauncher/OUTPUTS")
    s.input_settings = {
        "zipped_folder": 'fake_value',
        "basis_file": 'fake_value',
        "signal_file": ['fake_value', 'fake_value'],
        "control_file": ['fake_value']
    }
    s.run_session(nb_runs=nb_runs)
    # Check the Results
    assert s.workflows
    assert len(s.workflows) == nb_runs
    for wid in s.workflows:
        assert s.workflows[wid]["status"] == "Finished"
    assert s.pipeline_id == pipeline_id

@pytest.mark.parametrize(
    "backup_location, input_settings, pipeline_id, output_dir",
    [
        ('girder', {
            "zipped_folder": 'fake_value1',
            "basis_file": 'fake_value2',
            "signal_file": ['fake_value3', 'fake_value4'],
            "control_file": ['fake_value5']
        }, "LCModel/0.1", PurePosixPath("/vip/Home/test-VipLauncher/OUTPUTS"),
        ),
        (None, {
            "zipped_folder": None,
            "basis_file": None,
            "signal_file": None,
            "control_file": None
        }, "LCModel/0.1", PurePosixPath("/vip/Home/test-VipLauncher/OUTPUTS"),
        ),
        ('girder', {
            "zipped_folder": 'different_value1',
            "basis_file": 'different_value2',
            "signal_file": ['different_value3', 'different_value4'],
            "control_file": ['different_value5']
        }, "LCModel/0.1", PurePosixPath("/vip/Home/test-VipLauncher/OUTPUTS"),
        )
    ]
)
def test_backup(mocker, backup_location, input_settings, pipeline_id, output_dir):

    VipCI._BACKUP_LOCATION = backup_location
    # Return if backup is disabled
    if VipCI._BACKUP_LOCATION is None:
        return
    # Create session
    s1 = VipCI()
    s1.input_settings = input_settings
    s1.pipeline_id = pipeline_id
    s1.output_dir = output_dir
    # Backup
    s1._save()
    # Load backup
    s2 = VipCI(output_dir=s1.output_dir)
    # Check parameters
    assert s2.input_settings == s1.input_settings
    assert s2.pipeline_id == s1.pipeline_id
    assert s2.output_dir == s1.output_dir
    assert s2.workflows == s1.workflows


def test_properties_interface(mocker):

    VipCI._BACKUP_LOCATION = "girder"

    # Copy the first session
    s = VipCI()
    s.input_settings = {
        "zipped_folder": 'fake_value1',
        "basis_file": 'fake_value2',
        "signal_file": ['fake_value3', 'fake_value4'],
        "control_file": ['fake_value5']
    }
    # Backup the inputs
    backup = s.input_settings
    # Run a subtest for each property
    for prop in s.input_settings:
        setattr(s, prop, None) # Calls deleter
        assert getattr(s, prop) is None # Public attribute must be None
        assert not s._is_defined("_" + prop) # Private attribute must be unset
        setattr(s, prop, backup[prop]) # Reset
    # Test correct reset
    for key, value in s.input_settings.items():
        assert getattr(s, key) == value
