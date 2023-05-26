from VipLauncher import VipLauncher
from VipSession import VipSession
from pathlib import *

if __name__=="__main__":

    VipSession.init("VIP_API_KEY", session_name="test-lcmodel").upload_inputs("examples/data/lcmodel_sample", update_files=False)

    my_dir = PurePosixPath("/vip/Home/API/test-lcmodel/INPUTS")
    my_settings = {
        "zipped_folder": my_dir / "basis.zip",
        "basis_file": my_dir / "Basis_117T.basis",
        "signal_file": [ my_dir / s for s in ("signals/Rec002.RAW",  "signals/Rec001.RAW") ],
        "control_file": my_dir / "parameters/fit_117T_A.control"
    }
    # Init
    VipLauncher.init(api_key="VIP_API_KEY")
    # Full Run
    VipLauncher(
        session_name="tests-VipLauncher", 
        output_dir="/vip/Home/tests_VipLauncher",
        pipeline_id="LCModel/0.1", 
        input_settings=my_settings
    ).launch_pipeline().monitor_workflows(refresh_time=2).display().finish(timeout=100).display()
    # Fail
    VipLauncher(
        output_dir="/vip/Home/tests_VipLauncher",
    ).finish().display()

    VipSession("test-lcmodel").finish()