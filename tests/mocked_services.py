import io
from pathlib import Path


def mock_vip_api(mocker, pipeline_id):
    
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
                        'defaultValue': None, 
                        'description': 'Archive containing all metabolite & macromolecules in .RAW format', 
                        'isOptional': False, 
                        'isReturnedValue': False
                    }, 
                    {
                        'name': 'basis_file', 
                        'type': 'File', 
                        'defaultValue': None, 
                        'description': "Text file with extension '.basis' containing information & prior ...", 
                        'isOptional': False, 
                        'isReturnedValue': False
                    }, 
                    {
                        'name': 'signal_file', 
                        'type': 'File', 
                        'defaultValue': None, 
                        'description': "Text file with extension '.RAW' containing the signal to quantify", 
                        'isOptional': False, 
                        'isReturnedValue': False
                    }, 
                    {
                        'name': 'control_file', 
                        'type': 'File', 
                        'defaultValue': None, 
                        'description': "Text file with extension '.control' setting up constraints, options and prior knowledge used in LCModel algorithm", 
                        'isOptional': True, 
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
    
    def fake_list_elements(self):
        return [{'name': 'element1', 'path': 'path1'}, {'name': 'element2', 'path': 'path2'}]
    
    def fake_exists(path):
        return False
    
    def fake_delete_path(path):
        return True
    
    # mocker.patch("vip_client.utils.vip.exists", side_effect = fake_exists)
    mocker.patch("vip_client.utils.vip.exists").return_value = True
    mocker.patch("vip_client.utils.vip.upload").return_value = True
    mocker.patch("vip_client.utils.vip.download").return_value = True
    mocker.patch("vip_client.utils.vip.pipeline_def").side_effect = fake_pipeline_def
    mocker.patch("vip_client.utils.vip.list_pipeline").side_effect = fake_list_pipeline
    mocker.patch("vip_client.utils.vip.setApiKey").side_effect = fake_set_api_key
    mocker.patch("vip_client.utils.vip.init_exec").side_effect = fake_init_exec
    mocker.patch("vip_client.utils.vip.execution_info").side_effect = fake_execution_info
    mocker.patch("vip_client.utils.vip.list_elements").side_effect = fake_list_elements
    mocker.patch("vip_client.utils.vip.delete_path").side_effect = fake_delete_path

def mock_pathlib(mocker):
    
    def fake_pathlib_open(mode='r', buffering=-1, encoding=None, errors=None, newline=None):
        return io.open('tmp_data.json', mode, buffering, encoding, errors, newline)
    
    def fake_pathlib_iterdir():
        return [Path('tmp_data.json')]
    
    mocker.patch("pathlib.Path.exists").return_value = True
    mocker.patch("pathlib.Path.unlink").return_value = True
    mocker.patch("pathlib.Path.open").side_effect = fake_pathlib_open
    mocker.patch("pathlib.Path.iterdir").side_effect = fake_pathlib_iterdir
    
def mock_os(mocker):
    mocker.patch("os.unlink")
            
def mock_girder_client(mocker):
    from FakeGirderClient import FakeGirderClient
    mocker.patch("girder_client.GirderClient", FakeGirderClient)