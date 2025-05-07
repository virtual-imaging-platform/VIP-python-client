from vip_client.classes import VipSession, VipGirder, VipLauncher
from mocked_services import mock_vip_api, mock_pathlib, mock_os, mock_girder_client
import pytest


test_cases_missing_input_fields = [
    {
        "zipped_folder": 'fake_value1',
        "basis_file": 'fake_value2',
        "signal_file": ['fake_value3', 'fake_value4']
    },
    {
        "zipped_folder": 'fake_value1',
        "signal_file": ['fake_value3', 'fake_value4'],
        "control_file": 'fake_value5'
    },
    {
        "basis_file": 'fake_value2',
        "signal_file": ['fake_value3', 'fake_value4'],
    },
    {
        "zipped_folder": 'fake_value1',
        "basis_file": 'fake_value2',
    },
    # {
    # }
]

# VipSession trouve pas que l'input est vide quand on a '' et non []
test_cases_missing_input_values = [
    {
        "zipped_folder": 'fake_value1',
        "basis_file": '',
        "signal_file": ['fake_value3', 'fake_value4'],
        "control_file": 'fake_value5'
    },
    {
        "zipped_folder": 'fake_value1',
        "basis_file": 'fake_value2',
        "signal_file": [],
        "control_file": 'fake_value5'
    },
    {
        "zipped_folder": '',
        "basis_file": 'fake_value2',
        "signal_file": ['fake_value3', 'fake_value4'],
        "control_file": 'fake_value5'
    }
]

test_cases_missing_input_fields = [(input_settings, tested_class) for input_settings in test_cases_missing_input_fields for tested_class in [VipSession, VipLauncher, VipGirder]]
test_cases_missing_input_values = [(input_settings, tested_class) for input_settings in test_cases_missing_input_values for tested_class in [VipSession, VipLauncher, VipGirder]]

@pytest.fixture(scope="function", autouse=True)
def setup_teardown_vip_launcher(request, mocker):
    # Mock the VIP API
    mock_vip_api(mocker, "LCModel/0.1")
    mock_pathlib(mocker)
    mock_os(mocker)
    mock_girder_client(mocker)
    
    # Setup code before running the tests in the class
    print("Handshake with VIP")
    VipSession.init(api_key="FAKE_KEY")
    VipLauncher.init(api_key="FAKE_KEY")
    VipGirder.init(vip_key="FAKE_KEY", girder_key="FAKE_KEY")
    print("Setup done")

# BIZARRE
@pytest.mark.parametrize(
    "input_settings, tested_class", test_cases_missing_input_fields
)
def test_missing_input_settings(mocker, input_settings, tested_class):

    VipGirder._BACKUP_LOCATION = None
    
    # Copy the first session
    s = tested_class(session_name="test-VipLauncher", input_settings=input_settings)
    s.pipeline_id = "LCModel/0.1"
    if tested_class == VipLauncher:
        s.output_dir = "/path/to/output"
    if tested_class == VipSession:   
        mocker.patch.object(VipSession, '_exists', return_value=True)
        s.input_dir = "."
    
    needed_fields = ["zipped_folder", "basis_file", "signal_file"]
    missing_fields = [field for field in needed_fields if field not in input_settings]
    
    if not missing_fields:
        s.run_session()
        return
    
    # catch the exception message
    with pytest.raises(AttributeError) as e:
        s.run_session()
    assert str(e.value) == "Missing input parameter(s): " + ", ".join(sorted(missing_fields))   



@pytest.mark.parametrize(
    "input_settings, tested_class", test_cases_missing_input_values
)       
def test_missing_input_values(mocker, input_settings, tested_class):
    
    def is_input_full(value):
        """
        Returns False if `value` contains an empty string or list.
        """
        if isinstance(value, list): # Case: list
            return len(value) > 0 and all([is_input_full(v) for v in value])
        else:
            return (len(str(value)) > 0)

    tested_class._BACKUP_LOCATION = None
    
    mocker.patch("pathlib.Path.is_file").return_value = True
    
    # Copy the first session

    #else:
        #s.output_dir = "/path/to/output"
    
    missing_fields = [field for field in input_settings if not is_input_full(input_settings[field])]
    
    if not missing_fields:
        s = tested_class(input_settings=input_settings, session_name="test-VipLauncher")
        s.pipeline_id = "LCModel/0.1"
        if tested_class == VipSession:   
            mocker.patch.object(VipSession, '_exists', return_value=True)
            s.input_dir = "."
        s.run_session()
        return
    # Catch the exception message
    with pytest.raises(ValueError) as e:
        s = tested_class(input_settings=input_settings, session_name="test-VipLauncher")
        s.pipeline_id = "LCModel/0.1"
        if tested_class == VipSession:   
            mocker.patch.object(VipSession, '_exists', return_value=True)
            s.input_dir = "."
        s.run_session()
    assert str(e.value) == "Missing input value(s) for parameter(s): " + ", ".join(sorted(missing_fields))
