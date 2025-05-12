
class FakeGirderClient():
    
    pipeline_id = "LCModel/0.1"
    def __init__(self, apiUrl):
        pass
    def authenticate(self, apiKey):
        return True
    
    def resourceLookup(self, path):
        if path == '/vip/Home/test-VipLauncher-Backup/OUTPUTS':
            # Used to test the backup location, linked to the fake fetFolder method
            print("FakeGirderClient: resourceLookup called with path:", path)
            return {'_id': 'fake_id', '_modelType': 'folder'}
        elif path == '/vip/Home/test-VipLauncher-Backup-Special/OUTPUTS':
            print("FakeGirderClient: resourceLookup called with path:", path)
            return {'_id': 'different_id', '_modelType': 'folder'}
        else:
            return {'_id': 'other_id', '_modelType': 'folder'}
    
    def createFolder(self, parentId, name, reuseExisting=True, **kwargs):
        return {'_id': 'fake_id'}
    
    def addMetadataToFolder(self, folderId, metadata):
        return True
    
    def getFolder(cls, folderId):
        if folderId == 'fake_id':
            print("FakeGirderClient: getFolder called with folderId:", folderId)
            metadata = {
                'input_settings': {
                    'zipped_folder': 'fake_value1', 
                    'basis_file': 'fake_value2',
                    'signal_file': ['fake_value3', 'fake_value4'], 
                    'control_file': ['fake_value5']
                },
                "pipeline_id": cls.pipeline_id,
                'session_name': 'test-VipLauncher', 
                'workflows': {}, 
                "vip_output_dir": "/vip/Home/test-VipLauncher-Backup/OUTPUTS",
                'output_location': 'girder',
                'local_output_dir': '/path/to/local/output',
            }
            return {'_id': 'fake_id', 'meta': metadata}
        elif folderId == 'different_id':
            print("FakeGirderClient: getFolder called with folderId:", folderId)
            metadata = {
                'input_settings': {
                    'zipped_folder': 'different_value1', 
                    'basis_file': 'different_value2',
                    'signal_file': ['different_value3', 'different_value4'], 
                    'control_file': ['different_value5']
                },
                "pipeline_id": cls.pipeline_id,
                'session_name': 'test-VipLauncher-Special', 
                'workflows': {}, 
                "vip_output_dir": "/vip/Home/test-VipLauncher-Backup-Special/OUTPUTS",
                'output_location': 'girder',
                'local_output_dir': '/path/to/local/output',
            }
            return {'_id': 'different_id', 'meta': metadata}
        else:
            return {'_id': 'fake_id', 'meta': {}}
    
    def get(self, path):
        return {'_id': 'fake_id'}
    
    def listFiles(self, folderId):
        return [{'_id': 'fake_id'}]
    
    def listItem(self, folderId):
        return {'_id': 'fake_id'}
    
    @classmethod
    def set_pipeline_id(cls, pipeline_id):
        cls.pipeline_id = pipeline_id