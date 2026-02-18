# Description:
# Author: Frederic Cervenansky < frederic.cervenansky@creatis.insa-lyon.fr>
#
# Licence Cecill-B
# Copyright (C) Creatis 2017-2024


# import
import girder_client
import types
import sys
import click
from pathlib import Path

# api Rest url of the warehouse
url='https://insert/your-server-here/api/v1'

# apiKey is a "mechanism" to share authentication and rights on folder.
# User should defined through the web interface (inside user information) an apiKey ith the corresponding privileges
apiKey = 'GIRDER_API_KEY'

# Generate the warehouse client
gc = girder_client.GirderClient(apiUrl=url)

# Authentication to the warehouse
gc.authenticate(apiKey=apiKey)

# Use the ID of the folder you chose put your input MRIs
folderId ='FOLDER_ID' #  3D Flow phantom+Bubbles

# Local download directory
download_dir = Path('/insert/your/download/path')

# Download data from Girder
gc.downloadFolderRecursive(folderId, str(download_dir))

# Add derivatives/freesurfer folder
derivatives_fs = download_dir / 'derivatives' / 'freesurfer'
derivatives_fs.mkdir(parents=True, exist_ok=True)  # will create if not exists, do nothing if exists

print(f"'derivatives/freesurfer' folder ensured at: {derivatives_fs}")
