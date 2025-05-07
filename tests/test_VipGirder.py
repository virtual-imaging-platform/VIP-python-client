import pytest
from pathlib import *

from vip_client.classes import VipGirder
from mocked_services import mock_vip_api, mock_girder_client, mock_pathlib, mock_os
from FakeGirderClient import FakeGirderClient


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
    # Mock services
    mock_vip_api(mocker, "LCModel/0.1")
    mock_girder_client(mocker)
    mock_pathlib(mocker)
    mock_os(mocker)

    # Create a buffer file for the backup
    with open('tmp_data.json', 'w') as f:
        f.write('{}')
    
    # Setup code before running the tests in the class
    print("Handshake with VIP")
    VipGirder.init(vip_key="FAKE_KEY", girder_key="FAKE_KEY")
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
    processing = True
    
    def fake_init_exec(pipeline, name, inputValues, resultsLocation):
        nonlocal wf_counter
        wf_counter += 1
        return f'workflow-{wf_counter}'
             
    def fake_execution_info(workflow_id):
        nonlocal processing
        if not processing:
            return {'status': 'Finished', 'returnedFiles': [], 'startDate': 0}
        processing -= 1
        return {'status': 'Running', 'returnedFiles': [], 'startDate': 0}
    
    # Re patch the init_exec function to update the workflow counter
    mocker.patch("vip_client.utils.vip.init_exec").side_effect = fake_init_exec
    mocker.patch("vip_client.utils.vip.execution_info").side_effect = fake_execution_info
    
    # Launch a Full Session Run
    s = VipGirder(output_location="girder", session_name='test-VipLauncher', output_dir=PurePosixPath("/vip/Home/test-VipLauncher/OUTPUTS"))
    s.pipeline_id = pipeline_id
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
        }, "LCModel/0.1", PurePosixPath("/vip/Home/test-VipLauncher-Backup/OUTPUTS"),
        ),
        (None, {
            "zipped_folder": None,
            "basis_file": None,
            "signal_file": None,
            "control_file": None
        }, "LCModel/0.1", PurePosixPath("/vip/Home/test-VipLauncher-Backup/OUTPUTS"),
        ),
        ('girder', {
            "zipped_folder": 'different_value1',
            "basis_file": 'different_value2',
            "signal_file": ['different_value3', 'different_value4'],
            "control_file": ['different_value5']
        }, "LCModel/0.1", PurePosixPath("/vip/Home/test-VipLauncher-Backup-Special/OUTPUTS"),
        )
    ]
)
def test_backup(mocker, backup_location, input_settings, pipeline_id, output_dir):

    VipGirder._BACKUP_LOCATION = backup_location
        
    # Create session
    s1 = VipGirder(pipeline_id=pipeline_id, input_settings=input_settings, output_dir=output_dir)

    
    assert s1._save() is not (VipGirder._BACKUP_LOCATION is None) # Return False if no backup location
    
    # Load backup
    print("S1.OUTPUT_DIR", s1.output_dir)
    s2 = VipGirder(output_dir=s1.output_dir)
    # Check parameters
    assert s2.output_dir == s1.output_dir
    if VipGirder._BACKUP_LOCATION is None:
        assert not s2._load()
        assert s2.input_settings != s1.input_settings
        assert s2.pipeline_id != s1.pipeline_id
    else:
        assert s2.input_settings == s1.input_settings
        assert s2.pipeline_id == s1.pipeline_id


def test_properties_interface(mocker):

    VipGirder._BACKUP_LOCATION = "girder"

    # Copy the first session
    s = VipGirder()
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
