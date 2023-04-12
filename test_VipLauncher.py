from VipLauncher import VipLauncher

if __name__=="__main__":
    # LCModel
    my_settings = {
        "zipped_folder": "/vip/Home/API/test-lcmodel/INPUTS/basis.zip",
        "basis_file": "/vip/Home/API/test-lcmodel/INPUTS/Basis_117T.basis",
        "signal_file": [
            "/vip/Home/API/test-lcmodel/INPUTS/signals/Rec002.RAW",
            "/vip/Home/API/test-lcmodel/INPUTS/signals/Rec001.RAW"
        ],
        "control_file": "/vip/Home/API/test-lcmodel/INPUTS/parameters/fit_117T_A.control",
    }
    VipLauncher.init(
        api_key="VIP_API_KEY")
    VipLauncher(
        session_name="tests-VipLauncher", 
        output_dir="/vip/Home/tests_VipLauncher",
        pipeline_id="LCModel/0.1", 
        input_settings=my_settings
    ).launch_pipeline().monitor_workflows().finish()
    VipLauncher(
        output_dir="/vip/Home/tests_VipLauncher",
    ).finish()