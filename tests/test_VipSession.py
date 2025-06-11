from unittest.mock import patch
import pytest
from pathlib import *

from vip_client.classes import VipSession
from mocked_services import mock_vip_api, mock_pathlib, mock_os

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
        
    # Mock the VIP API
    mock_vip_api(mocker, "LCModel/0.1")
    mock_pathlib(mocker)
    mock_os(mocker)
    
    # Setup code before running the tests in the class
    print("Handshake with VIP")
    VipSession.init(api_key="FAKE_KEY")
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
    
    wf_counter = 0
    processing = 100
    

    def fake_exists(cls=None, path=None, location="local", ignore_empty_dir=False):
        return True
    
    with patch.object(VipSession, '_exists', fake_exists):

        def fake_init_exec(pipeline, name, inputValues, resultsLocation):
            nonlocal wf_counter
            wf_counter += 1
            return 'workflow-X' + str(wf_counter)
                    
        def fake_execution_info(workflow_id):
            nonlocal processing
            if not processing:
                return {'status': 'Finished', 'returnedFiles': [], 'startDate': 0}
            processing -= 1
            return {'status': 'Running', 'returnedFiles': [], 'startDate': 0}
            

        mocker.patch("vip_client.utils.vip.execution_info").side_effect = fake_execution_info


        mocker.patch("vip_client.utils.vip.execution_info").side_effect = fake_execution_info
        mocker.patch("vip_client.utils.vip.init_exec").side_effect = fake_init_exec
        
        # Launch a Full Session Run
        s = VipSession(output_dir="test-VipSession/out", input_dir="test-VipSession/in")
        s.pipeline_id = pipeline_id
        s.input_settings = {
            "zipped_folder": 'path/on/host/input.zip',
            "basis_file": 'path/on/host/fake_value',
            "signal_file": ['path/on/host/fake_value', 'path/on/host/fake_value'],
            "control_file": ['path/on/host/fake_value']
        }
        s.run_session(nb_runs=nb_runs, refresh_time=0)
        # Check the Results
        assert s.workflows
        assert len(s.workflows) == nb_runs
        for wid in s.workflows:
            assert s.workflows[wid]["status"] == "Finished"
        assert s.pipeline_id == pipeline_id

@pytest.mark.parametrize(
    "backup_location, input_settings, pipeline_id, output_dir",
    [
        ('local', {
            "zipped_folder": 'fake_value1',
            "basis_file": 'fake_value2',
            "signal_file": ['fake_value3', 'fake_value4'],
            "control_file": ['fake_value5']
        }, "LCModel/0.1", "test-VipSession/out",
        ),
        (None, {
            "zipped_folder": None,
            "basis_file": None,
            "signal_file": None,
            "control_file": None
        }, "LCModel/0.1", "test-VipSession/out",
        ),
        ('local', {
            "zipped_folder": 'different_value1',
            "basis_file": 'different_value2',
            "signal_file": ['different_value3', 'different_value4'],
            "control_file": ['different_value5']
        }, "LCModel/0.1", "test-VipSession/out",
        )
    ]
)
def test_backup(mocker, backup_location, input_settings, pipeline_id, output_dir):
    
    def fake_pipeline_def(pipeline):
        return {'identifier': pipeline_id, 'name': 'LCModel', 'description': 'MR spectrosocpy signal quantification software', 'version': '0.1', 'parameters': [{'name': 'zipped_folder', 'type': 'File', 'defaultValue': '$input.getDefaultValue()', 'description': 'Archive containing all metabolite & macromolecules in .RAW format', 'isOptional': False, 'isReturnedValue': False}, {'name': 'basis_file', 'type': 'File', 'defaultValue': '$input.getDefaultValue()', 'description': "Text file with extension '.basis' containing information & prior knowledge about the metabolites used for signal fit", 'isOptional': False, 'isReturnedValue': False}, {'name': 'signal_file', 'type': 'File', 'defaultValue': '$input.getDefaultValue()', 'description': "Text file with extension '.RAW' containing the signal to quantify", 'isOptional': False, 'isReturnedValue': False}, {'name': 'control_file', 'type': 'File', 'defaultValue': '$input.getDefaultValue()', 'description': "Text file with extension '.control' setting up constraints, options and prior knowledge used in LCModel algorithm", 'isOptional': False, 'isReturnedValue': False}, {'name': 'script_file', 'type': 'File', 'defaultValue': '/vip/ReproVIP (group)/LCModel/run-lcmodel.sh', 'description': 'Script lauching lcmodel', 'isOptional': False, 'isReturnedValue': False}], 'canExecute': True}
    
    s1_init = True
    
    def fake_is_file():
        nonlocal s1_init
        return not s1_init # If s1 is initialized, return False for not using the backup
    
    # Mock the VipSession method "_exists"
    mocker.patch.object(VipSession, '_exists', return_value=True)
    
    mocker.patch("vip_client.utils.vip.pipeline_def").side_effect = fake_pipeline_def
    mocker.patch("pathlib.Path.is_file").side_effect = fake_is_file
    
    VipSession._BACKUP_LOCATION = backup_location
    # Return if backup is disabled

    # Create session
    s1 = VipSession(output_dir=output_dir)
    s1.input_settings = input_settings
    s1.pipeline_id = pipeline_id    
    
    assert s1._save() is not (VipSession._BACKUP_LOCATION is None) # Return False if no backup location
    
    # Backup
    s1._save()
    # Set the s1 initialization flag to False
    s1_init = False
    # Load backup
    s2 = VipSession(output_dir=s1.output_dir)
    # Check parameters
    assert s2.output_dir == s1.output_dir
    if VipSession._BACKUP_LOCATION is None:
        assert not s2._load()
        assert s2.input_settings != s1.input_settings
        assert s2.pipeline_id != s1.pipeline_id
    else:
        assert s2.input_settings == s1.input_settings
        assert s2.pipeline_id == s1.pipeline_id

def test_properties_interface(mocker):

    VipSession._BACKUP_LOCATION = "local"

    # Copy the first session
    s = VipSession()
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
