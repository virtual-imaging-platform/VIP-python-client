"""
All classes for the client.
- VipSession: main user class. To run a VIP application on local datasets.
- VipLauncher: to run a Vip application on datasets located on VIP servers.
- VipCI (alpha): to run a Vip application on datasets located on CREATIS data warehouse.
- VipLoader (planned): to upload / download data to / from VIP servers.
- VipLoader (planned): base class.
"""

# Import classes and modules to secure the namespace
if __package__ != "vip_client.classes":
    import sys
    from pathlib import Path
    SOURCE_ROOT = str(Path(__file__).parents[2]) # src/
    sys.path.append(SOURCE_ROOT)
# Import utilities
import vip_client.utils
# Replace each class module by its class in the namespace
from vip_client.classes.VipSession import VipSession 
from vip_client.classes.VipLauncher import VipLauncher
from vip_client.classes.VipCI import VipCI
from vip_client.classes.VipLoader import VipLoader
from vip_client.classes.VipClient import VipClient 