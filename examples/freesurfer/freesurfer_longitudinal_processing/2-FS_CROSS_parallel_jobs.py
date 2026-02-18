from vip_client import VipSession
from pathlib import Path
import os 

input_dir = Path("/insert/your/input/path") # make sure license file is in this directory
output_dir = Path("/insert/your/output/path/derivatives/freesurfer")

# Save current working directory and change to /tmp
orig_cwd = os.getcwd()  
os.chdir('/tmp')    

# Get T1w NIfTIs only from sub-* folders, excluding run-02, run-03, ...
nifti_files = [
    str(f)
    for sub in input_dir.iterdir()
    if sub.is_dir() and sub.name.startswith("sub-")
    for f in sub.rglob("*.nii.gz")
    if f.name.endswith("_T1w.nii.gz")
    and ("_run-" not in f.name or "_run-01_" in f.name)
]

# Create subjid from filenames
subjid = [Path(f).name.replace(".nii.gz", "") for f in nifti_files]

input_settings = {
    "nifti": nifti_files,
    "license": str(input_dir / "license.txt"),
    "subjid": subjid
}

session = VipSession.init(
    api_key="VIP_API_KEY",
    input_dir=str(input_dir),
    output_dir= str(output_dir),
    pipeline_id="FreeSurfer-Recon-all/7.3.1",
    input_settings=input_settings
)

session.run_session()
session.display()

# Restore original working directory
os.chdir(orig_cwd)

# Download outputs to the output_dir
session.download_outputs(get_status=['Finished', 'Killed'])

# Optional cleanup of outputs on VIP 
# session.finish()
