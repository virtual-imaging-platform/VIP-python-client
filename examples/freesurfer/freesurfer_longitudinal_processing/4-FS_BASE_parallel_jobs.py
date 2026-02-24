#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "vip-client",
# ]

from vip_client import VipSession
from pathlib import Path
import os 

# This directory will be uploaded to VIP — ensure no sensitive data
# (e.g., DICOMs, scripts containing API keys) is included. 
input_dir = Path("/insert/your/input/path/derivatives/freesurfer/tmp") #make sure license file is copied in this directory
output_dir = Path("/insert/your/output/path/derivatives/freesurfer")

# Save current working directory and change to /tmp (temporary workaround for VIP bug)
orig_cwd = os.getcwd()  
os.chdir('/tmp')      

# Collect tarballs and BASE_IDs
tp_tarballs = [f for f in input_dir.iterdir() if f.suffix in (".tgz", ".tar.gz") and "_TPs" in f.name]
tp_tarballs.sort()  # optional

base_ids = [f.name.split("_")[0] for f in tp_tarballs]

# Build batch input settings
input_settings = {
    "LICENSE_FILE": str(input_dir / "license.txt"),
    "TP_TARBALL": [str(f) for f in tp_tarballs],  # list of tarballs
    "BASE_ID": base_ids,                           # list of base IDs
}

session = VipSession.init(
    api_key="VIP_API_KEY",
    input_dir=str(input_dir),
    output_dir= str(output_dir),
    pipeline_id="FreeSurfer-Recon-all-BASE/7.3.1",
    input_settings=input_settings,
)

session.run_session()  # VIP will process tarballs in parallel
session.display()

# Restore original working directory
os.chdir(orig_cwd)

# Download outputs to the output_dir
session.download_outputs(get_status=['Finished', 'Killed'])

# Optional cleanup of outputs on VIP 
# session.finish()

# Delete tmp folder locally
# WARNING: This removes the entire directory.
# Make sure that the license file is stored in another safe location.
shutil.rmtree(input_dir)
print(f"Deleted temporary folder: {input_dir}")



