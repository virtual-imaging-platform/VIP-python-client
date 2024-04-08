import io
import pytest
import unittest
from pathlib import *

import pytest_mock
from src.vip_client.utils import vip
from src.vip_client.classes import VipLauncher

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
    # Create a buffer file for the backup
    with open('tmp_data.json', 'w') as f:
        f.write('{}')
        print("Trying to create the buffer file")
    # Mock the VIP API
    mocked_list_pipeline = mocker.patch("vip_client.utils.vip.list_pipeline")
    mocked_list_pipeline.return_value = [
        {'identifier': 'LCModel/0.1', 'name': 'LCModel', 'description': None, 
         'version': '0.1', 'parameters': [], 'canExecute': True},
        {'identifier': 'CQUEST/0.3', 'name': 'LCModel', 'description': None, 
        'version': '0.1', 'parameters': [], 'canExecute': True}
    ]

    def fake_set_api_key(api_key):
        return True if api_key == "FAKE_KEY" else False

    mocked_set_api_key = mocker.patch("vip_client.utils.vip.setApiKey")
    mocked_set_api_key.side_effect = fake_set_api_key
    
    # Setup code before running the tests in the class
    print("Handshake with VIP")
    VipLauncher.init(api_key="FAKE_KEY")
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

    removed = False

    def fake_exists(path):
        if path == '/vip/Home/test-VipLauncher/OUTPUTS':
            return True
        if path == 'fake_value' and not removed:
            return True
        return False
    
    def fake_pipeline_def(pipeline):
        return {'identifier': pipeline_id, 'name': 'LCModel', 'description': 'MR spectrosocpy signal quantification software', 'version': '0.1', 'parameters': [{'name': 'zipped_folder', 'type': 'File', 'defaultValue': '$input.getDefaultValue()', 'description': 'Archive containing all metabolite & macromolecules in .RAW format', 'isOptional': False, 'isReturnedValue': False}, {'name': 'basis_file', 'type': 'File', 'defaultValue': '$input.getDefaultValue()', 'description': "Text file with extension '.basis' containing information & prior knowledge about the metabolites used for signal fit", 'isOptional': False, 'isReturnedValue': False}, {'name': 'signal_file', 'type': 'File', 'defaultValue': '$input.getDefaultValue()', 'description': "Text file with extension '.RAW' containing the signal to quantify", 'isOptional': False, 'isReturnedValue': False}, {'name': 'control_file', 'type': 'File', 'defaultValue': '$input.getDefaultValue()', 'description': "Text file with extension '.control' setting up constraints, options and prior knowledge used in LCModel algorithm", 'isOptional': False, 'isReturnedValue': False}, {'name': 'script_file', 'type': 'File', 'defaultValue': '/vip/ReproVIP (group)/LCModel/run-lcmodel.sh', 'description': 'Script lauching lcmodel', 'isOptional': False, 'isReturnedValue': False}], 'canExecute': True}
    
    def fake_init_exec(pipeline, name, inputValues, resultsLocation):
        return 'workflow-XXXXXX'
    
    def fake_execution_info(workflow_id):
        return {'status': 'Finished', 'returnedFiles': [], 'startDate': 0}
    
    def fake_delete_path(path):
        nonlocal removed
        removed = True
        return True
    
    mocked_exists = mocker.patch("vip_client.utils.vip.exists")
    mocked_exists.side_effect = fake_exists

    mocked_pipeline_def = mocker.patch("vip_client.utils.vip.pipeline_def")
    mocked_pipeline_def.side_effect = fake_pipeline_def

    mocked_init_exec = mocker.patch("vip_client.utils.vip.init_exec")
    mocked_init_exec.side_effect = fake_init_exec

    mocked_execution_info = mocker.patch("vip_client.utils.vip.execution_info")
    mocked_execution_info.side_effect = fake_execution_info

    mocked_delete_path = mocker.patch("vip_client.utils.vip.delete_path")
    mocked_delete_path.side_effect = fake_delete_path

    # Launch a Full Session Run
    s = VipLauncher()
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
    assert len(s.workflows) == 1
    for wid in s.workflows:
        assert s.workflows[wid]["status"] == "Finished"
    assert s.pipeline_id == pipeline_id
    # Finish the Session
    s.finish(timeout=50)
    # Check Deletion
    assert removed
    for wid in s.workflows:
        assert s.workflows[wid]["status"] == "Removed"

@pytest.mark.parametrize(
    "backup_location, input_settings, pipeline_id, output_dir",
    [
        ('vip', {
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
        ('vip', {
            "zipped_folder": 'different_value1',
            "basis_file": 'different_value2',
            "signal_file": ['different_value3', 'different_value4'],
            "control_file": ['different_value5']
        }, "LCModel/0.1", PurePosixPath("/vip/Home/test-VipLauncher/OUTPUTS"),
        )
    ]
)
def test_backup(mocker, backup_location, input_settings, pipeline_id, output_dir):

    def fake_exists(path):
        return True

    def fake_pathlib_exists():
        return True
        
    def fake_delete_path(path):
        return True
    
    def fake_upload(local_path, vip_path):
        return True
    
    def fake_download(vip_path, local_path):
        return True
    
    def fake_pathlib_open(mode='r', buffering=-1, encoding=None, errors=None, newline=None):
        print("EENTER")
        return io.open('tmp_data.json', mode, buffering, encoding, errors, newline)
    
    def fake_unlink(self):
        return True

    mocked_exists = mocker.patch("vip_client.utils.vip.exists")
    mocked_exists.side_effect = fake_exists

    mocked_pathlib_exists = mocker.patch("pathlib.Path.exists")
    mocked_pathlib_exists.side_effect = fake_pathlib_exists

    mocked_delete_path = mocker.patch("vip_client.utils.vip.delete_path")
    mocked_delete_path.side_effect = fake_delete_path

    mocked_upload = mocker.patch("vip_client.utils.vip.upload")
    mocked_upload.side_effect = fake_upload

    mocked_download_file = mocker.patch("vip_client.utils.vip.download")
    mocked_download_file.side_effect = fake_download

    mocked_pathlib_open = mocker.patch("pathlib.Path.open")
    mocked_pathlib_open.side_effect = fake_pathlib_open

    mocked_unlink = mocker.patch("os.unlink")
    mocked_unlink.side_effect = fake_unlink

    VipLauncher._BACKUP_LOCATION = backup_location
    # Return if backup is disabled
    if VipLauncher._BACKUP_LOCATION is None:
        return
    # Create session
    s1 = VipLauncher()
    s1.input_settings = input_settings
    s1.pipeline_id = pipeline_id
    s1.output_dir = output_dir
    # Backup
    s1._save()
    # Load backup
    s2 = VipLauncher(output_dir=s1.output_dir)
    # Check parameters
    assert s2.input_settings == s1.input_settings
    assert s2.pipeline_id == s1.pipeline_id
    assert s2.output_dir == s1.output_dir
    assert s2.workflows == s1.workflows


def test_properties_interface(mocker):

    def fake_exists(path):
        return True

    def fake_pathlib_exists():
        return True
        
    def fake_delete_path(path):
        return True
    
    def fake_upload(local_path, vip_path):
        return True
    
    def fake_download(vip_path, local_path):
        return True
    
    def fake_pathlib_open(mode='r', buffering=-1, encoding=None, errors=None, newline=None):
        print("EENTER")
        return io.open('tmp_data.json', mode, buffering, encoding, errors, newline)
    
    def fake_unlink(self):
        return True

    mocked_exists = mocker.patch("vip_client.utils.vip.exists")
    mocked_exists.side_effect = fake_exists

    mocked_pathlib_exists = mocker.patch("pathlib.Path.exists")
    mocked_pathlib_exists.side_effect = fake_pathlib_exists

    mocked_delete_path = mocker.patch("vip_client.utils.vip.delete_path")
    mocked_delete_path.side_effect = fake_delete_path

    mocked_upload = mocker.patch("vip_client.utils.vip.upload")
    mocked_upload.side_effect = fake_upload

    mocked_download_file = mocker.patch("vip_client.utils.vip.download")
    mocked_download_file.side_effect = fake_download

    mocked_pathlib_open = mocker.patch("pathlib.Path.open")
    mocked_pathlib_open.side_effect = fake_pathlib_open

    mocked_unlink = mocker.patch("os.unlink")
    mocked_unlink.side_effect = fake_unlink

    VipLauncher._BACKUP_LOCATION = "vip"

    # Copy the first session
    s = VipLauncher(output_dir=PurePosixPath("/vip/Home/test-VipLauncher/OUTPUTS"))
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
