#!/usr/bin/env python
# coding: utf-8

# Main Parameters
# ---

# In[1]:


from vip-python-client.VipCI import VipCI
import time

# Pipeline identifier
my_pipeline="CQUEST/0.1.1"

# Input Settings
my_settings = {
    "zipped_folder": "/collection/ReproVIPSpectro/data/quest/basis.zip",
    "data_file": "/collection/ReproVIPSpectro/data/quest/signals",
    "parameter_file": "/collection/ReproVIPSpectro/data/quest/parameters/quest_param_117T_B.txt",
}
# N.B.: Here "data_file" leads to a folder, the other arguments lead to single files.

# Random output folder
my_output_dir = "/collection/ReproVIPSpectro/results/test_%s" \
    % time.strftime('%Y%m%d-%H%M%S', time.localtime())


# __N.B.__: In `my_settings`, the input files are pointed by Girder paths, usually in format: "/collection/[collection_name]/[path_to_folder]". 
# - if the path leads to a file, the same file be passed to VIP;
# - If the path leads to a Girder item, all files in this item will be passed to VIP;
# - If the path leads to a Girder folder, all files in this folder will be passed to VIP.

# ---
# Connect to VIP & Girder and run two VIP executions for CQUEST
# ---

# __N.B.__: You may kill the jobs after 3-4 minutes to shorten the test.

# In[3]:


# Connect with Vip & Girder
VipCI.init(
  vip_key="VIP_API_KEY", # My environment variable for the VIP API key (also works with litteral string or file name)
  girder_key="GIRDER_API_KEY" # My environment variable for the Girder API key (also works with litteral string or file name)
)

# Create a Session
session = VipCI(
  session_name="Test_Girder", # Session Name
)

# Launch the Pipeline
session.launch_pipeline(
  pipeline_id=my_pipeline, # Pipeline identifier
  input_settings=my_settings, # Input Settings
  output_dir=my_output_dir, # Output directory
  nb_runs=2 # Run 2 workflows at the same time
)

# Monitor VIP Executions
session.monitor_workflows()


# ---
# **Session metadata are now attached to the output folder on Girder.**
# - Check the results on the Girder portal: https://pilot-warehouse.creatis.insa-lyon.fr/#collection/63b6e0b14d15dd536f0484bc/folder/63b6e29b4d15dd536f0484c2

# __N.B.__: The last cell could also be written with a single line of code:
# ```python
# VipCI.init(
#     vip_key="VIP_API_KEY", # My environment variable for the VIP API key 
#     girder_key="GIRDER_API_KEY", # My environment variable for the Girder API key
#     session_name = "Test_Girder", # Session Name
#     pipeline_id=my_pipeline, # Pipeline identifier
#     input_settings=my_settings, # Input Settings
#     output_dir=my_output_dir # Output directory
# ).run_session(nb_runs=2) # Run 2 workflows at the same time
# ```

# ---
# Resume a previous Session and run 2 additional executions
# ---
# *A session can be loaded from its output directory on Girder*

# In[4]:


VipCI(my_output_dir).run_session(nb_runs=2)


# ---
# Check the results on the Girder portal: https://pilot-warehouse.creatis.insa-lyon.fr/#collection/63b6e0b14d15dd536f0484bc/folder/63b6e29b4d15dd536f0484c2
# 
