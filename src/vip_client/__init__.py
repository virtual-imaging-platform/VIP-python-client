"""
VIP Python client

Python classes to interact with the Virtual Imaging Platform (VIP) through its CARMIN (RESTful) API.
Contacts: Sorina Camarasu-Pop <sorina.pop@creatis.insa-lyon.fr> & Axel Bonnet <axel.bonnet@creatis.insa-lyon.fr>.
"""

# Informations
__version__ = "0.0.12"
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