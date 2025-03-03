"""
All classes for the client.
- VipSession: main user class. To run a VIP application on local datasets.
- VipLauncher: to run a Vip application on datasets located on VIP servers.
- VipGirder (alpha): to run a Vip application on datasets located on CREATIS data warehouse.
- VipLoader (planned): to upload / download data to / from VIP servers.
- VipLoader (planned): base class.
"""

# Replace each class module by its class in the namespace
from vip_client.classes.VipSession import VipSession 
from vip_client.classes.VipLauncher import VipLauncher
from vip_client.classes.VipGirder import VipGirder
