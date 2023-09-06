"""
Python client for the Virtual Imaging Platform (VIP): https://vip.creatis.insa-lyon.fr/.

Python classes and methods to interact with VIP through its RESTful API.
Main user class: VipSession 
    from vip_client import VipSession
For more information: https://github.com/virtual-imaging-platform/VIP-python-client.
"""

# Informations
__version__ = "0.1.0"
__license__ = "CECILL-B"

# Import classes and packages to secure the namespace
if __package__ != "vip_client":
    import sys
    from pathlib import Path
    SOURCE_ROOT = str(Path(__file__).parents[1]) # <=> /src/
    sys.path.append(SOURCE_ROOT)
# Run utils/__init__.py
import vip_client.utils 
# Run classes/__init__.py
import vip_client.classes 
# Shortcut to import the VipSession class
from vip_client.classes import VipSession