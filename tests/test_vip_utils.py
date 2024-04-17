import pytest
import time
import os

from src.vip_client.utils.vip import *

BASE_PATH_VIP = '/vip/Home/API/client_tests/'
BASE_PATH_LOCAL = 'tests/data/'


def compare_files(file1, file2):
    with open(file1, 'r') as f1, open(file2, 'r') as f2:
        return f1.read() == f2.read()

@pytest.fixture(scope="session", autouse=True)
def setup_teardown_vip_launcher():
    assert setApiKey(os.environ['VIP_API_KEY'])
    assert new_session()
    if not create_dir(BASE_PATH_VIP):
        raise Exception("Error creating directory")
    counter = 0
    while not exists(BASE_PATH_VIP):
        time.sleep(5)
        if counter > 24:
            raise Exception("Directory not created after 120 seconds")
        counter += 1
    yield
    assert delete_path(BASE_PATH_VIP)

def test_upload_download():
    assert upload(BASE_PATH_LOCAL + 'file.txt', BASE_PATH_VIP + 'file.txt')
    assert exists(BASE_PATH_VIP + 'file.txt')
    assert download(BASE_PATH_VIP + 'file.txt', BASE_PATH_LOCAL + 'file_copy.txt')
    assert compare_files(BASE_PATH_LOCAL + 'file.txt', BASE_PATH_LOCAL + 'file_copy.txt')
    assert delete_path(BASE_PATH_VIP + 'file.txt')


def test_init_exec():
    input_values = {
        'mand_text': 'value1',
        'mand_file': '/vip/Home/file.txt',
    }
    exec_id = init_exec('Fake_app_test/0.1', resultsLocation=BASE_PATH_VIP, inputValues=input_values, name='test_init_exec')
    exec_info = execution_info(exec_id)
    assert exec_info['status'] == 'Running'


def test_kill_exec():
    input_values = {
        'mand_text': 'value1',
        'mand_file': '/vip/Home/file.txt',
        'mand_time': 100,
    }
    exec_id = init_exec('Fake_app_test_delay/0.1', resultsLocation=BASE_PATH_VIP, inputValues=input_values, name='test_kill_exec')
    counter = 0
    while execution_info(exec_id)['status'] != 'Running':
        time.sleep(5)
        if counter > 12:
            raise Exception("Execution not started after 60 seconds")
        counter += 1
    assert kill_execution(exec_id, deleteFiles=True)
    counter = 0
    while execution_info(exec_id)['status'] != 'Killed':
        time.sleep(5)
        if counter > 12:
            raise Exception("Execution not killed after 60 seconds")

def test_get_exec_stdout():
    input_values = {
        'mand_text': 'value1',
        'mand_file': '/vip/Home/file.txt',
    }
    exec_id = init_exec('Fake_app_test/0.1', resultsLocation=BASE_PATH_VIP, inputValues=input_values, name='test_get_exec_stdout')
    counter = 0
    while execution_info(exec_id)['status'] != 'Finished':
        time.sleep(5)
        if counter > 12:
            raise Exception("Execution not ended after 60 seconds")
        counter += 1
    stdout = get_exec_stdout(exec_id)
    assert isinstance(stdout, str)
    

def test_get_exec_results():
    input_values = {
        'mand_text': 'value1',
        'mand_file': '/vip/Home/file.txt',
    }
    exec_id = init_exec('Fake_app_test/0.1', resultsLocation=BASE_PATH_VIP, inputValues=input_values, name='test_get_exec_results')
    counter = 0
    while execution_info(exec_id)['status'] != 'Finished':
        time.sleep(5)
        if counter > 12:
            raise Exception("Execution not ended after 60 seconds")
        counter += 1
    results = get_exec_results(exec_id)
    # assert that this is a list of dictionaries
    assert isinstance(results, list)
    for r in results:
        assert isinstance(r, dict)
        assert 'executionId' in r
        assert 'path' in r
    

def test_list_pipeline():
    pipelines = list_pipeline()
    # assert that this is a list of dictionaries
    assert isinstance(pipelines, list)
    for p in pipelines:
        assert isinstance(p, dict)
        assert 'identifier' in p
        assert 'name' in p
        assert 'version' in p
        assert 'parameters' in p
        assert 'canExecute' in p
        assert 'description' in p


def test_pipeline_def():
    pipeline = pipeline_def('CQUEST/0.3')
    assert isinstance(pipeline, dict)
    assert 'identifier' in pipeline
    assert 'name' in pipeline
    assert 'version' in pipeline
    assert 'parameters' in pipeline
    assert 'canExecute' in pipeline
    assert 'description' in pipeline


def test_platform_info():
    info = platform_info()
    assert isinstance(info, dict)
    assert info['platformName'] == 'VIP'
   