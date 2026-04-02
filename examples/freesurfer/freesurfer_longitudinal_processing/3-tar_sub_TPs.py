from pathlib import Path
import tarfile
import shutil
import csv

fs_dir = Path("/insert/your/input/path/derivatives/freesurfer")
tmp_dir = fs_dir / "tmp"

# create a tmp directory if it doesn't exist
tmp_dir.mkdir(exist_ok=True)

# Collect eligible tarballs (.tar.gz or .tgz)
tarballs = [
    t for t in fs_dir.iterdir()
    if t.is_file()
    and t.suffixes in ([".tar", ".gz"], [".tgz"])
    and "ses-" in t.name
    and ".long." not in t.name
]

subjects = {}

for tar_path in tarballs:
    subj = tar_path.name.split("_")[0]  # sub-XXXX

    # Remove full archive suffix safely
    if tar_path.suffixes == [".tar", ".gz"]:
        folder_name = tar_path.name[:-7]  # remove .tar.gz
    else:  # .tgz
        folder_name = tar_path.stem  # remove .tgz

    extract_dir = tmp_dir / "extracted" / folder_name
    extract_dir.mkdir(parents=True, exist_ok=True)

    # Untar 
    with tarfile.open(tar_path, "r:*") as tar:
        for member in tar.getmembers():
            # Strip first path component
            parts = member.name.split("/", 1)
            if len(parts) == 2:
                member.name = parts[1]
            else:
                member.name = parts[0]
            tar.extract(member, path=extract_dir)

    subjects.setdefault(subj, []).append(folder_name)  # store folder/archive name

# Group per subject
single_tp_subjects_dict = {}  # subjects with only one timepoint

for subj, tp_dirs in subjects.items():
    if len(tp_dirs) == 1:
        # Only one timepoint -> won't be tarred
        single_tp_subjects_dict[subj] = tp_dirs[0]  # full folder/archive name
        continue

    # Tarball for subjects with multiple timepoints
    out_tar = tmp_dir / f"{subj}_TPs.tgz"
    with tarfile.open(out_tar, "w:gz") as tar:
        for folder_name in tp_dirs:
            folder_path = tmp_dir / "extracted" / folder_name
            for item in folder_path.iterdir():
                tar.add(item, arcname=item.name)

# Cleanup extracted files 
shutil.rmtree(tmp_dir / "extracted", ignore_errors=True)

# Save single-timepoint subjects to CSV 
csv_path = fs_dir / "single_timepoint_subjects.csv"
with open(csv_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["subject_id", "folder_name"])
    for subj, folder_name in single_tp_subjects_dict.items():
        writer.writerow([subj, folder_name])

# Print summary
print("✅ Subjects with only one timepoint (not tarred):")
print(single_tp_subjects_dict)
print(f"\n📄 CSV saved: {csv_path}")
