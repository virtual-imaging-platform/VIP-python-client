# import sys
# sys.path.append("../VipCI.py")
from VipCI import VipCI
from pathlib import *

if __name__=="__main__":

    # Directory
    my_dir = PurePosixPath("/collection/ReproVIPSpectro/data/quest/")

    # Input Settings
    my_settings = {
        "zipped_folder": "/collection/ReproVIPSpectro/data/quest/basis.zip",
        "data_file": [ my_dir / ("signals/Rec001_Vox%d.mrui" %i) for i in (1,2) ],
        "parameter_file": "/collection/ReproVIPSpectro/data/quest/parameters",
    }

    # Init
    VipCI.init(
        session_name="test",
        pipeline_id="CQUEST/0.1.1", 
        input_settings=my_settings, 
        output_dir="/collection/ReproVIPSpectro/results/new-folder"
    )
    VipCI.show_pipeline("quest")

    # Session
    VipCI.init(vip_key = "VIP_API_KEY", girder_key="GIRDER_API_KEY",
        pipeline_id="CQUEST/0.1.1", 
        input_settings=my_settings, 
        output_dir="/collection/ReproVIPSpectro/results/new-folder"
    ).run_session(refresh_time=5)
    
    # VipCI is unable to load a session
    session = VipCI(
        output_dir="/collection/ReproVIPSpectro/results/new-folder"
    ).monitor_workflows()

    # Errors
 
    # session = VipCI().launch_pipeline(
    #     pipeline_id="CQUEST/0.1-logs", 
    #     input_settings=my_settings, 
    #     output_dir="/collection/ReproVIPSpectro/results/new-folder2"
    # )
    # VipCI("/collection/ReproVIPSpectro/results/new-folder").finish()