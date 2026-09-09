"""
Utilities for VIP session management and workflow execution.
Contains helper functions for creating, launching, and monitoring LCModel sessions.
"""

import os
import time
import sys
from io import StringIO
from vip_client.classes import VipSession


def create_session_for_control_file(control_file, db_name, signal_files_list, control_folder_path, 
                                   signal_folder_path, zipped_folder_file_path, 
                                   make_basis_file_path, pipeline_id, output_folder_path, 
                                   session_0):
    """Creates and configures a VIP session for a given control file using pre-uploaded inputs"""
    # Individual settings for this specific session (referencing already uploaded files)
    input_settings = {
        "signal_file": [signal_folder_path + "/" + db_name + "/" + signal_file for signal_file in signal_files_list],
        "zipped_folder": zipped_folder_file_path,
        "makebasis_file": make_basis_file_path,
        "control_file": control_folder_path + "/" + control_file,    
    }

    print(control_file)
    session_name = "LCMODEL_DKNTMN_" + control_file.split("_")[-1].split(".")[0] + "_" + db_name
    
    os.makedirs(output_folder_path + '/' + session_name, exist_ok=True)

    session = VipSession(
        session_name=session_name,
        pipeline_id=pipeline_id,
        input_settings=input_settings,
        output_dir=output_folder_path + '/' + session_name,
    )
    
    # Access the inputs of Session-Zero
    session.get_inputs(session_0)
    
    return session, session_name, control_file


def launch_session(session):
    """Launches the pipeline for a session using pre-uploaded inputs"""
    try:
        session.launch_pipeline(nb_runs=1)
        return True
    except Exception as e:
        print(f"    ERROR: Failed to launch {session.session_name}: {e}")
        return False


def check_session_status(session):
    """
    Check the current status of a session by examining its workflows
    Returns: "Running", "Finished", "Failed", or "Unknown"
    """
    try:
        if not hasattr(session, 'workflows') or not session.workflows:
            return "Queued"
        
        # Update workflow status from VIP
        session._update_workflows()
        
        # Check if any workflows are still running
        running_count = 0
        finished_count = 0
        failed_count = 0
        
        for workflow_id, workflow_info in session.workflows.items():
            status = workflow_info.get("status", "Unknown")
            if status == "Running":
                running_count += 1
            elif status == "Finished":
                finished_count += 1
            elif status in ["Failed", "Error"]:
                failed_count += 1
        
        # Determine overall session status
        if failed_count > 0:
            return "Failed"
        elif running_count > 0:
            return "Running"
        elif finished_count > 0 and running_count == 0:
            return "Finished"
        else:
            return "Unknown"
            
    except Exception as e:
        print(f"    Warning: Status check failed for {session.session_name}: {e}")
        return "Unknown"


def manage_concurrent_workflows(all_sessions, max_concurrent=3, refresh_time=30, max_wait_time=3600):
    """
    Manages execution of sessions with a maximum number of concurrent workflows
    Uses a simple polling approach based on the VIP library source code
    
    Args:
        all_sessions: List of all sessions to execute
        max_concurrent: Maximum number of simultaneous workflows
        refresh_time: Time between status checks in seconds
        max_wait_time: Maximum total wait time in seconds
    
    Returns:
        Dict with final status of each session
    """
    print(f"Managing {len(all_sessions)} sessions with max {max_concurrent} concurrent workflows")
    
    # Initialize queues and tracking
    pending_sessions = all_sessions.copy()
    active_sessions = []
    completed_sessions = {}
    
    start_time = time.time()
    check_count = 0
    
    while pending_sessions or active_sessions:
        current_time = time.time()
        elapsed_time = current_time - start_time
        check_count += 1
        
        print(f"\n--- Check #{check_count} ({elapsed_time:.0f}s) | Pending: {len(pending_sessions)}, Active: {len(active_sessions)}, Completed: {len(completed_sessions)} ---")
        
        # Check timeout
        if elapsed_time > max_wait_time:
            print(f"TIMEOUT: Maximum wait time ({max_wait_time}s) reached.")
            for session in active_sessions + pending_sessions:
                if session.session_name not in completed_sessions:
                    completed_sessions[session.session_name] = "Timeout"
            break
        
        # Check status of active sessions
        newly_completed = []
        for session in active_sessions[:]:
            status = check_session_status(session)
            
            if status in ["Finished", "Failed"]:
                completed_sessions[session.session_name] = status
                active_sessions.remove(session)
                newly_completed.append(session)
                print(f"  {session.session_name}: {status}")
            elif status == "Unknown":
                print(f"  {session.session_name}: Status unknown, treating as still running")
        
        # Launch new sessions if slots are available
        available_slots = max_concurrent - len(active_sessions)
        sessions_to_launch = min(available_slots, len(pending_sessions))
        
        if sessions_to_launch > 0 and pending_sessions:
            for _ in range(sessions_to_launch):
                if pending_sessions:
                    session = pending_sessions.pop(0)
                    if launch_session(session):
                        active_sessions.append(session)
                        print(f"  Launched: {session.session_name}")
                    else:
                        completed_sessions[session.session_name] = "Failed"
                        print(f"  Failed to launch: {session.session_name}")
        
        # Show completed sessions this cycle
        if newly_completed:
            print(f"  Completed: {[s.session_name for s in newly_completed]}")
        
        # Wait before next check if there are still active or pending sessions
        if active_sessions or pending_sessions:
            print(f"  Waiting {refresh_time} seconds before next check...")
            time.sleep(refresh_time)
        else:
            break
    
    total_time = time.time() - start_time
    print(f"\nAll sessions completed in {total_time:.0f}s")
    return completed_sessions


def cleanup_vip_sessions(session_0, all_sessions):
    """Clean up VIP data for session_0 and all individual sessions"""
    print("\nCleaning up VIP data...")
    try:
        session_0.finish()  # removes the INPUT data for all sessions
        print("  Session-Zero cleaned up")
        
        for session in all_sessions:
            try:
                VipSession(session.session_name).finish()  # removes the OUTPUT data for current session
            except:
                pass
        print("  Individual sessions cleaned up")
        return True
    except Exception as e:
        print(f"  Warning: Cleanup failed: {e}")
        return False
