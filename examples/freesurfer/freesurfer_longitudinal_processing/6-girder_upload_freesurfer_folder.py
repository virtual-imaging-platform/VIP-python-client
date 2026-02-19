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

# api Rest url of the warehouse
#Windows users: paths use backslashes (\) while Linux/macOS use forward slashes (/)
url='https://insert/your-server-here/api/v1'
# https://srmnopt.creatis.insa-lyon.fr/warehouse/api/v1 --> for NMR and Optics
# https://myriad.creatis.insa-lyon.fr/api/v1 --> for MYRIAD

# apiKey is a "mechanism" to share authentication and rights on folder.
# User should defined through the web interface (inside user information) an apiKey with the corresponding privileges
apiKey = 'GIRDER_API_KEY'

# Generate the warehouse client
gc = girder_client.GirderClient(apiUrl=url)

# Authentication to the warehouse
gc.authenticate(apiKey=apiKey)

# upload local freesurfer folder in the original input folder on Girder
folderId ='FOLDER_ID' #  3D Flow phantom+Bubbles
#an example of a folder ID: 698de7fe82d062f2aea9619d

# If 'derivatives' folder exists but 'freeSurfer' folder is absent:
# gc.upload('/insert/your/upload/path/derivatives/freesurfer', folderId)

# Default upload (if 'derivatives' folder is absent on the warehouse):
gc.upload('/insert/your/upload/path/derivatives/', folderId)

