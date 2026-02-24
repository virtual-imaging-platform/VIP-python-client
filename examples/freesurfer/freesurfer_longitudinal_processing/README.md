
# FreeSurfer Longitudinal Processing Pipeline Using VIP Platform

## Overview  

This repository contains scripts and instructions to run **FreeSurfer longitudinal pipeline** encompassing three processing steps (cross, base, long) using **VIP Client** and **Girder** for data storage and retrieval. The pipeline supports **3D T1-weighted MRIs** for whole brain segmentation.
  
1. **Download MRI Data from Girder**
2. **Run FreeSurfer Longitudinal [CROSS]**: run the standard cross-sectional `recon-all` pipeline
3. **Group Per-Subject Timepoints**: these will be used as inputs for step 4
4. **Run FreeSurfer Longitudinal [BASE]** : run `recon-all -base` and create within subject template
5. **Run FreeSurfer Longitudinal [LONG]**: run `recon-all -long` and create subject-specific longitudinal segmentations.
6. **Upload FreeSurfer Outputs Back to Girder**: this step re-upload the `directives` folder containing the outputs back to Girder.
  
The pipeline is fully automated with Python scripts, integrates VIP job submission, monitoring, and local download, and ensures all derivatives are centralized on Girder.  
  
## Requirements  
  
### Software  
- Python ≥ 3.11  
- `vip-client` Python package  
- `girder_client` Python package  
  
### VIP  
- VIP account and API key  
- Access to the VIP **FreeSurfer pipelines**:  
  - `FreeSurfer-Recon-all/7.3.1`  
  - `FreeSurfer-Recon-all-BASE/7.3.1`  
  - `FreeSurfer-Recon-all-LONG/7.3.1`  

### Girder  
- Girder account and API key  
  
### Data  
- BIDS-compliant T1-weighted MRI dataset:

```
bids/
├── sub-*/
│   └── ses-*/
│       └── anat/
│           └── *_T1w.nii.gz
└── directives/
    └── freesurfer/
```
- FreeSurfer license file (`license.txt`) 

This setup allows **fully automated longitudinal FreeSurfer processing** with reproducible outputs stored both locally and on Girder for sharing or further analysis.

## Pipeline Workflow

## 1- Download MRI Data from Girder

This script authenticates to the Girder warehouse, download the input BIDS-compliant MRI dataset locally, and ensure the FreeSurfer derivatives directory structure exists.
  
### ⚙️ Inputs  
- `url`: Girder API endpoint  
- `folderId`: ID of the Girder folder containing MRI data  
- `download_dir`: Local path where data will be downloaded  
  
### 📤 Outputs  
- Local copy of the MRI dataset  
- Created directory: `derivatives/freesurfer/` inside the download folder if not already present.
  
### ▶️ How to Run  
1. Replace placeholders:  
- `url`
- `GIRDER_API_KEY`  
- `FOLDER_ID`  
- `/insert/your/download/path`  
2. Run the script:
```bash  
python3 1-girder_download_input_data.py  
```

## 2- Run FreeSurfer Longitudinal [CROSS]


This script launches the  **standard FreeSurfer`recon-all` cross sectional**  pipeline on VIP for all T1-weighted MRIs and download the results locally. The script:

-   Finds all  `*_T1w.nii.gz`  files in  `sub-*`  folders
-   Keeps only the  `run-01`  scans (ignores additional runs) --> See "File Selection Rules" Section below for more details
-   Builds subject IDs automatically from the filenames (removing  `.nii.gz`)   
-   Submits parallel jobs to the VIP FreeSurfer recon-all pipeline 
-   Downloads the completed outputs locally to  `derivatives/freesurfer/`

#### File Selection Rules

 **Note**: If two or more T1-weighted sequences were present at the same session, they were labeled  `*_run-01_T1w`  and  `_run-02_T1w`... The  **non-gadolinium (no Gado)**  scan (if present) was labeled as  `*_run-01_T1w`, as it is preferred for segmentation.
 
So, the script uses only files ending with:
-   `*_T1w.nii.gz`  (no run specification)
OR
-   `*_run-01_T1w.nii.gz` 

> ⚠️ If processing of `*_run-01_T1w.nii.gz` fails, you can try `*_run-02_T1w.nii.gz` or `*_run-03_T1w.nii.gz` directly on the platform. Make sure to put the results back in the `directives/freesurfer` folder.

### ⚙️ Inputs
- `nifti`: List of T1-weighted NIfTI files (`*_T1w.nii.gz`) from `sub-*` folders, keeping only `run-01`
- `license`: FreeSurfer license file, placed inside `input_dir`
- `subjid`: utomatically generated subject IDs used to name output folders for each NIfTI file (derived from the filename minus `.nii.gz`)

### 📤 Outputs
- FreeSurfer cross-sectional results in:  
  `derivatives/freesurfer/`  

> ⚠️ Important: Review the outputs carefully and note which results to keep or exclude/re-run before proceeding to the next steps.

### How to Run
1. Replace placeholders:
   - `/insert/your/input/path`
   - `/insert/your/output/path/derivatives/freesurfer`
   - `VIP_API_KEY`
2. Ensure `license.txt` is present in `input_dir`.
3. Run:
```bash  
python3 2-FS_CROSS_parallel_jobs.py  
```

## 3- Group Per-Subject Timepoints 

This script prepares the  **subject-specific timepoints tarballs for the BASE step**  by grouping cross-sectional timepoints (`ses-*`) for each subject into a single archive. Each archive contains all sessions for one subject, ready for the  `recon-all -base`  pipeline. The script:

-   Detects all eligible cross-sectional tarballs in  `derivatives/freesurfer/`
    -   Must contain  `ses-` 
    -   Must  **not**  contain  `.long.`  
-   Extracts each archive temporarily    
-   Groups timepoints by subject (`sub-XXXX`)    
-   Re-compresses them into one  `.tgz`  per subject   
-   Cleans temporary extracted files

### ⚙️ Inputs

-   `fs_dir`: Path to the  `derivatives/freesurfer/`  directory containing cross-sectional  `.tar.gz`  or  `.tgz`  outputs from downloaded from VIP in step 1.
    

### 📤 Outputs

-   Grouped per-subject archives for longitudinal processing:
`derivatives/freesurfer/`

### How to Run

1.  Replace placeholders:
    -   `/insert/your/input/path/derivatives/freesurfer`     
2.  Run:
```bash
python3 3-tar_sub_TPs.py  
```

## 4- Run FreeSurfer Longitudinal [BASE]


This script runs  **FreeSurfer  `recon-all -base`**  on VIP using the grouped timepoints from Step 3. It generates the  **within-subject template**  required for the following longitudinal processing stream.

The script:

-   Finds all grouped archives (`*_TPs.tgz`) in the  `tmp/`  folder
-   Extracts BASE IDs for each subject   
-   Launches the VIP  **recon-all -base**  pipeline    
-   Downloads the completed BASE outputs locally    
-   Deletes the temporary  `tmp/`  folder to clean up local storage
    

### ⚙️ Inputs

- `TP_TARBALL`: List of grouped timepoint archives (`*_TPs.tgz`) for each subject
- `LICENSE_FILE`: FreeSurfer license file (`license.txt`) located in `input_dir`
- `BASE_ID`: ubject IDs corresponding to each BASE template, automatically extracted from the tarball filenames and used to name the output folders for each subject
    
### 📤 Outputs

- Outputs will be downloaded to:
`derivatives/freesurfer`

**Note:** Keep the outputs on VIP as well, since they will be used directly in the next processing step [LONG]. This avoids the need to re-upload files. 
Also, 
> ⚠️ The temporary folder (`tmp`) will be deleted locally at the end of execution, since all data will be available on VIP for the next step. Make sure your FreeSurfer license file (`license.txt`) is copied to a safe location is stored in another safe location.

### How to Run

1. Replace placeholders:
   - `/insert/your/input/path/derivatives/freesurfer/tmp`
   - `/insert/your/output/path/derivatives/freesurfer`
   - `VIP_API_KEY`
2. Ensure `license.txt` is present in `input_dir`.
3. Run:
```bash  
python3 4-FS_BASE_parallel_jobs.py
```

## 5- Run FreeSurfer Longitudinal [LONG] 


This script runs  **FreeSurfer  `recon-all -long`**  on VIP using the  BASE templates from Step 4 and the timepoints (TPs) tarballs produced from Step 3 and were used as an input to step 4, producing segmentations more robustly by registering each timepoint to its corresponding subject template. The script:
-   Connects to VIP using the API key    
-   Lists BASE templates and TP tarballs on VIP   
-   Matches BASE templates with corresponding TP tarballs for each subject   
-   Prepares VIP input settings for the LONG pipeline  
-   Launches  `recon-all -long`  jobs in parallel on VIP    
-   Monitors workflow progress  
-   Downloads the completed longitudinal outputs to the local output directory
  
### ⚙️ Inputs  
- `TP_TARBALL`: List of grouped timepoint archives (`*_TPs.tgz`) for each subject (from the input folder in Step 4)
- `LICENSE_FILE`: FreeSurfer license file (`license.txt`) located in the Step 4 input folder
- `BASE_ID`: Subject-specific BASE template folder (output from Step 4)

### 📤 Outputs  
- Outputs will be downloaded to:
`derivatives/freesurfer`
- Output folders will be named following this pattern: `sub-*_ses-*_T1w.long.sub-*`.

### How to Run

1. Replace placeholders:
   - `/vip/Home/API/VipSession-xxxxxx-xxxxxx-bxx/OUTPUTS/YYYY-MM-DD_HHMMSS/`
   - `/vip/Home/API/VipSession-xxxxxx-xxxxxx-bxx/INPUTS/`
   - `VIP_API_KEY`
2.  `license.txt` should already be present in `/vip/Home/API/VipSession-xxxxxx-xxxxxx-bxx/INPUTS/`.
3. Run:
```bash  
python3 5-FS_LONG_parallel_jobs.py
```

## 6- Upload FreeSurfer Outputs Back to Girder

This script uploads **local FreeSurfer outputs** (from CROSS, BASE, and LONG pipelines) back to the **Girder warehouse** for centralized storage and sharing. The script:  
  
- Connects to Girder using the API key  
- Authenticates the user  
- Uploads the local FreeSurfer `derivatives` and/or `derivatives/freesurfer` back to Girder

### ⚙️ Inputs
- Girder API:
  - `url` — API endpoint of the Girder server  
    Examples:
    ```
    https://srmnopt.creatis.insa-lyon.fr/warehouse/api/v1
    https://myriad.creatis.insa-lyon.fr/api/v1
    ```
- Local FreeSurfer derivatives folder:
`/insert/your/upload/path/derivatives/freesurfer`
- Girder target folder ID:
`folderId = 'FOLDER_ID'`

### 📤 Outputs  
- Uploads all FreeSurfer derivative files (`derivatives/freesurfer/`) to the specified Girder folder  

### How to Run  
  
1. Replace placeholders:  
- `/insert/your/upload/path/derivatives/freesurfer` → local derivatives folder  
- `FOLDER_ID` → Girder target folder ID 
- `VIP_API_KEY` → your Girder API key  
2. Run:  
```bash  
python3 6-girder_upload_freesurfer_folder.py
```
