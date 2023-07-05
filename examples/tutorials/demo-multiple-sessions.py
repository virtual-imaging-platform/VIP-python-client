"""
This toy example provides a clever use of the VipSession method `get_inputs`.
The pipeline "CQUEST" is run with multiple parameter sets (`input_settings`)
on the same input data (`input_dir`). This is done in two steps :
1.  A single VipSession instance  is used to upload the dataset on VIP; 
2.  Multiple VipSession instances are used to run CQUEST with multiple 
    parameter sets. The dataset is shared between sessions using `get_inputs`.
"""

# Import libraries
import sys
from pathlib import *
from shutil import rmtree
sys.path.append(str(Path().resolve()))
from src.VipSession import VipSession

##############
# Parameters #
##############

# Path to the dataset
my_dataset = Path("examples/tutorials/data")

# Pipeline identifier
pipeline_id = "CQUEST/0.2-egi"

# Dictionnary containing multiple `input_settings` with dedicated `session_name`s
all_settings = { 
    # First session running on all signals
    "All-Signals": { 
        "data_file": list((my_dataset/"signals").iterdir()),
        "parameter_file": my_dataset / "parameters.txt",
        "zipped_folder": my_dataset / "basis.zip"
    },
    # Second session running on signal 1 only
    "Signal-1": { 
        "data_file": my_dataset/ "signals" / "001.mrui",
        "parameter_file": my_dataset / "parameters.txt",
        "zipped_folder": my_dataset / "basis.zip"
    },
    # Third session running on signal 2 only
    "Signal-2": { 
        "data_file": my_dataset/ "signals" / "002.mrui",
        "parameter_file": my_dataset / "parameters.txt",
        "zipped_folder": my_dataset / "basis.zip"
    }
}

#############
# Procedure #
#############

# Upload the full dataset with a dedicated "Session Zero"
session_0 = VipSession.init(
    api_key = "VIP_API_KEY", # << paste your VIP API key here 
    session_name = "Session-Zero",
    input_dir = my_dataset
).upload_inputs()

# Run the pipeline with each parameter set
for session_name in all_settings:
    # Instantiate a new VipSession with name, pipeline ID and input_settings
    s = VipSession( 
        session_name = session_name,
        pipeline_id = pipeline_id,
        input_settings = all_settings[session_name] 
    )
    # Access the inputs of Session-Zero
    s.get_inputs(session_0) 
    # Launch the upload-run-download procedure with the right settings
    s.run_session(update_files=False) # this will skip the "upload" step

# Remove the temporary data from VIP
session_0.finish() # removes the INPUT data for all sessions
for session_name in all_settings:
    VipSession(session_name).finish() # removes the OUTPUT data for current session

#######
# END #
#######

# Remove the output data from this machine
rmtree(session_0.output_dir) # removes data from Session Zero
for session_name in all_settings:
    rmtree(VipSession(session_name, verbose=False).output_dir) # data from curent session
try: Path("vip_outputs").rmdir() # removes the default output directory *if empty*
except: pass
print("\nOutput data have been removed from this machine.")