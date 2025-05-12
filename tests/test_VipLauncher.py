import pytest
from pathlib import *

from vip_client.classes import VipLauncher
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
        if path == '/vip/Home/test-VipLauncher/OUTPUTS' and not removed:
            return True
        if path == 'fake_value' and not removed:
            return True
        return False
    
    def fake_delete_path(path):
        nonlocal removed
        removed = True
        return True
    
    mocker.patch("vip_client.utils.vip.exists").side_effect = fake_exists
    mocker.patch("vip_client.utils.vip.delete_path").side_effect = fake_delete_path

    removed = False

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
    s.finish(timeout=1, keep_input=True, keep_output=True)
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
        
    removed = False
    removed2 = False
    access_counter = 3
    
    def fake_exists(path):
        nonlocal access_counter
        if path == '/vip/Home/test-VipLauncher/OUTPUTS/session_data.json':
            if access_counter > 0:
                access_counter -= 1
                return False
            else:
                return True
        nonlocal removed2
        if path == '/vip/Home/test-VipLauncher/OUTPUTS' and not removed:
            return True
        if path == "/vip/Home/test-VipLauncher/OUTPUTS/session_data.json" and not removed2:
            removed2 = True
            return False
        if path == 'fake_value' and not removed:
            return True
        return True
    
    def fake_delete_path(path):
        nonlocal removed
        removed = True
        return True
    
    mocker.patch("vip_client.utils.vip.exists").side_effect = fake_exists
    mocker.patch("vip_client.utils.vip.delete_path").side_effect = fake_delete_path

    mock_vip_api(mocker, pipeline_id)
    mock_pathlib(mocker)
    mock_os(mocker)

    VipLauncher._BACKUP_LOCATION = backup_location
    # Create session
    s1 = VipLauncher()
    s1.input_settings = input_settings
    s1.pipeline_id = pipeline_id
    s1.output_dir = output_dir
    
    # Return if backup is disabled
    assert s1._save() is not (VipLauncher._BACKUP_LOCATION is None) # Return False if no backup location
    
    # Load backup
    s2 = VipLauncher(output_dir=s1.output_dir)
    # Check parameters
    assert s2.output_dir == s1.output_dir
    if VipLauncher._BACKUP_LOCATION is None:
        assert not s2._load()
        assert s2.input_settings != s1.input_settings
        assert s2.pipeline_id != s1.pipeline_id
    else:
        assert s2.input_settings == s1.input_settings
        assert s2.pipeline_id == s1.pipeline_id


def test_properties_interface(mocker):

    mocker.patch("vip_client.utils.vip.exists").return_value = True
    
    VipLauncher._BACKUP_LOCATION = "vip"

    # Copy the first session
    s = VipLauncher(output_dir=PurePosixPath("/vip/Home/test-VipLauncher/OUTPUTS"))
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
