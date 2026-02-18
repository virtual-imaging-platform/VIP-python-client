#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "vip-client",
# ]
# ///

from vip_client import VipSession
from vip_client.utils import vip

# VIP API Key
API_KEY = "VIP_API_KEY"

# Initialize VIP connection
VipSession.init(api_key=API_KEY)

# VIP paths 
BASE_DIR = "/vip/Home/API/VipSession-xxxxxx-xxxxxx-bxx/OUTPUTS/YYYY-MM-DD_HHMMSS/" # from output of BASE pipeline
TP_DIR   = "/vip/Home/API/VipSession-xxxxxx-xxxxxx-bxx/INPUTS/" # from input of BASE pipeline
LICENSE_FILE = "/vip/Home/API/VipSession-xxxxxx-xxxxxx-bxx/INPUTS/license.txt" # from input of BASE pipeline

# Local output directory
output_dir = Path("/home/zakaria/VIP/guillaume_data_test/derivatives/freesurfer")

# List BASE and TP files from VIP 
base_files = [
    item['path']
    for item in vip.list_elements(BASE_DIR)
    if not item['isDirectory'] and item['path'].split('/')[-1].startswith("sub-") and "_TPs" not in item['path']
]

tp_files = [
    item['path']
    for item in vip.list_elements(TP_DIR)
    if not item['isDirectory'] and item['path'].split('/')[-1].startswith("sub-") and "_TPs" in item['path']
]

# Match BASE → TP tarball 
base_dict = {f.split("/")[-1].split(".")[0]: f for f in base_files}
tp_dict   = {f.split("/")[-1].split("_TPs")[0]: f for f in tp_files}
subjects = set(base_dict.keys()) & set(tp_dict.keys())

if not subjects:
    raise RuntimeError("No matching BASE and TP_TARBALL found!")

print(f"Submitting {len(subjects)} LONG jobs for subjects: {', '.join(subjects)}")

# Gather VIP input files per subject
vip_input_files = []
for sub in subjects:
    vip_input_files.append(base_dict[sub])
    vip_input_files.append(tp_dict[sub])

# Input settings for the LONG pipeline
input_settings = {
    "LICENSE_FILE": LICENSE_FILE,
    "BASE_ID": [base_dict[sub] for sub in subjects],      
    "TP_TARBALL": [tp_dict[sub] for sub in subjects],   
    "directives": "-all",                                
}

# Create VIP session
session_name = "VIP_FS_LONG_parallel"
session = VipSession(session_name)

# Launch pipeline directly on VIP
session.launch_pipeline(
    pipeline_id="FreeSurfer-Recon-all-LONG/7.3.1",
    input_settings=input_settings,
    output_dir= str(output_dir)
)

# Monitor progress
session.monitor_workflows()

# Download outputs to the output_dir
session.download_outputs(get_status=['Finished', 'Killed'])

# Optional cleanup of outputs on VIP 
# session.finish()

