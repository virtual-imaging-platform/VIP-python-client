
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
        cls.pipeline_id = pipeline_id