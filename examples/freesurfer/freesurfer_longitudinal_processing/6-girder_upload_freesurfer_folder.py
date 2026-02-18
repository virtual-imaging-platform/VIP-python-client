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
url='https://insert/your-server-here/api/v1'

# apiKey is a "mechanism" to share authentication and rights on folder.
# User should defined through the web interface (inside user information) an apiKey with the corresponding privileges
apiKey = 'GIRDER_API_KEY'

# Generate the warehouse client
gc = girder_client.GirderClient(apiUrl=url)

# Authentication to the warehouse
gc.authenticate(apiKey=apiKey)

# upload local freesurfer folder in the original input folder on Girder
folderId ='FOLDER_ID' #  3D Flow phantom+Bubbles
gc.upload('/insert/your/upload/path/derivatives/freesurfer',folderId)

