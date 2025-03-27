"""
Python client for the Virtual Imaging Platform (VIP): https://vip.creatis.insa-lyon.fr/.

Python classes and methods to interact with VIP through its RESTful API.
Main user class: VipSession 
    from vip_client import VipSession
For more information: https://github.com/virtual-imaging-platform/VIP-python-client.
"""

# Informations
__version__ = "0.1.7"
__license__ = "CECILL-B"

from vip_client.classes import VipSession
