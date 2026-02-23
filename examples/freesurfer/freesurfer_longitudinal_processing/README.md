# SUIT Pipeline README 

## Overview

This pipeline processes T1-weighted MRI for **cerebellar analysis** using SPM12 and SUIT:

1.  **Locate Relevant MRIs and Copy to Directives Folders** – Copy `_T1w.nii.gz` and `run-01_T1w.nii.gz` to `directives/SUIT` folder and unzip.  
2.  **Set Origin & Re-orient** – Manually set origin and reorient in SPM window.   
3.  **SPM Unified Segmentation and Intra-Cranial Volume Calculation** – Segment GM/WM/CSF, create ICV mask, compute ICV, and save to `ICV_volumes.csv`.   
4.  **SPM-SUIT-based Cerebellar Segmentation** – Isolate cerebellum, normalize via SUIT, reslice atlas back to native space, compute lobular volumes, and save to `lobular_volumes.csv`.   
5.  **Cerebellum-Only GM/WM** – Mask brainstem using Buckner atlas, save cerebellum-only GM/WM, compute volumes and save to `total_cerebellar_volumes.csv`.

## Requirements

-   **Software:** MATLAB, SPM12, SUIT toolbox
-   **Data:** BIDS-compliant T1 MRIs (`sub-*/ses-*/anat/sub-*_ses-*_T1w.nii.gz`)  
-   **Files:** TPM.nii and Buckner 7-network atlas   

## Pipeline Workflow

## 1. Locate Relevant MRIs and Copy to Directives Folders

This MATLAB script scans a BIDS-like directory structure to:

-   Locate T1-weighted MRI files 
-   Select only the appropriate acquisitions
-   Copy them into a SUIT processing directory 
-   Unzip the files

It preserves the original bids folder hierarchy.

### ⚙️ Inputs

#### Required directory structure

The script expects a BIDS-like organization:

```
bids/
├── sub-*/
│   └── ses-*/
│       └── anat/
│           └── *_T1w.nii.gz
└── directives/
    └── SUIT/
```

#### Path variables

```matlab
src_root = 'path/to/bids/data'; #root folder containing original BIDS data
dst_root = 'path/to/bids/data/directives/SUIT'#destination folder where SUIT processing will take place;
```  

#### File Selection Rules

 **Note**: If two or more T1-weighted sequences were present at the same session, they were labeled  `*_run-01_T1w`  and  `_run-02_T1w`... The  **non-gadolinium (no Gado)**  scan (if present) was labeled as  `*_run-01_T1w`, as it is preferred for segmentation.
 
So, the script keeps only files ending with:
-   `_T1w.nii.gz`  (no run specification)
OR
-   `_run-01_T1w.nii.gz` 

All other runs (e.g., `run-02`, `run-03`, etc.) are excluded.
    
### 📤 Outputs

#### Output structure (preserved tree)

```
bids/
└── directives/
    └── SUIT/
        └── sub-*/
            └── ses-*/
                └── anat/
                    └── *_T1w.nii
```

## 2. Set Origin & Re-orient

This MATLAB script performs  **reorientation to set the origin at the anterior commissure**, ensuring optimal processing of T1-weighted MRI in subsequent SUIT steps. The script:

-   Recursively searches for all  `_T1w.nii`  files
-   Opens each file in SPM’s display window
-   Allows the user to set the origin and reorient the image
-   Waits for the user to close the window before proceeding to the next MRI
    
### ⚙️ Inputs

-   **dataFolder**: SUIT directives processing folder containing the T1 images 
    
```
dataFolder = 'path/to/bids/directives/SUIT';
```

### 📤 Outputs

-   Reoriented T1 images with the updated origin and orientation, **overwriting the original files** in the same folder

## 3. SPM Unified Segmentation and Intra-Cranial Volume Calculation

This MATLAB script performs automated **SPM12-based tissue segmentation** on the T1-weighted MRI scans and computes **intracranial volume (ICV)** metrics for each subject. The script uses SPM’s built-in batch functions

Specifically, the script:

 1. Segments each T1 image into gray matter (GM), white matter (WM), and
    cerebrospinal fluid (CSF) using SPM’s unified segmentation   
 2. Generates an intracranial volume (ICV) mask by combining GM, WM, and CSF probability maps    
 3. Calculates tissue volumes (GM, WM, CSF) and total ICV in mm³ using voxel dimensions  
 4. Save results as `ICV_volumes.csv`

Missing segmentation outputs are logged and skipped
    
### ⚙️ Inputs

 - **src_root**: SUIT directives processing folder containing the T1 images   
 - **tpm_file**: SPM tissue probability map (`TPM.nii`). It must be present in the `directives/SUIT` folder

    
```
src_root = 'path/to/bids/directives/SUIT';
tpm_file = fullfile(src_root,'TPM.nii');
```
  
### 📤 Outputs

 - **Segmented images**: `c1*`, `c2*`, `c3*` (GM, WM, CSF) 
 -  **Forward and and inverse deformation fields**  `y_*`, `iy_*`
 - **ICV mask**: `ICV_seg_*.nii`
 - **CSV file**: `ICV_volumes.csv` with columns: Subject and Session, GM_mm³, WM_mm³, CSF_mm³, ICV_mm³    
 - **Error log**: `step_3_error_logs.csv` (if any failures)

## 4. SPM-SUIT-based Cerebellar Segmentation

This MATLAB script performs **SUIT-based cerebellar segmentation** on the T1-weighted MRIs:

1.  Isolates cerebellum/brainstem using `suit_isolate_seg`  
2.  Normalizes gray/white matter via `suit_normalize_dartel`  
3.  Reslices the SUIT atlas to subject space (`suit_reslice_dartel_inv`)
4.  Calculates lobular volumes
5.  Saves results as `lobular_volumes.csv`

Missing segmentation outputs are logged and skipped

### ⚙️ Inputs

-   **dataFolder**:  SUIT directives processing folder containing the T1 images
    
```
dataFolder = 'path/to/bids/directives/SUIT';
```

### 📤 Outputs

-   **Cerebellar isolation masks**: `c_*_pcereb.nii`
-   **Segmentation files**: `*_seg1.nii`, `*_seg2.nii`  
-   **Normalization outputs**: `Affine_*_seg1.mat`, `u_a_*_seg1.nii`  
-   **Lobular volume CSV**: `lobular_volumes.csv`   
-   **Error log**: `step_4_error_logs.csv` (if any failures)
    
## 5. Cerebellum-Only GM/WM Extraction Using Buckner Atlas

This MATLAB script extracts **cerebellum-only gray and white matter volumes** from SUIT-segmented T1 images using the Buckner 7-network atlas:

> **Note:** SUIT GM and WM segmentations include both cerebellum and brainstem. Since this pipeline focuses only on the cerebellum, we use the Buckner cerebellar atlas to mask out brainstem tissue.

The script:

1.  Load and combine Buckner atlas into a single cerebellar mask
2.   Identify T1 image, `sub-*_seg1.nii` (GM), and `sub-*_seg1.nii` (WM) files and apply SUIT inverse normalization to warp the mask to each subject’s T1 space   
3.  Multiply GM and WM images by combined cerebellar mask to exclude brainstem
4.  Saves masked images and calculates probability-weighted volumes (mm³)    
5.  Save results as `total_cerebellar_volumes.csv`

Missing segmentation outputs are logged and skipped

## ⚙️ Inputs

-   **dataFolder**: folder containing SUIT-processed T1 images
-   **atlasFile**: Buckner 7-network atlas in SUIT space (`atl-Buckner7_space-SUIT_dseg.nii`).  It must be present in the `directives/SUIT` folder.
```
dataFolder = '/path/to/bids/directives/SUIT/';
atlasFile  = fullfile(dataFolder, 'atl-Buckner7_space-SUIT_dseg.nii');
```

## 📤 Outputs

-   **Masked images**:    
    -   `cerebGM_only_*.nii`     
    -   `cerebWM_only_*.nii`      
-   **CSV file**: `total_cerebellar_volumes.csv` (columns: Tissue, Volume_mm³)    
-   **Error log**: `step_5_error_logs.csv` (if any failures)
    

