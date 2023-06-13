# Small example using VIP API

`./freesurfer-recon-all.sh` script launches Freesurfer on VIP server through VIP API.

## Requirements

### VIP API token

Export the API token before executing `./freesurfer-recon-all.sh`

`export VIP_API_TOKEN=<token>`

### Freesurfer license

Add your Freesurfer license in `inputs/LICENSE.txt`

### Get dataset

Install [`datalad`](https://handbook.datalad.org/en/latest/intro/installation.html)

For Linux:

via apt
```
sudo apt-get install datalad
```
or via PyPI
```
pip install datalad
```

Download the T1 image:
```
datalad get example/freesurfer/inputs/ds001600/sub-1/anat/sub-1_T1w.nii.gz
```