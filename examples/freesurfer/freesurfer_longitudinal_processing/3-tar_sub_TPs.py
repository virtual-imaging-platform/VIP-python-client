from pathlib import Path
import tarfile
import shutil

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
        base_name = tar_path.name[:-7]   # remove ".tar.gz"
    else:  # .tgz
        base_name = tar_path.stem        # removes ".tgz"

    extract_dir = tmp_dir / "extracted" / base_name
    extract_dir.mkdir(parents=True, exist_ok=True)

    # Untar (auto-detect compression)
    with tarfile.open(tar_path, "r:*") as tar:
        tar.extractall(path=extract_dir)

    subjects.setdefault(subj, []).append(extract_dir)

# Group per subject
for subj, tp_dirs in subjects.items():
    out_tar = tmp_dir / f"{subj}_TPs.tgz"

    with tarfile.open(out_tar, "w:gz") as tar:
        for tp_dir in tp_dirs:
            for item in tp_dir.iterdir():
                tar.add(item, arcname=item.name)

# Cleanup extracted files
shutil.rmtree(tmp_dir / "extracted", ignore_errors=True)

print("✅ Done: grouped longitudinal timepoints per subject.")

