### LCModel examples

This folder contains example code to launch the LCModel pipeline using the VIP Python client. It provides three configurations depending on the data source:

- **Data on VIP**: The notebook `launch_lcmodel.ipynb` uses inputs already stored on VIP and writes the results back to VIP.
- **Data on Girder**: The notebook `launch_with_girder.ipynb` uses inputs stored on Girder and saves the produced outputs there.
- **Local data**: The script `script_for_local_data/exec_LCModel.py` runs the LCModel pipeline on local inputs and downloads the results at the end of the session.

Note that `exec_LCModel.py` relies on `script_for_local_data/session_utils.py` to provide additional flexibility (e.g., launching multiple sessions in parallel, queueing upcoming sessions, and deduplicating uploads for inputs shared across sessions). Some of these features use internal mechanisms of the Python client and are not official examples of the standard usage of the client.

The notebook `launch_with_girder.ipynb` and the script `exec_LCModel.py` were created in collaboration with researchers from the CREATIS laboratory to study the variability of results as the DKNTMN parameter (specified in `.control` files) changes.