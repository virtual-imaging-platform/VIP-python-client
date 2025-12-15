from vip_client.classes.VipGirder import VipGirder
from vip_client.classes.VipLauncher import VipLauncher
from vip_client.classes.VipSession import VipSession

"""
All classes for the client.
- VipSession: main user class. To run a VIP application on local datasets.
- VipLauncher: to run a Vip application on datasets located on VIP servers.
- VipGirder: to run a Vip application on datasets located on CREATIS data warehouse.
"""

__all__ = ["VipGirder", "VipLauncher", "VipSession"]
