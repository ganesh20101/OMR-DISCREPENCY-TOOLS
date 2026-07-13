# OMR Image Processing Pipeline with Jenkins

Automated alignment and scanning of OMR (Optical Mark Recognition) answer sheets using Python and Jenkins.

## Overview

This pipeline processes OMR images stored in subfolders. For each subfolder, it:
1. **Aligns** all `*F.jpg` images using a reference template image (if not already aligned).
2. **Scans** each image to extract roll numbers, question numbers (QBNO), question series (QPSERIES), and bubble responses.
3. Generates a **CSV file** per subfolder, named after the folder (e.g., `101.csv`).
4. Creates **marker files** (`alignment_done.txt`, `scan_done.txt`) to avoid re‑processing already completed folders.

## Features

- Recursively finds all `*F.jpg` images in subfolders.
- Uses **ORB feature matching** for image alignment.
- Extracts answer data using pre‑defined template regions (from a `.gs` JSON file).
- Progress bars with `tqdm` for alignment and scanning.
- Skips already aligned/scanned folders – ideal for incremental runs.
- Archives all generated CSV files in Jenkins.

## Prerequisites

### Software

- **Jenkins** (Windows) with Pipeline plugin.
- **Python 3.8+** (tested with 3.14.0).
- **Git** (to clone the repository).

### Python Packages

Install the required packages on the Jenkins machine:

```bash
pip install opencv-python pillow numpy tqdm

Directory Structure on Jenkins Machine

C:\
├── scripts\
│   ├── align.py          # Alignment script
│   └── scan.py           # OMR scanning script
├── New_folder\
│   └── all_images\
│       └── template\
│           ├── jssc.gs                 # JSON template (region definitions)
│           └── 2024.07.18 12.29.42F.jpg # Reference image for alignment
└── jssc\                               # Base folder for OMR images
    ├── 101\                            # Subfolder 101
    │   ├── 2024.07.18 12.29.42F.jpg
    │   └── ...
    ├── 102\
    └── ...
Note: Your image folders can have any name; the pipeline will process all subfolders containing *F.jpg files.
Jenkins Pipeline Setup
Create a new Pipeline job in Jenkins.

Select "Pipeline script" (or "Pipeline script from SCM" and point to this repository).

Copy the content of Jenkinsfile (provided in the repository) into the script area.

Configure environment variables in the environment block of the Jenkinsfile:

BASE_DIR – path to the root folder containing subfolders (e.g., C:\\jssc).

TEMPLATE_PATH – path to the template JSON file.

TEMPLATE_IMAGE – path to the reference alignment image.

ALIGN_SCRIPT – path to align.py.

SCAN_SCRIPT – path to scan.py.

(Optional) OUTPUT_CSV – leave empty for auto‑generated names.

Save the job and Build Now.

Running the Pipeline
The pipeline automatically discovers all subfolders under BASE_DIR that contain *F.jpg files.

It processes each subfolder in sequence.

After the first successful run, alignment_done.txt and scan_done.txt are created in each subfolder.

On subsequent runs, alignment and scanning are skipped for already‑processed folders.

All generated CSV files are copied to the Jenkins workspace and archived as build artifacts.

Configuration Parameters (Jenkinsfile)
Variable	Description	Example
BASE_DIR	Root folder containing subfolders with images	C:\\jssc
TEMPLATE_PATH	JSON template file (from GUI tool)	C:/New_folder/all_images/template/jssc.gs
TEMPLATE_IMAGE	Reference image for alignment	C:/New_folder/all_images/template/2024.07.18 12.29.42F.jpg
ALIGN_SCRIPT	Path to alignment Python script	C:/scripts/align.py
SCAN_SCRIPT	Path to scanning Python script	C:/scripts/scan.py
ALIGN_IMAGES	Enable alignment (true/false)	true
FORCE_ALIGNMENT	Force re‑alignment even if marker exists	false
Output
For each subfolder, the pipeline generates:

A CSV file named <folder>.csv inside that subfolder (e.g., 101.csv).

The CSV contains:

ROLLNO (concatenated digits)

QBNO (question booklet number)

QPSERIES (series letter)

One column per question (A1, A2, …) with answers (A, B, C, D, X for unanswered, * for multiple).

Front side Image – the full path to the image file.

Customisation
Recursive search: align.py and scan.py use os.walk() to find all *F.jpg files in subfolders. No changes needed.

Progress bars: tqdm is used for both scripts – they show live progress in the Jenkins console.

Marker files: alignment_done.txt and scan_done.txt are created in each subfolder to avoid reprocessing.

Troubleshooting
Issue	Solution
python not recognised in Jenkins	Add Python to System PATH and restart Jenkins service.
findFiles DSL method not found	Use archiveArtifacts artifacts: '*.csv' (as in the provided Jenkinsfile).
Paths with spaces	Use forward slashes (/) or double backslashes (\\) in environment block.
Get-ChildItem parameter errors	The Jenkinsfile uses compatible PowerShell syntax (Where-Object { $_.PSIsContainer }).
No F.jpg files found	Ensure images are named with F.jpg suffix and placed inside subfolders under BASE_DIR.
Alignment/scanning fails	Verify Python packages (opencv-python, numpy, tqdm) are installed.
License
GNU GPL v3 (or your preferred license).

Author: Ganesh
Copyright: © 2024

