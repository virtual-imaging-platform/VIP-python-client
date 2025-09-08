# 1. Imports
import os
import shutil
from pathlib import Path

from vip_client.classes import VipSession
from session_utils import (
    create_session_for_control_file, 
    manage_concurrent_workflows, 
    cleanup_vip_sessions
)

# 2. User parameters (to edit)
VIP_API_KEY         = os.environ.get('VIP_API_KEY')

PIPELINE_ID         = "LCModel/0.2"
LAUNCH_EXECUTION    = True

# 3. Pipeline parameters (to edit)
CONTROL_FOLDER_PATH = './tests_slim/inputs/controls'
SIGNAL_FOLDER_PATH = './tests_slim/inputs/signals'
MAKE_BASIS_FILE_PATH = './tests_slim/inputs/makeBasis_3T_Mac_VIP.in'
ZIPPED_FOLDER_FILE_PATH = './tests_slim/inputs/basis.zip'
INPUT_FOLDER_PATH = './tests_slim/inputs'

OUTPUT_FOLDER_PATH  = './tests_slim/outputs/data'

# 4. Results extraction folder
EXTRACTION_FOLDER   = './tests_slim/outputs/extracted_files'
os.makedirs(EXTRACTION_FOLDER, exist_ok=True)

# 5. Execution parameters (to edit)
MAX_CONCURRENT_WORKFLOWS = 3  # Number of concurrent workflows (probably max 3 for now)
REFRESH_TIME = 10  # Workflow status check interval in seconds
MAX_WAIT_TIME = 3600  # Maximum wait time for running sessions

# 6. VIP initialization and global upload of inputs
session_0 = None
if LAUNCH_EXECUTION:
    # Get all .control and .signal files (per database)
    control_files_list = os.listdir(CONTROL_FOLDER_PATH)
    signal_database_list = os.listdir(SIGNAL_FOLDER_PATH)
    
    print(f"Initializing VIP and uploading inputs for {len(control_files_list)} sessions...")
    
    # Upload the zero session (containing all inputs)
    session_0 = VipSession.init(
        api_key=VIP_API_KEY,
        session_name="Session-Zero-LCModel",
        input_dir=INPUT_FOLDER_PATH
    ).upload_inputs()
    
    print("Global upload completed!")

if LAUNCH_EXECUTION:
    print(f"Preparing {len(control_files_list) * len(signal_database_list)} sessions")
    
    # Phase 1: Create executions
    all_sessions = []

    for control_file, signal_database in [(cf, sd) for cf in control_files_list for sd in signal_database_list]:
        signal_files_list = [f for f in os.listdir(f"{SIGNAL_FOLDER_PATH}/{signal_database}") if f.endswith('.RAW')]
        try:
            db_name = signal_database.split("_")[0]
            session, session_name, control_file_ref = create_session_for_control_file(
                control_file, db_name, signal_files_list, CONTROL_FOLDER_PATH,
                SIGNAL_FOLDER_PATH, ZIPPED_FOLDER_FILE_PATH, MAKE_BASIS_FILE_PATH,
                PIPELINE_ID, OUTPUT_FOLDER_PATH, session_0
            )
            all_sessions.append(session)
            print(f"Creating session for control file: {control_file} with signals from {signal_database}")
            
        except Exception as e:
            print(f"ERROR: Failed to create session for {control_file}: {e}")
    
    print(f"Created {len(all_sessions)} sessions successfully")
    
    # Phase 2: Manage executions
    if all_sessions:
        final_status = manage_concurrent_workflows(
            all_sessions, 
            max_concurrent=MAX_CONCURRENT_WORKFLOWS,
            refresh_time=REFRESH_TIME,
            max_wait_time=MAX_WAIT_TIME
        )
        
        # Phase 3: Download results
        print("\nDownloading results...")
        successful_downloads = 0
        
        for session in all_sessions:
            session_name = session.session_name
            status = final_status.get(session_name, "Unknown")
            
            if status == "Finished":
                try:
                    session.download_outputs(get_status=["Finished"], unzip=True)
                    successful_downloads += 1
                    print(f"  Downloaded: {session_name}")
                except Exception as e:
                    print(f"  ERROR: Download failed for {session_name}: {e}")
        
        # Summary
        print("\nFinal Summary:")
        print(f"  Sessions created: {len(all_sessions)}")
        print(f"  Successfully completed: {sum(1 for s in final_status.values() if s == 'Finished')}")
        print(f"  Failed: {sum(1 for s in final_status.values() if s == 'Failed')}")
        print(f"  Downloaded: {successful_downloads}")

        # Cleanup: Delete temporary data from VIP.
        # WARNING: if the script is interrupted before this step, you will need to manually delete outputs produced on VIP.
        cleanup_vip_sessions(session_0, all_sessions)
    
else:
    print("LAUNCH_EXECUTION is set to False, skipping pipeline execution")




# 7. Retrieve output folders
if os.path.exists(OUTPUT_FOLDER_PATH):
    folders = os.listdir(OUTPUT_FOLDER_PATH)
    print(f"Processing output directory: {OUTPUT_FOLDER_PATH}")
    dkntmn_folders = [f for f in folders if os.path.isdir(Path(OUTPUT_FOLDER_PATH) / f)]
    
    output_path = Path(OUTPUT_FOLDER_PATH)
    
    # 8. Extract .table files
    extracted_count = 0
    for folder in dkntmn_folders:
        folder_path = output_path / folder
        
        if not folder_path.exists():
            continue
            
        sub_folders = [d for d in os.listdir(folder_path) if os.path.isdir(folder_path / d)]
        if not sub_folders:
            continue
            
        # To ignore timestamps that wrap simulations (change if studying reproducibility with the same parameters)
        sub = sub_folders[0]
        sub_path = folder_path / sub
        
        # Search for .tgz folders containing results
        items_in_sub = os.listdir(sub_path)
        tgz_folders = [f for f in items_in_sub if f.endswith('.tgz') and os.path.isdir(sub_path / f)]
        
        for item in tgz_folders:
            item_path = sub_path / item
            table_path = item_path / 'result.table'
            dest_folder = Path(EXTRACTION_FOLDER) / folder
            
            if table_path.exists():
                os.makedirs(dest_folder, exist_ok=True)
                
                identifier = item.split('.')[0] + '.table'
                new_table_path = dest_folder / identifier
                
                # Copy the .table into the extraction folder
                try:
                    shutil.copy(table_path, new_table_path)
                    extracted_count += 1
                    
                except Exception as e:
                    print(f"ERROR during copy: {e}")
    
    print(f"Extracted {extracted_count} result files to: {EXTRACTION_FOLDER}")
    
    # Check final
    if os.path.exists(EXTRACTION_FOLDER):
        total_files = sum(len(files) for _, _, files in os.walk(EXTRACTION_FOLDER))
        print(f"Total files in extraction folder: {total_files}")
    else:
        print("Extraction folder does not exist or is empty")
        
else:
    print(f"Output directory {OUTPUT_FOLDER_PATH} does not exist. Skipping file extraction.")
